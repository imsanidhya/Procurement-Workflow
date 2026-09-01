# =========================================================
# email_service.py
# =========================================================

import os
import base64
import smtplib

from email.message import EmailMessage

from flask import current_app, url_for


# =========================================================
# GENERAL HELPERS
# =========================================================

def normalize_email(email):
    """
    Normalize an email address.
    """

    return (email or "").strip().lower()


def unique_emails(emails):
    """
    Remove empty and duplicate email addresses while
    preserving order.
    """

    result = []

    for email in emails or []:

        email = normalize_email(email)

        if not email:
            continue

        if email not in result:
            result.append(email)

    return result


def get_approver_list(req):
    """
    Return configured approvers as a clean list.
    """

    if not req:
        return []

    return unique_emails(
        (req.approver_emails or "").split(",")
    )


# =========================================================
# REQUEST URL
# =========================================================

def get_request_url(req):
    """
    Generate an absolute URL for the request history page.
    """

    return url_for(
        "request_history",
        request_number=req.request_number,
        _external=True,
    )


# =========================================================
# MICROSOFT 365 CONFIGURATION
# =========================================================

def get_mail_config():
    """
    Read email configuration from Flask config.

    Expected configuration:

        MAIL_SERVER
        MAIL_PORT
        MAIL_USE_TLS
        MAIL_USE_SSL
        MAIL_AUTH_MODE
        MAIL_USERNAME
        MAIL_PASSWORD
        MAIL_DEFAULT_SENDER

    OAuth configuration:

        MAIL_TENANT_ID
        MAIL_CLIENT_ID
        MAIL_CLIENT_SECRET

    MAIL_AUTH_MODE:

        password
        oauth
    """

    return {
        "server": current_app.config.get(
            "MAIL_SERVER",
            "smtp.office365.com",
        ),

        "port": int(
            current_app.config.get(
                "MAIL_PORT",
                587,
            )
        ),

        "use_tls": bool(
            current_app.config.get(
                "MAIL_USE_TLS",
                True,
            )
        ),

        "use_ssl": bool(
            current_app.config.get(
                "MAIL_USE_SSL",
                False,
            )
        ),

        "auth_mode": (
            current_app.config.get(
                "MAIL_AUTH_MODE",
                "password",
            )
            or "password"
        ).lower().strip(),

        "username": current_app.config.get(
            "MAIL_USERNAME",
        ),

        "password": current_app.config.get(
            "MAIL_PASSWORD",
        ),

        "sender": (
            current_app.config.get(
                "MAIL_DEFAULT_SENDER",
            )
            or current_app.config.get(
                "MAIL_USERNAME",
            )
        ),

        "tenant_id": current_app.config.get(
            "MAIL_TENANT_ID",
        ),

        "client_id": current_app.config.get(
            "MAIL_CLIENT_ID",
        ),

        "client_secret": current_app.config.get(
            "MAIL_CLIENT_SECRET",
        ),
    }


# =========================================================
# OAUTH TOKEN
# =========================================================

def get_oauth_access_token():
    """
    Obtain a Microsoft Entra OAuth access token using
    client credentials.

    Requires:

        msal

    Configuration:

        MAIL_TENANT_ID
        MAIL_CLIENT_ID
        MAIL_CLIENT_SECRET

    The Microsoft 365 application must have the required
    Exchange Online SMTP application permissions and
    administrator consent.
    """

    config = get_mail_config()

    tenant_id = config["tenant_id"]
    client_id = config["client_id"]
    client_secret = config["client_secret"]

    if not tenant_id:
        raise RuntimeError(
            "MAIL_TENANT_ID is not configured."
        )

    if not client_id:
        raise RuntimeError(
            "MAIL_CLIENT_ID is not configured."
        )

    if not client_secret:
        raise RuntimeError(
            "MAIL_CLIENT_SECRET is not configured."
        )

    try:

        import msal

    except ImportError as exc:

        raise RuntimeError(
            "MSAL is not installed. "
            "Install it with: pip install msal"
        ) from exc

    authority = (
        f"https://login.microsoftonline.com/"
        f"{tenant_id}"
    )

    application = msal.ConfidentialClientApplication(
        client_id=client_id,
        authority=authority,
        client_credential=client_secret,
    )

    result = application.acquire_token_for_client(
        scopes=[
            "https://outlook.office365.com/.default"
        ]
    )

    if "access_token" not in result:

        error = result.get(
            "error_description"
        ) or result.get(
            "error"
        ) or "Unknown OAuth error."

        raise RuntimeError(
            f"Microsoft 365 OAuth authentication failed: "
            f"{error}"
        )

    return result["access_token"]


# =========================================================
# SMTP OAUTH XOAUTH2
# =========================================================

def smtp_auth_oauth(
    smtp,
    username,
    access_token,
):
    """
    Authenticate to Microsoft 365 SMTP using XOAUTH2.
    """

    if not username:
        raise RuntimeError(
            "MAIL_USERNAME is required for OAuth SMTP."
        )

    auth_string = (
        f"user={username}\x01"
        f"auth=Bearer {access_token}\x01"
        f"\x01"
    )

    encoded = base64.b64encode(
        auth_string.encode("utf-8")
    ).decode("ascii")

    code, response = smtp.docmd(
        "AUTH",
        "XOAUTH2 " + encoded,
    )

    if code != 235:

        try:
            response_text = response.decode(
                "utf-8",
                errors="replace",
            )
        except Exception:
            response_text = str(response)

        raise smtplib.SMTPAuthenticationError(
            code,
            response,
        )


# =========================================================
# BASIC SMTP AUTH
# =========================================================

def smtp_auth_password(
    smtp,
    username,
    password,
):
    """
    Authenticate using username/password.

    Microsoft 365 may have SMTP AUTH disabled by the
    tenant or mailbox. OAuth is preferred for new
    production deployments.
    """

    if not username:
        raise RuntimeError(
            "MAIL_USERNAME is not configured."
        )

    if not password:
        raise RuntimeError(
            "MAIL_PASSWORD is not configured."
        )

    smtp.login(
        username,
        password,
    )


# =========================================================
# ATTACHMENT NORMALIZATION
# =========================================================

def add_attachment(
    message,
    attachment,
):
    """
    Add an attachment.

    Supported attachment formats:

    1. File path:

        {
            "path": "/tmp/file.pdf",
            "filename": "file.pdf",
            "content_type": "application/pdf"
        }

    2. Bytes:

        {
            "data": b"...",
            "filename": "file.pdf",
            "content_type": "application/pdf"
        }

    3. BytesIO:

        {
            "file_object": buffer,
            "filename": "file.pdf",
            "content_type": "application/pdf"
        }
    """

    if not attachment:
        return False

    filename = attachment.get(
        "filename",
        "attachment",
    )

    content_type = attachment.get(
        "content_type",
        "application/octet-stream",
    )

    file_data = None

    # -----------------------------------------------------
    # Raw bytes
    # -----------------------------------------------------

    if attachment.get("data") is not None:

        file_data = attachment["data"]

    # -----------------------------------------------------
    # File-like object / BytesIO
    # -----------------------------------------------------

    elif attachment.get("file_object") is not None:

        file_object = attachment["file_object"]

        try:
            file_object.seek(0)
        except Exception:
            pass

        file_data = file_object.read()

    # -----------------------------------------------------
    # Filesystem path
    # -----------------------------------------------------

    elif attachment.get("path"):

        file_path = attachment["path"]

        if not os.path.exists(file_path):

            print(
                "EMAIL ATTACHMENT ERROR: "
                f"File not found: {file_path}"
            )

            return False

        with open(
            file_path,
            "rb",
        ) as file:

            file_data = file.read()

        if not attachment.get("filename"):

            filename = os.path.basename(
                file_path
            )

    # -----------------------------------------------------
    # Nothing usable
    # -----------------------------------------------------

    else:

        print(
            "EMAIL ATTACHMENT ERROR: "
            "No data, file object, or path."
        )

        return False

    # -----------------------------------------------------
    # MIME type
    # -----------------------------------------------------

    if (
        content_type
        and "/"
        in content_type
    ):

        maintype, subtype = (
            content_type.split(
                "/",
                1,
            )
        )

    else:

        maintype = "application"
        subtype = "octet-stream"

    message.add_attachment(
        file_data,
        maintype=maintype,
        subtype=subtype,
        filename=filename,
    )

    return True


# =========================================================
# BASIC EMAIL SENDER
# =========================================================

def send_email(
    recipients,
    subject,
    body,
    attachments=None,
):
    """
    Send email through Microsoft 365 SMTP.

    Supports:

        MAIL_AUTH_MODE=password

    or:

        MAIL_AUTH_MODE=oauth

    Email failures are caught and returned as False.
    """

    # -----------------------------------------------------
    # Normalize recipients
    # -----------------------------------------------------

    if isinstance(
        recipients,
        str,
    ):

        recipients = [
            recipients
        ]

    recipients = unique_emails(
        recipients
    )

    if not recipients:

        print(
            "EMAIL SKIPPED: No recipients."
        )

        return False

    # -----------------------------------------------------
    # Configuration
    # -----------------------------------------------------

    config = get_mail_config()

    server = config["server"]
    port = config["port"]
    use_tls = config["use_tls"]
    use_ssl = config["use_ssl"]
    auth_mode = config["auth_mode"]
    username = config["username"]
    password = config["password"]
    sender = config["sender"]

    # -----------------------------------------------------
    # Validate sender
    # -----------------------------------------------------

    if not sender:

        print(
            "EMAIL ERROR: "
            "MAIL_DEFAULT_SENDER / MAIL_USERNAME "
            "is not configured."
        )

        return False

    # -----------------------------------------------------
    # TLS / SSL validation
    # -----------------------------------------------------

    if use_tls and use_ssl:

        print(
            "EMAIL ERROR: "
            "MAIL_USE_TLS and MAIL_USE_SSL "
            "cannot both be True."
        )

        return False

    # -----------------------------------------------------
    # Build email
    # -----------------------------------------------------

    message = EmailMessage()

    message["Subject"] = subject
    message["From"] = sender
    message["To"] = ", ".join(
        recipients
    )

    message.set_content(
        body
    )

    # -----------------------------------------------------
    # Attachments
    # -----------------------------------------------------

    for attachment in attachments or []:

        try:

            add_attachment(
                message,
                attachment,
            )

        except Exception as exc:

            print(
                "EMAIL ATTACHMENT ERROR:",
                exc,
            )

    # -----------------------------------------------------
    # Send
    # -----------------------------------------------------

    smtp = None

    try:

        print(
            "EMAIL SENDING:",
            recipients,
            subject,
            "AUTH:",
            auth_mode,
        )

        # -------------------------------------------------
        # SSL
        # -------------------------------------------------

        if use_ssl:

            smtp = smtplib.SMTP_SSL(
                server,
                port,
                timeout=30,
            )

        # -------------------------------------------------
        # Normal SMTP
        # -------------------------------------------------

        else:

            smtp = smtplib.SMTP(
                server,
                port,
                timeout=30,
            )

        smtp.ehlo()

        # -------------------------------------------------
        # STARTTLS
        # -------------------------------------------------

        if use_tls:

            smtp.starttls()

            smtp.ehlo()

        # -------------------------------------------------
        # Authentication
        # -------------------------------------------------

        if auth_mode == "oauth":

            access_token = (
                get_oauth_access_token()
            )

            smtp_auth_oauth(
                smtp,
                username,
                access_token,
            )

        elif auth_mode == "password":

            smtp_auth_password(
                smtp,
                username,
                password,
            )

        else:

            raise RuntimeError(
                "Invalid MAIL_AUTH_MODE. "
                "Use 'password' or 'oauth'."
            )

        # -------------------------------------------------
        # Send
        # -------------------------------------------------

        smtp.send_message(
            message
        )

        print(
            "EMAIL SENT:",
            recipients,
            subject,
        )

        return True

    except Exception as exc:

        print(
            "EMAIL ERROR:",
            repr(exc),
        )

        return False

    finally:

        if smtp:

            try:
                smtp.quit()
            except Exception:
                pass


# =========================================================
# REQUEST SUBMITTED
# =========================================================

def notify_request_submitted(req):
    """
    Notify:

        1. Requester
        2. First approver only
    """

    if not req:
        return False

    requester_email = normalize_email(
        req.requester_email
    )

    approvers = get_approver_list(
        req
    )

    first_approver = (
        approvers[0]
        if approvers
        else None
    )

    recipients = unique_emails(
        [
            requester_email,
            first_approver,
        ]
    )

    if not recipients:

        return False

    request_url = get_request_url(
        req
    )

    subject = (
        "Procurement Request Submitted - "
        f"{req.request_number}"
    )

    body = f"""
Hello,

A new procurement request has been submitted.

Request Number:
{req.request_number}

Request Date:
{req.request_date}

Requester:
{req.requester_name}

Requester Email:
{req.requester_email}

Employee ID:
{req.employee_id or ""}

Department:
{req.department or ""}

Designation:
{req.designation or ""}

Request Type:
{req.request_type or ""}

Subject:
{req.subject or ""}

Priority:
{req.priority or ""}

Item:
{req.item_name or ""}

Item Description:
{req.item_description or ""}

Quantity:
{req.quantity or ""}

Estimated Budget:
{req.estimated_budget or ""}

Business Requirement:
{req.business_requirement or ""}

Business Justification:
{req.business_justification or ""}

Expected Benefits:
{req.expected_benefits or ""}

Status:
SUBMITTED

Please review the request here:

{request_url}

Regards,
Procurement Workflow System
""".strip()

    return send_email(
        recipients=recipients,
        subject=subject,
        body=body,
    )


# =========================================================
# NEXT APPROVER
# =========================================================

def notify_next_approver(
    req,
    next_approver,
):
    """
    Notify only the next approver.
    """

    if not req:
        return False

    next_approver = normalize_email(
        next_approver
    )

    if not next_approver:
        return False

    request_url = get_request_url(
        req
    )

    subject = (
        "Approval Required - "
        f"{req.request_number}"
    )

    body = f"""
Hello,

A procurement request is now waiting for your approval.

Request Number:
{req.request_number}

Request Date:
{req.request_date}

Requester:
{req.requester_name}

Requester Email:
{req.requester_email}

Employee ID:
{req.employee_id or ""}

Department:
{req.department or ""}

Designation:
{req.designation or ""}

Request Type:
{req.request_type or ""}

Subject:
{req.subject or ""}

Priority:
{req.priority or ""}

Item:
{req.item_name or ""}

Item Description:
{req.item_description or ""}

Quantity:
{req.quantity or ""}

Estimated Budget:
{req.estimated_budget or ""}

Business Requirement:
{req.business_requirement or ""}

Business Justification:
{req.business_justification or ""}

Status:
AWAITING YOUR APPROVAL

Please review and take action here:

{request_url}

Regards,
Procurement Workflow System
""".strip()

    return send_email(
        recipients=[
            next_approver
        ],
        subject=subject,
        body=body,
    )


# =========================================================
# QUERY SUBMITTED
# =========================================================

def notify_query_submitted(
    req,
    sender_name,
    sender_email,
    recipient_email,
    query_comment,
):
    """
    Notify a participant about a query.
    """

    if not req:
        return False

    recipient_email = normalize_email(
        recipient_email
    )

    if not recipient_email:
        return False

    sender_email = normalize_email(
        sender_email
    )

    request_url = get_request_url(
        req
    )

    subject = (
        "Query Raised - "
        f"{req.request_number}"
    )

    body = f"""
Hello,

A query has been raised regarding a procurement request.

Request Number:
{req.request_number}

Requester:
{req.requester_name}

Department:
{req.department or ""}

Subject:
{req.subject or ""}

Query Raised By:
{sender_name or sender_email}

Sender Email:
{sender_email}

Query:

{query_comment}

Please review and respond here:

{request_url}

Regards,
Procurement Workflow System
""".strip()

    return send_email(
        recipients=[
            recipient_email
        ],
        subject=subject,
        body=body,
    )


# =========================================================
# QUERY RESPONSE
# =========================================================

def notify_query_response(
    req,
    responder_name,
    responder_email,
    recipient_email,
    response_text,
):
    """
    Notify the original query sender.
    """

    if not req:
        return False

    recipient_email = normalize_email(
        recipient_email
    )

    if not recipient_email:
        return False

    responder_email = normalize_email(
        responder_email
    )

    request_url = get_request_url(
        req
    )

    subject = (
        "Query Response Received - "
        f"{req.request_number}"
    )

    body = f"""
Hello,

A response has been submitted to your query.

Request Number:
{req.request_number}

Requester:
{req.requester_name}

Department:
{req.department or ""}

Responded By:
{responder_name or responder_email}

Responder Email:
{responder_email}

Response:

{response_text}

Please view the complete request history here:

{request_url}

Regards,
Procurement Workflow System
""".strip()

    return send_email(
        recipients=[
            recipient_email
        ],
        subject=subject,
        body=body,
    )


# =========================================================
# REQUEST RETURNED
# =========================================================

def notify_request_returned(
    req,
    returned_by,
    return_comment,
):
    """
    Notify requester when request is returned.
    """

    if not req:
        return False

    requester_email = normalize_email(
        req.requester_email
    )

    if not requester_email:
        return False

    returned_by = normalize_email(
        returned_by
    )

    request_url = get_request_url(
        req
    )

    subject = (
        "Procurement Request Returned - "
        f"{req.request_number}"
    )

    body = f"""
Hello {req.requester_name},

Your procurement request has been returned
for correction/review.

Request Number:
{req.request_number}

Requester:
{req.requester_name}

Returned By:
{returned_by}

Return Comment:

{return_comment}

Status:
RETURNED

Please review the request here:

{request_url}

Regards,
Procurement Workflow System
""".strip()

    return send_email(
        recipients=[
            requester_email
        ],
        subject=subject,
        body=body,
    )


# =========================================================
# FINAL APPROVAL PDF
# =========================================================

def create_final_approval_pdf_attachment(req):
    """
    Use the EXISTING ReportLab PDF generator.

    IMPORTANT:
    This function expects your existing detailed PDF
    generator to be available in pdf_service.py.

    That generator should return BytesIO.
    """

    try:

        from pdf_service import (
            generate_request_pdf,
        )

    except ImportError as exc:

        raise RuntimeError(
            "Could not import generate_request_pdf "
            "from pdf_service.py. "
            "Move your existing ReportLab generator "
            "into pdf_service.py."
        ) from exc

    pdf_buffer = generate_request_pdf(
        req
    )

    if pdf_buffer is None:

        raise RuntimeError(
            "PDF generator returned None."
        )

    # -----------------------------------------------------
    # Existing generator returns BytesIO
    # -----------------------------------------------------

    if hasattr(
        pdf_buffer,
        "seek",
    ):

        pdf_buffer.seek(0)

    return {
        "file_object": pdf_buffer,

        "filename": (
            f"{req.request_number}"
            f"_approved.pdf"
        ),

        "content_type": (
            "application/pdf"
        ),
    }


# =========================================================
# FINAL APPROVAL
# =========================================================

def notify_final_approval(req):
    """
    Notify all participants after final approval.

    Recipients:

        1. Requester
        2. All approvers

    Attachment:

        Final approved ReportLab PDF.
    """

    if not req:
        return False

    # -----------------------------------------------------
    # Participants
    # -----------------------------------------------------

    participants = []

    requester_email = normalize_email(
        req.requester_email
    )

    if requester_email:

        participants.append(
            requester_email
        )

    participants.extend(
        get_approver_list(
            req
        )
    )

    participants = unique_emails(
        participants
    )

    if not participants:

        print(
            "FINAL APPROVAL EMAIL SKIPPED:",
            req.request_number,
        )

        return False

    # -----------------------------------------------------
    # Request URL
    # -----------------------------------------------------

    request_url = get_request_url(
        req
    )

    # -----------------------------------------------------
    # PDF
    # -----------------------------------------------------

    attachments = []

    try:

        pdf_attachment = (
            create_final_approval_pdf_attachment(
                req
            )
        )

        attachments.append(
            pdf_attachment
        )

    except Exception as exc:

        print(
            "FINAL APPROVAL PDF ERROR:",
            repr(exc),
        )

        # -------------------------------------------------
        # We still send the approval email.
        # -------------------------------------------------

    # -----------------------------------------------------
    # Email
    # -----------------------------------------------------

    subject = (
        "Procurement Request Fully Approved - "
        f"{req.request_number}"
    )

    body = f"""
Hello,

The following procurement request has received
final approval through the procurement workflow.

Request Number:
{req.request_number}

Request Date:
{req.request_date}

Requester:
{req.requester_name}

Requester Email:
{req.requester_email}

Employee ID:
{req.employee_id or ""}

Department:
{req.department or ""}

Designation:
{req.designation or ""}

Request Type:
{req.request_type or ""}

Subject:
{req.subject or ""}

Priority:
{req.priority or ""}

Item:
{req.item_name or ""}

Item Description:
{req.item_description or ""}

Quantity:
{req.quantity or ""}

Estimated Budget:
{req.estimated_budget or ""}

Business Requirement:
{req.business_requirement or ""}

Business Justification:
{req.business_justification or ""}

Expected Benefits:
{req.expected_benefits or ""}

Status:
FULLY APPROVED

The approved procurement request PDF is attached
to this email.

You can also view the complete request history here:

{request_url}

Regards,
Procurement Workflow System
""".strip()

    return send_email(
        recipients=participants,
        subject=subject,
        body=body,
        attachments=attachments,
    )