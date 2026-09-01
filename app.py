from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_from_directory,
)

from config import Config

from models import (
    db,
    ProcurementRequest,
    ApprovalHistory,
    QueryMessage,
    User,
)

from mis import save_request_to_mis

from flask_mail import (
    Mail,
    Message,
)

from datetime import datetime
from functools import wraps

from werkzeug.utils import secure_filename

import os
import uuid


# =========================================================
# FLASK APPLICATION
# =========================================================

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)


# =========================================================
# FLASK MAIL
# =========================================================

mail = Mail(app)


# =========================================================
# CREATE DATABASE TABLES
# =========================================================

with app.app_context():
    db.create_all()


# =========================================================
# ATTACHMENT CONFIGURATION
# =========================================================

ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "gif",
    "webp",
    "pdf",
    "doc",
    "docx",
    "xls",
    "xlsx",
    "csv",
    "txt",
    "zip",
}

MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024


# =========================================================
# APPLICATION URL
# =========================================================

APPLICATION_URL = os.getenv(
    "APPLICATION_URL",
    "http://127.0.0.1:5000",
).rstrip("/")


# =========================================================
# GENERAL HELPERS
# =========================================================

def normalize_email(email):
    return (email or "").strip().lower()


def allowed_file(filename):

    if not filename:
        return False

    if "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1].lower()

    return extension in ALLOWED_EXTENSIONS


def generate_safe_filename(filename):

    original_filename = secure_filename(filename)

    if not original_filename:
        original_filename = "attachment"

    unique_id = uuid.uuid4().hex[:12]

    return f"{unique_id}_{original_filename}"


def get_upload_folder():

    folder = app.config.get("UPLOAD_FOLDER")

    if folder:
        os.makedirs(folder, exist_ok=True)

    return folder


# =========================================================
# EMAIL HELPERS
# =========================================================

def get_application_url():
    return APPLICATION_URL.rstrip("/")


def send_email(
    recipients,
    subject,
    html_body,
    text_body=None,
    cc=None,
    bcc=None,
):

    if isinstance(recipients, str):
        recipients = [recipients]

    recipients = [
        normalize_email(email)
        for email in (recipients or [])
        if normalize_email(email)
    ]

    if not recipients:
        print("EMAIL ERROR: No recipients supplied.")
        return False

    if not app.config.get("MAIL_USERNAME"):
        print("EMAIL ERROR: MAIL_USERNAME is not configured.")
        return False

    if not app.config.get("MAIL_PASSWORD"):
        print("EMAIL ERROR: MAIL_PASSWORD is not configured.")
        return False

    try:

        message = Message(
            subject=subject,
            recipients=recipients,
            cc=cc or [],
            bcc=bcc or [],
            sender=app.config.get(
                "MAIL_DEFAULT_SENDER"
            ),
        )

        message.body = (
            text_body
            if text_body
            else html_to_plain_text(html_body)
        )

        message.html = html_body

        mail.send(message)

        print(
            "EMAIL SENT:",
            subject,
            "->",
            recipients,
        )

        return True

    except Exception as e:

        print(
            "EMAIL SEND ERROR:",
            subject,
            "->",
            recipients,
            "ERROR:",
            e,
        )

        return False


def html_to_plain_text(html):

    if not html:
        return ""

    replacements = [
        ("<br>", "\n"),
        ("<br/>", "\n"),
        ("<br />", "\n"),
        ("</p>", "\n"),
        ("</div>", "\n"),
        ("</li>", "\n"),
        ("</h1>", "\n"),
        ("</h2>", "\n"),
        ("</h3>", "\n"),
    ]

    text = html

    for old, new in replacements:
        text = text.replace(old, new)

    import re

    text = re.sub(
        r"<[^>]+>",
        "",
        text,
    )

    text = re.sub(
        r"\n\s*\n+",
        "\n\n",
        text,
    )

    return text.strip()


def email_layout(
    title,
    body_html,
):

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport"
              content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
    </head>

    <body style="
        margin:0;
        padding:0;
        background:#f4f6f8;
        font-family:Arial,Helvetica,sans-serif;
        color:#263238;
    ">

        <div style="
            max-width:700px;
            margin:30px auto;
            background:#ffffff;
            border-radius:10px;
            overflow:hidden;
            box-shadow:0 2px 10px rgba(0,0,0,0.08);
        ">

            <div style="
                background:#17365d;
                color:#ffffff;
                padding:22px 28px;
            ">
                <h2 style="
                    margin:0;
                    font-size:22px;
                ">
                    Procurement Workflow
                </h2>

                <div style="
                    margin-top:5px;
                    font-size:13px;
                    opacity:0.9;
                ">
                    Automated Notification
                </div>
            </div>

            <div style="
                padding:28px;
                line-height:1.6;
            ">

                {body_html}

            </div>

            <div style="
                background:#f7f8fa;
                border-top:1px solid #e5e7eb;
                padding:16px 28px;
                color:#6b7280;
                font-size:12px;
            ">
                This is an automated email from the
                Procurement Workflow System.
                Please do not reply to this email.
            </div>

        </div>

    </body>
    </html>
    """


def email_button(
    text,
    url,
    color="#17365d",
):

    return f"""
    <p style="margin:24px 0;">
        <a href="{url}"
           style="
                display:inline-block;
                background:{color};
                color:#ffffff;
                text-decoration:none;
                padding:11px 20px;
                border-radius:6px;
                font-weight:bold;
           ">
            {text}
        </a>
    </p>
    """


# =========================================================
# EMAIL: REQUEST SUBMITTED
# =========================================================
#
# IMPORTANT:
# The requester is now included in the recipients.
# The email button uses request-history instead of
# review-request because the requester is authorized
# to access request history.
# =========================================================

def send_request_submitted_email(req):

    recipients = []

    # -----------------------------------------------------
    # REQUESTER
    # -----------------------------------------------------

    requester_email = normalize_email(
        req.requester_email
    )

    if requester_email:
        recipients.append(
            requester_email
        )

    # -----------------------------------------------------
    # APPROVERS
    # -----------------------------------------------------

    for approver in get_assigned_approvers(req):

        approver = normalize_email(
            approver
        )

        if (
            approver
            and approver not in recipients
        ):
            recipients.append(
                approver
            )

    if not recipients:
        return False

    # -----------------------------------------------------
    # REQUEST HISTORY URL
    # -----------------------------------------------------

    history_url = (
        f"{get_application_url()}"
        f"/request-history/{req.request_number}"
    )

    # -----------------------------------------------------
    # EMAIL SUBJECT
    # -----------------------------------------------------

    subject = (
        f"Procurement Request "
        f"{req.request_number} Submitted"
    )

    # -----------------------------------------------------
    # EMAIL BODY
    # -----------------------------------------------------

    body = f"""
    <p>Hello,</p>

    <p>
        Procurement request
        <strong>{req.request_number}</strong>
        has been successfully submitted.
    </p>

    <table style="
        width:100%;
        border-collapse:collapse;
        margin:20px 0;
    ">

        <tr>
            <td style="
                padding:8px;
                border-bottom:1px solid #ddd;
            ">
                <strong>Request Number</strong>
            </td>

            <td style="
                padding:8px;
                border-bottom:1px solid #ddd;
            ">
                {req.request_number}
            </td>
        </tr>

        <tr>
            <td style="
                padding:8px;
                border-bottom:1px solid #ddd;
            ">
                <strong>Requester</strong>
            </td>

            <td style="
                padding:8px;
                border-bottom:1px solid #ddd;
            ">
                {req.requester_name}
            </td>
        </tr>

        <tr>
            <td style="
                padding:8px;
                border-bottom:1px solid #ddd;
            ">
                <strong>Department</strong>
            </td>

            <td style="
                padding:8px;
                border-bottom:1px solid #ddd;
            ">
                {req.department or "-"}
            </td>
        </tr>

        <tr>
            <td style="
                padding:8px;
                border-bottom:1px solid #ddd;
            ">
                <strong>Requirement</strong>
            </td>

            <td style="
                padding:8px;
                border-bottom:1px solid #ddd;
            ">
                {req.item_description}
            </td>
        </tr>

        <tr>
            <td style="padding:8px;">
                <strong>Status</strong>
            </td>

            <td style="
                padding:8px;
                color:#17365d;
                font-weight:bold;
            ">
                SUBMITTED
            </td>
        </tr>

    </table>

    {email_button(
        "View Request",
        history_url,
        "#17365d",
    )}

    <p>
        The request has been submitted successfully
        and is now in the procurement approval workflow.
    </p>

    <p>
        This is an automated notification from the
        Procurement Workflow System.
    </p>
    """

    html = email_layout(
        subject,
        body,
    )

    return send_email(
        recipients,
        subject,
        html,
    )


# =========================================================
# EMAIL: NEXT APPROVER
# =========================================================

def send_next_approver_email(
    req,
    next_approver,
):

    review_url = (
        f"{get_application_url()}"
        f"/review-request/{req.request_number}"
    )

    subject = (
        f"Procurement Request "
        f"{req.request_number} Awaiting Your Approval"
    )

    body = f"""
    <p>Hello,</p>

    <p>
        Procurement request
        <strong>{req.request_number}</strong>
        has been approved by the previous approver and
        is now awaiting your approval.
    </p>

    <table style="
        width:100%;
        border-collapse:collapse;
        margin:20px 0;
    ">

        <tr>
            <td style="padding:8px;border-bottom:1px solid #ddd;">
                <strong>Request Number</strong>
            </td>

            <td style="padding:8px;border-bottom:1px solid #ddd;">
                {req.request_number}
            </td>
        </tr>

        <tr>
            <td style="padding:8px;border-bottom:1px solid #ddd;">
                <strong>Requester</strong>
            </td>

            <td style="padding:8px;border-bottom:1px solid #ddd;">
                {req.requester_name}
            </td>
        </tr>

        <tr>
            <td style="padding:8px;">
                <strong>Status</strong>
            </td>

            <td style="padding:8px;">
                Awaiting Approval
            </td>
        </tr>

    </table>

    {email_button(
        "Review Request",
        review_url,
    )}
    """

    html = email_layout(
        subject,
        body,
    )

    return send_email(
        [next_approver],
        subject,
        html,
    )


# =========================================================
# EMAIL: FINAL APPROVAL
# =========================================================

def send_final_approval_email(req):

    recipients = []

    requester = normalize_email(
        req.requester_email
    )

    if requester:
        recipients.append(requester)

    for approver in get_assigned_approvers(req):

        if approver not in recipients:
            recipients.append(approver)

    if not recipients:
        return False

    history_url = (
        f"{get_application_url()}"
        f"/request-history/{req.request_number}"
    )

    subject = (
        f"Procurement Request "
        f"{req.request_number} Fully Approved"
    )

    body = f"""
    <p>Hello,</p>

    <p>
        Procurement request
        <strong>{req.request_number}</strong>
        has completed the approval workflow and has been
        <strong style="color:#198754;">
            fully approved
        </strong>.
    </p>

    <table style="
        width:100%;
        border-collapse:collapse;
        margin:20px 0;
    ">

        <tr>
            <td style="padding:8px;border-bottom:1px solid #ddd;">
                <strong>Request Number</strong>
            </td>

            <td style="padding:8px;border-bottom:1px solid #ddd;">
                {req.request_number}
            </td>
        </tr>

        <tr>
            <td style="padding:8px;border-bottom:1px solid #ddd;">
                <strong>Requester</strong>
            </td>

            <td style="padding:8px;border-bottom:1px solid #ddd;">
                {req.requester_name}
            </td>
        </tr>

        <tr>
            <td style="padding:8px;">
                <strong>Status</strong>
            </td>

            <td style="
                padding:8px;
                color:#198754;
                font-weight:bold;
            ">
                APPROVED
            </td>
        </tr>

    </table>

    {email_button(
        "View Request History",
        history_url,
        "#198754",
    )}
    """

    html = email_layout(
        subject,
        body,
    )

    return send_email(
        recipients,
        subject,
        html,
    )


# =========================================================
# EMAIL: REQUEST RETURNED
# =========================================================

def send_request_returned_email(
    req,
    return_comment,
):

    requester = normalize_email(
        req.requester_email
    )

    if not requester:
        return False

    history_url = (
        f"{get_application_url()}"
        f"/request-history/{req.request_number}"
    )

    subject = (
        f"Procurement Request "
        f"{req.request_number} Returned"
    )

    body = f"""
    <p>Hello {req.requester_name},</p>

    <p>
        Your procurement request
        <strong>{req.request_number}</strong>
        has been returned by the approver.
    </p>

    <div style="
        background:#fff4e5;
        border-left:4px solid #f59e0b;
        padding:14px 16px;
        margin:20px 0;
    ">
        <strong>Return Comment</strong>

        <p style="margin-bottom:0;">
            {return_comment}
        </p>
    </div>

    {email_button(
        "View Request History",
        history_url,
        "#f59e0b",
    )}

    <p>
        Please review the comments and take the required
        corrective action.
    </p>
    """

    html = email_layout(
        subject,
        body,
    )

    return send_email(
        [requester],
        subject,
        html,
    )


# =========================================================
# EMAIL: QUERY
# =========================================================

def send_query_email(
    req,
    recipients,
    sender_name,
    query_comment,
):

    if not recipients:
        return False

    history_url = (
        f"{get_application_url()}"
        f"/request-history/{req.request_number}"
    )

    subject = (
        f"Query Raised - Procurement Request "
        f"{req.request_number}"
    )

    body = f"""
    <p>Hello,</p>

    <p>
        <strong>{sender_name}</strong> has raised a query
        regarding procurement request
        <strong>{req.request_number}</strong>.
    </p>

    <div style="
        background:#eef6ff;
        border-left:4px solid #2563eb;
        padding:14px 16px;
        margin:20px 0;
    ">
        <strong>Query</strong>

        <p style="margin-bottom:0;">
            {query_comment}
        </p>
    </div>

    {email_button(
        "View Query / Respond",
        history_url,
        "#2563eb",
    )}

    <p>
        Please review the query and respond through the
        procurement workflow system.
    </p>
    """

    html = email_layout(
        subject,
        body,
    )

    return send_email(
        recipients,
        subject,
        html,
    )


# =========================================================
# EMAIL: QUERY RESPONSE
# =========================================================

def send_query_response_email(
    query,
    response_text,
):

    sender_email = normalize_email(
        query.sender_email
    )

    if not sender_email:
        return False

    req = ProcurementRequest.query.get(
        query.request_id
    )

    if not req:
        return False

    history_url = (
        f"{get_application_url()}"
        f"/request-history/{req.request_number}"
    )

    subject = (
        f"Query Response Received - "
        f"{req.request_number}"
    )

    body = f"""
    <p>Hello {query.sender_name or ''},</p>

    <p>
        Your query regarding procurement request
        <strong>{req.request_number}</strong>
        has received a response.
    </p>

    <div style="
        background:#f0fdf4;
        border-left:4px solid #16a34a;
        padding:14px 16px;
        margin:20px 0;
    ">
        <strong>Response</strong>

        <p style="margin-bottom:0;">
            {response_text}
        </p>
    </div>

    {email_button(
        "View Query History",
        history_url,
        "#16a34a",
    )}
    """

    html = email_layout(
        subject,
        body,
    )

    return send_email(
        [sender_email],
        subject,
        html,
    )


# =========================================================
# EMAIL: QUERY CLOSED
# =========================================================

def send_query_closed_email(
    req,
    root_query,
):

    recipients = []

    requester = normalize_email(
        req.requester_email
    )

    if requester:
        recipients.append(requester)

    query_sender = normalize_email(
        root_query.sender_email
    )

    if (
        query_sender
        and query_sender not in recipients
    ):
        recipients.append(query_sender)

    if not recipients:
        return False

    history_url = (
        f"{get_application_url()}"
        f"/request-history/{req.request_number}"
    )

    subject = (
        f"Query Closed - Procurement Request "
        f"{req.request_number}"
    )

    body = f"""
    <p>Hello,</p>

    <p>
        Query
        <strong>#{root_query.id}</strong>
        for procurement request
        <strong>{req.request_number}</strong>
        has been closed.
    </p>

    <p>
        The procurement request is now available for
        further workflow processing.
    </p>

    {email_button(
        "View Request History",
        history_url,
    )}
    """

    html = email_layout(
        subject,
        body,
    )

    return send_email(
        recipients,
        subject,
        html,
    )


# =========================================================
# LOGIN REQUIRED
# =========================================================

def login_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:

            flash(
                "Please login to continue.",
                "warning",
            )

            return redirect(
                url_for("login")
            )

        return function(*args, **kwargs)

    return decorated_function


# =========================================================
# APPROVER REQUIRED
# =========================================================

def approver_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:

            flash(
                "Please login to continue.",
                "warning",
            )

            return redirect(
                url_for("login")
            )

        if session.get("role") != "APPROVER":

            flash(
                "You are not authorized to perform this action.",
                "danger",
            )

            return redirect(
                url_for("dashboard")
            )

        return function(*args, **kwargs)

    return decorated_function


# =========================================================
# USER REDIRECT HELPER
# =========================================================

def redirect_to_dashboard():

    if session.get("role") == "APPROVER":

        return redirect(
            url_for("approval_dashboard")
        )

    return redirect(
        url_for("dashboard")
    )


# =========================================================
# REQUEST HELPERS
# =========================================================

def get_request_by_number(request_number):

    if not request_number:
        return None

    return ProcurementRequest.query.filter(
        db.func.lower(
            ProcurementRequest.request_number
        )
        == request_number.strip().lower()
    ).first()


def get_assigned_approvers(req):

    return [
        normalize_email(email)
        for email in (req.approver_emails or "").split(",")
        if normalize_email(email)
    ]


def get_approval_history(req):

    return (
        ApprovalHistory.query
        .filter_by(request_id=req.id)
        .order_by(
            ApprovalHistory.created_at.asc(),
            ApprovalHistory.id.asc(),
        )
        .all()
    )


def get_approved_approvers(req):

    return [
        normalize_email(history.approver_email)
        for history in get_approval_history(req)
        if history.action == "APPROVED"
    ]


def get_current_approver(req):

    approvers = get_assigned_approvers(req)

    if not approvers:
        return None

    approved_approvers = get_approved_approvers(req)

    for approver in approvers:

        if approver not in approved_approvers:
            return approver

    return None


def is_current_approver(req, approver_email):

    current_approver = get_current_approver(req)

    return (
        current_approver is not None
        and current_approver
        == normalize_email(approver_email)
    )


# =========================================================
# USER HELPERS
# =========================================================

def get_user_name(email, fallback=None):

    email = normalize_email(email)

    if not email:
        return fallback

    user = User.query.filter(
        db.func.lower(User.email) == email
    ).first()

    if user:
        return user.name

    return fallback


# =========================================================
# QUERY HELPERS
# =========================================================

def get_query_history(req):

    if not req:
        return []

    return (
        QueryMessage.query
        .filter(
            QueryMessage.request_id == req.id
        )
        .order_by(
            QueryMessage.created_at.asc(),
            QueryMessage.id.asc(),
        )
        .all()
    )


def get_queries_for_user(req, user_email):

    if not req:
        return []

    user_email = normalize_email(user_email)

    if not user_email:
        return []

    return (
        QueryMessage.query
        .filter(
            QueryMessage.request_id == req.id,
            db.or_(
                db.func.lower(
                    QueryMessage.sender_email
                ) == user_email,

                db.func.lower(
                    QueryMessage.recipient_email
                ) == user_email,
            ),
        )
        .order_by(
            QueryMessage.created_at.asc(),
            QueryMessage.id.asc(),
        )
        .all()
    )


def get_latest_query_activity(req, user_email):

    if not req:
        return None

    user_email = normalize_email(user_email)

    if not user_email:
        return None

    return (
        QueryMessage.query
        .filter(
            QueryMessage.request_id == req.id,
            db.or_(
                db.func.lower(
                    QueryMessage.sender_email
                ) == user_email,

                db.func.lower(
                    QueryMessage.recipient_email
                ) == user_email,
            ),
        )
        .order_by(
            QueryMessage.created_at.desc(),
            QueryMessage.id.desc(),
        )
        .first()
    )


def get_latest_query_message(req, user_email=None):

    if not req:
        return None

    query = QueryMessage.query.filter(
        QueryMessage.request_id == req.id
    )

    if user_email:

        user_email = normalize_email(
            user_email
        )

        query = query.filter(
            db.or_(
                db.func.lower(
                    QueryMessage.sender_email
                ) == user_email,

                db.func.lower(
                    QueryMessage.recipient_email
                ) == user_email,
            )
        )

    return (
        query
        .order_by(
            QueryMessage.created_at.desc(),
            QueryMessage.id.desc(),
        )
        .first()
    )


def user_can_access_query(query, user_email):

    if not query:
        return False

    user_email = normalize_email(user_email)

    sender = normalize_email(
        query.sender_email
    )

    recipient = normalize_email(
        query.recipient_email
    )

    return (
        user_email == sender
        or user_email == recipient
    )


# =========================================================
# QUERY THREAD HELPERS
# =========================================================

def get_query_root(query):

    if not query:
        return None

    if not query.reply_to_id:
        return query

    root = QueryMessage.query.get(
        query.reply_to_id
    )

    return root or query


def get_query_thread(query):

    root = get_query_root(query)

    if not root:
        return []

    return (
        QueryMessage.query
        .filter(
            db.or_(
                QueryMessage.id == root.id,
                QueryMessage.reply_to_id == root.id,
            )
        )
        .order_by(
            QueryMessage.created_at.asc(),
            QueryMessage.id.asc(),
        )
        .all()
    )


def get_active_query_roots(req):

    if not req:
        return []

    return (
        QueryMessage.query
        .filter(
            QueryMessage.request_id == req.id,
            QueryMessage.reply_to_id.is_(None),
            QueryMessage.status.in_(
                [
                    "OPEN",
                    "RESPONDED",
                ]
            ),
        )
        .order_by(
            QueryMessage.created_at.desc(),
            QueryMessage.id.desc(),
        )
        .all()
    )


def get_active_queries(req):

    return get_active_query_roots(req)


def get_active_query(req):

    queries = get_active_query_roots(req)

    if queries:
        return queries[0]

    return None


def has_active_queries(req):

    if not req:
        return False

    return (
        QueryMessage.query
        .filter(
            QueryMessage.request_id == req.id,
            QueryMessage.reply_to_id.is_(None),
            QueryMessage.status.in_(
                [
                    "OPEN",
                    "RESPONDED",
                ]
            ),
        )
        .count()
        > 0
    )


# =========================================================
# QUERY THREADS FOR USER
# =========================================================

def get_query_threads_for_user(req, user_email):

    user_email = normalize_email(user_email)

    if not req or not user_email:
        return []

    messages = get_queries_for_user(
        req,
        user_email,
    )

    roots = {}

    for message in messages:

        root = get_query_root(message)

        if not root:
            continue

        if not user_can_access_query(
            root,
            user_email,
        ):
            continue

        roots[root.id] = root

    thread_data = []

    for root in roots.values():

        thread = get_query_thread(root)

        visible_thread = [
            message
            for message in thread
            if user_can_access_query(
                message,
                user_email,
            )
        ]

        if not visible_thread:
            continue

        latest_message = max(
            visible_thread,
            key=lambda message: (
                message.created_at,
                message.id,
            ),
        )

        thread_data.append(
            {
                "root": root,
                "messages": visible_thread,
                "latest_message": latest_message,
                "status": root.status,
                "created_at": root.created_at,
                "updated_at": latest_message.created_at,
            }
        )

    thread_data.sort(
        key=lambda item: (
            item["updated_at"],
            item["root"].id,
        ),
        reverse=True,
    )

    return thread_data


# =========================================================
# QUERY PARTICIPANTS
# =========================================================

def get_participant_emails(req):

    participants = []

    requester_email = normalize_email(
        req.requester_email
    )

    if requester_email:
        participants.append(
            requester_email
        )

    for email in get_assigned_approvers(req):

        email = normalize_email(email)

        if (
            email
            and email not in participants
        ):
            participants.append(email)

    return participants


def get_participant_details(req):

    participants = get_participant_emails(req)

    details = []

    requester_email = normalize_email(
        req.requester_email
    )

    for email in participants:

        if email == requester_email:

            name = req.requester_name

        else:

            name = get_user_name(
                email,
                fallback=email,
            )

        details.append(
            {
                "email": email,
                "name": name,
            }
        )

    return details


# =========================================================
# QUERY REQUESTS FOR APPROVER
# =========================================================

def get_query_requests_for_approver(
    approver_email
):

    approver_email = normalize_email(
        approver_email
    )

    if not approver_email:
        return []

    requests = (
        ProcurementRequest.query
        .join(
            QueryMessage,
            QueryMessage.request_id
            == ProcurementRequest.id,
        )
        .filter(
            db.or_(
                db.func.lower(
                    QueryMessage.sender_email
                ) == approver_email,

                db.func.lower(
                    QueryMessage.recipient_email
                ) == approver_email,
            )
        )
        .distinct()
        .order_by(
            ProcurementRequest.created_at.desc()
        )
        .all()
    )

    result = []

    for req in requests:

        assigned = get_assigned_approvers(req)

        if approver_email not in assigned:
            continue

        threads = get_query_threads_for_user(
            req,
            approver_email,
        )

        if not threads:
            continue

        result.append(
            {
                "request": req,
                "query_threads": threads,
                "latest_query": threads[0]["latest_message"],
                "query_history": get_queries_for_user(
                    req,
                    approver_email,
                ),
            }
        )

    result.sort(
        key=lambda item: (
            item["latest_query"].created_at,
            item["latest_query"].id,
        ),
        reverse=True,
    )

    return result


# =========================================================
# MIS HELPER
# =========================================================

def update_mis(req):

    try:

        save_request_to_mis(
            {
                "request_number": req.request_number,
                "request_date": req.request_date,
                "requester_name": req.requester_name,
                "requester_email": req.requester_email,
                "employee_id": req.employee_id,
                "department": req.department,
                "designation": req.designation,
                "item_description": req.item_description,
                "business_requirement": req.business_requirement,
                "boq": req.boq,
                "approver_emails": req.approver_emails,
                "status": req.status,
                "attachment_filename": req.attachment_filename,
                "created_at": req.created_at,
                "updated_at": req.updated_at,
            },
            app.config["MIS_FILE"],
        )

    except Exception as e:

        print(
            "MIS ERROR:",
            e,
        )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    if "user_id" not in session:
        return redirect(
            url_for("login")
        )

    if session.get("role") == "APPROVER":

        return redirect(
            url_for("approval_dashboard")
        )

    return redirect(
        url_for("dashboard")
    )


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"],
)
def login():

    if "user_id" in session:

        if session.get("role") == "APPROVER":

            return redirect(
                url_for("approval_dashboard")
            )

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        email = normalize_email(
            request.form.get(
                "email",
                "",
            )
        )

        password = request.form.get(
            "password",
            "",
        )

        if not email or not password:

            flash(
                "Email and password are required.",
                "danger",
            )

            return render_template(
                "login.html"
            )

        user = User.query.filter(
            db.func.lower(User.email) == email
        ).first()

        if (
            user is None
            or not user.is_active
            or not user.check_password(password)
        ):

            flash(
                "Invalid email or password.",
                "danger",
            )

            return render_template(
                "login.html"
            )

        session.clear()

        session["user_id"] = user.id
        session["user_name"] = user.name
        session["user_email"] = normalize_email(
            user.email
        )
        session["employee_id"] = user.employee_id
        session["department"] = user.department
        session["designation"] = user.designation
        session["role"] = user.role

        flash(
            f"Welcome, {user.name}!",
            "success",
        )

        if user.role == "APPROVER":

            return redirect(
                url_for("approval_dashboard")
            )

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "login.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out successfully.",
        "success",
    )

    return redirect(
        url_for("login")
    )


# =========================================================
# USER DASHBOARD
# =========================================================

@app.route("/dashboard")
@login_required
def dashboard():

    if session.get("role") == "APPROVER":

        return redirect(
            url_for("approval_dashboard")
        )

    user_email = normalize_email(
        session.get("user_email")
    )

    submitted_requests = (
        ProcurementRequest.query
        .filter(
            db.func.lower(
                ProcurementRequest.requester_email
            ) == user_email
        )
        .order_by(
            ProcurementRequest.created_at.desc()
        )
        .all()
    )

    draft_requests = (
        ProcurementRequest.query
        .filter(
            db.func.lower(
                ProcurementRequest.requester_email
            ) == user_email,
            ProcurementRequest.status == "DRAFT",
        )
        .order_by(
            ProcurementRequest.updated_at.desc()
        )
        .all()
    )

    query_history = (
        QueryMessage.query
        .filter(
            db.or_(
                db.func.lower(
                    QueryMessage.sender_email
                ) == user_email,

                db.func.lower(
                    QueryMessage.recipient_email
                ) == user_email,
            )
        )
        .order_by(
            QueryMessage.created_at.desc(),
            QueryMessage.id.desc(),
        )
        .all()
    )

    query_thread_data = []

    request_ids = {
        message.request_id
        for message in query_history
        if message.request_id
    }

    for request_id in request_ids:

        req = ProcurementRequest.query.get(
            request_id
        )

        if not req:
            continue

        threads = get_query_threads_for_user(
            req,
            user_email,
        )

        for thread in threads:

            query_thread_data.append(
                {
                    "request": req,
                    "root": thread["root"],
                    "messages": thread["messages"],
                    "latest_message": thread["latest_message"],
                    "status": thread["status"],
                    "created_at": thread["created_at"],
                    "updated_at": thread["updated_at"],
                }
            )

    query_thread_data.sort(
        key=lambda item: (
            item["updated_at"],
            item["root"].id,
        ),
        reverse=True,
    )

    return render_template(
        "dashboard.html",
        submitted_requests=submitted_requests,
        draft_requests=draft_requests,
        query_history=query_history,
        query_thread_data=query_thread_data,
    )


# =========================================================
# REQUEST DETAILS
# =========================================================

@app.route(
    "/request-details/<request_number>",
    methods=["GET"],
)
@login_required
def request_details(request_number):

    if session.get("role") == "APPROVER":

        return redirect(
            url_for("approval_dashboard")
        )

    req = get_request_by_number(
        request_number
    )

    if not req:

        flash(
            "Procurement request was not found.",
            "danger",
        )

        return redirect(
            url_for("dashboard")
        )

    user_email = normalize_email(
        session.get("user_email")
    )

    if normalize_email(
        req.requester_email
    ) != user_email:

        flash(
            "You are not authorized to access this request.",
            "danger",
        )

        return redirect(
            url_for("dashboard")
        )

    query_history = get_queries_for_user(
        req,
        user_email,
    )

    query_threads = get_query_threads_for_user(
        req,
        user_email,
    )

    active_queries = [
        query
        for query in get_active_queries(req)
        if user_can_access_query(
            query,
            user_email,
        )
    ]

    return render_template(
        "request_details.html",
        req=req,
        query_history=query_history,
        query_threads=query_threads,
        active_queries=active_queries,
    )


# =========================================================
# SUBMIT REQUEST
# =========================================================

@app.route(
    "/submit-request",
    methods=["GET", "POST"],
)
@login_required
def submit_request():

    if session.get("role") == "APPROVER":

        return redirect(
            url_for("approval_dashboard")
        )

    if request.method == "POST":

        requester_name = (
            request.form.get(
                "requester_name",
                "",
            )
            .strip()
        )

        requester_email = normalize_email(
            request.form.get(
                "requester_email",
                "",
            )
        )

        employee_id = (
            request.form.get(
                "employee_id",
                "",
            )
            .strip()
        )

        department = (
            request.form.get(
                "department",
                "",
            )
            .strip()
        )

        designation = (
            request.form.get(
                "designation",
                "",
            )
            .strip()
        )

        item_description = (
            request.form.get(
                "item_description",
                "",
            )
            .strip()
        )

        business_requirement = (
            request.form.get(
                "business_requirement",
                "",
            )
            .strip()
        )

        boq = (
            request.form.get(
                "boq",
                "",
            )
            .strip()
        )

        approvers = request.form.getlist(
            "approvers[]"
        )

        cleaned_approvers = []

        for email in approvers:

            email = normalize_email(email)

            if (
                email
                and email not in cleaned_approvers
            ):

                cleaned_approvers.append(
                    email
                )

        approver_emails = ",".join(
            cleaned_approvers
        )

        if not requester_name:

            flash(
                "Requester name is required.",
                "danger",
            )

            return redirect(
                url_for("submit_request")
            )

        if not requester_email:

            flash(
                "Requester organization email is required.",
                "danger",
            )

            return redirect(
                url_for("submit_request")
            )

        logged_in_email = normalize_email(
            session.get("user_email")
        )

        if requester_email != logged_in_email:

            flash(
                "Requester email must match the logged-in user.",
                "danger",
            )

            return redirect(
                url_for("submit_request")
            )

        if not item_description:

            flash(
                "Requirement description is required.",
                "danger",
            )

            return redirect(
                url_for("submit_request")
            )

        if not business_requirement:

            flash(
                "Business requirement details are required.",
                "danger",
            )

            return redirect(
                url_for("submit_request")
            )

        if not approver_emails:

            flash(
                "At least one approver email is required.",
                "danger",
            )

            return redirect(
                url_for("submit_request")
            )

        for approver_email in cleaned_approvers:

            approver = User.query.filter(
                db.func.lower(User.email)
                == approver_email
            ).first()

            if not approver:

                flash(
                    f"Approver {approver_email} was not found.",
                    "danger",
                )

                return redirect(
                    url_for("submit_request")
                )

            if not approver.is_active:

                flash(
                    f"Approver {approver_email} is inactive.",
                    "danger",
                )

                return redirect(
                    url_for("submit_request")
                )

            if approver.role != "APPROVER":

                flash(
                    f"{approver_email} is not an approver.",
                    "danger",
                )

                return redirect(
                    url_for("submit_request")
                )

        request_number = (
            "PR-"
            + datetime.now().strftime(
                "%Y%m%d%H%M%S"
            )
            + "-"
            + uuid.uuid4().hex[:4].upper()
        )

        request_date = datetime.today().date()

        attachment_filenames = []

        files = request.files.getlist(
            "attachments[]"
        )

        upload_folder = get_upload_folder()

        for file in files:

            if not file:
                continue

            if not file.filename:
                continue

            if not allowed_file(
                file.filename
            ):

                flash(
                    f"File type is not allowed: "
                    f"{file.filename}",
                    "danger",
                )

                return redirect(
                    url_for("submit_request")
                )

            file.seek(
                0,
                os.SEEK_END,
            )

            file_size = file.tell()

            file.seek(0)

            if file_size > MAX_ATTACHMENT_SIZE:

                flash(
                    f"File {file.filename} exceeds "
                    f"the maximum size of 10 MB.",
                    "danger",
                )

                return redirect(
                    url_for("submit_request")
                )

            saved_filename = generate_safe_filename(
                file.filename
            )

            if upload_folder:

                file_path = os.path.join(
                    upload_folder,
                    saved_filename,
                )

                file.save(file_path)

            attachment_filenames.append(
                saved_filename
            )

        attachment_filename = ",".join(
            attachment_filenames
        )

        new_request = ProcurementRequest(
            request_number=request_number,
            request_date=request_date,
            requester_name=requester_name,
            requester_email=requester_email,
            employee_id=employee_id,
            department=department,
            designation=designation,
            item_description=item_description,
            business_requirement=business_requirement,
            boq=boq,
            approver_emails=approver_emails,
            status="SUBMITTED",
            attachment_filename=(
                attachment_filename
                if attachment_filename
                else None
            ),
        )

        try:

            db.session.add(
                new_request
            )

            db.session.commit()

        except Exception as e:

            db.session.rollback()

            print(
                "DATABASE ERROR:",
                e,
            )

            if upload_folder:

                for filename in attachment_filenames:

                    try:

                        file_path = os.path.join(
                            upload_folder,
                            filename,
                        )

                        if os.path.exists(
                            file_path
                        ):

                            os.remove(
                                file_path
                            )

                    except Exception:
                        pass

            flash(
                "There was an error while saving "
                "the request. Please try again.",
                "danger",
            )

            return redirect(
                url_for("submit_request")
            )

        update_mis(
            new_request
        )

        # =====================================================
        # EMAIL: REQUESTER + APPROVERS
        # =====================================================

        email_sent = send_request_submitted_email(
            new_request
        )

        if not email_sent:

            print(
                "WARNING: Request was saved successfully "
                "but the submission email could not be sent:",
                request_number,
            )

        flash(
            f"Request submitted successfully. "
            f"Request Number: {request_number}",
            "success",
        )

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "submit_request.html"
    )


# =========================================================
# APPROVAL DASHBOARD
# =========================================================

@app.route("/approval-dashboard")
@approver_required
def approval_dashboard():

    approver_email = normalize_email(
        session.get("user_email")
    )

    all_requests = (
        ProcurementRequest.query
        .order_by(
            ProcurementRequest.created_at.desc()
        )
        .all()
    )

    requests = []
    approved_requests = []
    returned_requests = []

    for req in all_requests:

        assigned_approvers = get_assigned_approvers(
            req
        )

        if approver_email not in assigned_approvers:
            continue

        current_approver = get_current_approver(
            req
        )

        if (
            req.status == "SUBMITTED"
            and current_approver == approver_email
        ):

            requests.append(req)

        elif req.status == "APPROVED":

            approved_requests.append(req)

        elif req.status == "RETURNED":

            returned_requests.append(req)

    query_request_data = []

    query_requests = get_query_requests_for_approver(
        approver_email
    )

    for item in query_requests:

        req = item["request"]

        query_threads = item["query_threads"]

        if not query_threads:
            continue

        latest_query = query_threads[0]["latest_message"]

        query_request_data.append(
            {
                "request": req,
                "status": latest_query.status,
                "latest_query": latest_query,
                "query_history": item["query_history"],
                "query_threads": query_threads,
            }
        )

    query_request_data.sort(
        key=lambda item: (
            item["latest_query"].created_at,
            item["latest_query"].id,
        ),
        reverse=True,
    )

    request_number = (
        request.args.get(
            "request_number",
            "",
        )
        .strip()
    )

    searched_request = None
    query_history = []
    query_threads = []
    latest_query = None

    if request_number:

        searched_request = get_request_by_number(
            request_number
        )

        if searched_request:

            assigned = get_assigned_approvers(
                searched_request
            )

            if approver_email not in assigned:

                searched_request = None

                flash(
                    "You are not assigned to this request.",
                    "warning",
                )

            else:

                query_history = get_queries_for_user(
                    searched_request,
                    approver_email,
                )

                query_threads = get_query_threads_for_user(
                    searched_request,
                    approver_email,
                )

                latest_query = get_latest_query_activity(
                    searched_request,
                    approver_email,
                )

        else:

            flash(
                "Procurement request was not found.",
                "warning",
            )

    return render_template(
        "approval_dashboard.html",
        requests=requests,
        approved_requests=approved_requests,
        returned_requests=returned_requests,
        query_request_data=query_request_data,
        query_requests=[
            item["request"]
            for item in query_request_data
        ],
        request_number=request_number,
        searched_request=searched_request,
        query_history=query_history,
        query_threads=query_threads,
        latest_query=latest_query,
    )


# =========================================================
# APPROVER QUERY DETAILS
# =========================================================

@app.route(
    "/approver-query-details/<request_number>",
    methods=["GET"],
)
@approver_required
def approver_query_details(request_number):

    approver_email = normalize_email(
        session.get("user_email")
    )

    req = get_request_by_number(
        request_number
    )

    if not req:

        flash(
            "Procurement request was not found.",
            "danger",
        )

        return redirect(
            url_for("approval_dashboard")
        )

    assigned = get_assigned_approvers(req)

    if approver_email not in assigned:

        flash(
            "You are not assigned to this request.",
            "danger",
        )

        return redirect(
            url_for("approval_dashboard")
        )

    return redirect(
        url_for(
            "request_history",
            request_number=req.request_number,
        )
    )


# =========================================================
# BACKWARD COMPATIBILITY QUERY HISTORY
# =========================================================

@app.route(
    "/approver-query-history/<request_number>",
    methods=["GET"],
)
@approver_required
def approver_query_history(request_number):

    return redirect(
        url_for(
            "request_history",
            request_number=request_number,
        )
    )


# =========================================================
# REVIEW REQUEST
# =========================================================

@app.route(
    "/review-request/<request_number>",
    methods=["GET"],
)
@approver_required
def review_request(request_number):

    req = get_request_by_number(
        request_number
    )

    if not req:

        flash(
            "Procurement request was not found.",
            "danger",
        )

        return redirect(
            url_for("approval_dashboard")
        )

    approver_email = normalize_email(
        session.get("user_email")
    )

    assigned = get_assigned_approvers(req)

    if approver_email not in assigned:

        flash(
            "You are not assigned to review this request.",
            "danger",
        )

        return redirect(
            url_for("approval_dashboard")
        )

    current_approver = get_current_approver(
        req
    )

    if current_approver != approver_email:

        if current_approver:

            flash(
                f"This request is currently waiting "
                f"for approval from {current_approver}.",
                "warning",
            )

        else:

            flash(
                "This request is no longer awaiting "
                "your approval.",
                "warning",
            )

        return redirect(
            url_for("approval_dashboard")
        )

    if req.status not in [
        "SUBMITTED",
        "QUERY",
    ]:

        flash(
            f"This request cannot be reviewed because "
            f"its current status is {req.status}.",
            "warning",
        )

        return redirect(
            url_for("approval_dashboard")
        )

    active_queries = [
        query
        for query in get_active_queries(req)
        if user_can_access_query(
            query,
            approver_email,
        )
    ]

    query_threads = get_query_threads_for_user(
        req,
        approver_email,
    )

    participant_emails = get_participant_emails(
        req
    )

    participant_details = get_participant_details(
        req
    )

    return render_template(
        "review_request.html",
        req=req,
        active_queries=active_queries,
        query_threads=query_threads,
        participant_emails=participant_emails,
        participant_details=participant_details,
        has_active_query=bool(active_queries),
        query_page_url=url_for(
            "request_history",
            request_number=req.request_number,
        ),
    )


# =========================================================
# APPROVE REQUEST
# =========================================================

@app.route(
    "/approve-request/<request_number>",
    methods=["POST"],
)
@approver_required
def approve_request(request_number):

    req = get_request_by_number(
        request_number
    )

    if not req:

        flash(
            "Procurement request was not found.",
            "danger",
        )

        return redirect(
            url_for("approval_dashboard")
        )

    approver_email = normalize_email(
        session.get("user_email")
    )

    assigned = get_assigned_approvers(req)

    if approver_email not in assigned:

        flash(
            "You are not assigned to approve this request.",
            "danger",
        )

        return redirect(
            url_for("approval_dashboard")
        )

    if req.status != "SUBMITTED":

        flash(
            f"This request cannot be approved because "
            f"its current status is {req.status}.",
            "warning",
        )

        return redirect(
            url_for(
                "review_request",
                request_number=req.request_number,
            )
        )

    current_approver = get_current_approver(
        req
    )

    if current_approver != approver_email:

        flash(
            f"It is not your turn to approve this request. "
            f"The current approver is {current_approver}.",
            "warning",
        )

        return redirect(
            url_for("approval_dashboard")
        )

    if has_active_queries(req):

        flash(
            "This request has an active query. "
            "Please close the query before approving.",
            "warning",
        )

        return redirect(
            url_for(
                "request_history",
                request_number=req.request_number,
            )
        )

    current_index = assigned.index(
        approver_email
    )

    is_last_approver = (
        current_index
        == len(assigned) - 1
    )

    if is_last_approver:
        req.status = "APPROVED"
    else:
        req.status = "SUBMITTED"

    req.reviewed_by = approver_email
    req.reviewed_at = datetime.utcnow()
    req.return_comment = None
    req.query_comment = None

    approval_history = ApprovalHistory(
        request_id=req.id,
        approval_level=current_index + 1,
        approver_email=approver_email,
        action="APPROVED",
        comment=None,
        created_at=datetime.utcnow(),
    )

    try:

        db.session.add(
            approval_history
        )

        db.session.commit()

    except Exception as e:

        db.session.rollback()

        print(
            "APPROVAL DATABASE ERROR:",
            e,
        )

        flash(
            "There was an error while approving "
            "the request.",
            "danger",
        )

        return redirect(
            url_for(
                "review_request",
                request_number=req.request_number,
            )
        )

    update_mis(req)

    if is_last_approver:

        send_final_approval_email(
            req
        )

        flash(
            f"Request {req.request_number} "
            f"has been fully approved.",
            "success",
        )

    else:

        next_approver = assigned[
            current_index + 1
        ]

        send_next_approver_email(
            req,
            next_approver,
        )

        flash(
            f"Request {req.request_number} "
            f"has been approved by you and forwarded "
            f"to the next approver: {next_approver}",
            "success",
        )

    return redirect(
        url_for("approval_dashboard")
    )


# =========================================================
# RETURN REQUEST
# =========================================================

@app.route(
    "/return-request/<request_number>",
    methods=["POST"],
)
@approver_required
def return_request(request_number):

    req = get_request_by_number(
        request_number
    )

    if not req:

        flash(
            "Procurement request was not found.",
            "danger",
        )

        return redirect(
            url_for("approval_dashboard")
        )

    approver_email = normalize_email(
        session.get("user_email")
    )

    assigned = get_assigned_approvers(req)

    if approver_email not in assigned:

        flash(
            "You are not assigned to return this request.",
            "danger",
        )

        return redirect(
            url_for("approval_dashboard")
        )

    current_approver = get_current_approver(
        req
    )

    if current_approver != approver_email:

        flash(
            f"It is not your turn to return this request. "
            f"The current approver is {current_approver}.",
            "warning",
        )

        return redirect(
            url_for("approval_dashboard")
        )

    if req.status != "SUBMITTED":

        flash(
            f"This request cannot be returned because "
            f"its current status is {req.status}.",
            "warning",
        )

        return redirect(
            url_for(
                "review_request",
                request_number=req.request_number,
            )
        )

    if has_active_queries(req):

        flash(
            "This request has an active query. "
            "The query must be closed before the request "
            "can be returned.",
            "warning",
        )

        return redirect(
            url_for(
                "request_history",
                request_number=req.request_number,
            )
        )

    return_comment = (
        request.form.get(
            "return_comment",
            "",
        )
        .strip()
    )

    if not return_comment:

        flash(
            "Return comment is required.",
            "danger",
        )

        return redirect(
            url_for(
                "review_request",
                request_number=req.request_number,
            )
        )

    current_index = assigned.index(
        approver_email
    )

    req.status = "RETURNED"
    req.reviewed_by = approver_email
    req.reviewed_at = datetime.utcnow()
    req.return_comment = return_comment

    approval_history = ApprovalHistory(
        request_id=req.id,
        approval_level=current_index + 1,
        approver_email=approver_email,
        action="RETURNED",
        comment=return_comment,
        created_at=datetime.utcnow(),
    )

    try:

        db.session.add(
            approval_history
        )

        db.session.commit()

    except Exception as e:

        db.session.rollback()

        print(
            "RETURN DATABASE ERROR:",
            e,
        )

        flash(
            "There was an error while returning "
            "the request.",
            "danger",
        )

        return redirect(
            url_for(
                "review_request",
                request_number=req.request_number,
            )
        )

    update_mis(req)

    send_request_returned_email(
        req,
        return_comment,
    )

    flash(
        f"Request {req.request_number} "
        f"has been returned successfully.",
        "success",
    )

    return redirect(
        url_for("approval_dashboard")
    )


# =========================================================
# QUERY REQUEST
# =========================================================

@app.route(
    "/query-request/<request_number>",
    methods=["POST"],
)
@approver_required
def query_request(request_number):

    req = get_request_by_number(
        request_number
    )

    if not req:

        flash(
            "Procurement request was not found.",
            "danger",
        )

        return redirect(
            url_for("approval_dashboard")
        )

    sender_email = normalize_email(
        session.get("user_email")
    )

    sender_name = session.get(
        "user_name"
    )

    assigned = get_assigned_approvers(req)

    if sender_email not in assigned:

        flash(
            "You are not assigned to query this request.",
            "danger",
        )

        return redirect(
            url_for("approval_dashboard")
        )

    current_approver = get_current_approver(
        req
    )

    if current_approver != sender_email:

        flash(
            f"It is not your turn to query this request. "
            f"The current approver is {current_approver}.",
            "warning",
        )

        return redirect(
            url_for("approval_dashboard")
        )

    if req.status != "SUBMITTED":

        flash(
            f"This request cannot be queried because "
            f"its current status is {req.status}.",
            "warning",
        )

        return redirect(
            url_for(
                "review_request",
                request_number=req.request_number,
            )
        )

    query_comment = (
        request.form.get(
            "query_comment",
            "",
        )
        .strip()
    )

    if not query_comment:

        flash(
            "Query comment is required.",
            "danger",
        )

        return redirect(
            url_for(
                "review_request",
                request_number=req.request_number,
            )
        )

    query_target = (
        request.form.get(
            "query_target",
            "",
        )
        .strip()
    )

    if not query_target:

        flash(
            "Please select a query participant.",
            "danger",
        )

        return redirect(
            url_for(
                "review_request",
                request_number=req.request_number,
            )
        )

    participants = get_participant_emails(req)

    if query_target.upper() == "ALL":

        recipients = [
            email
            for email in participants
            if email != sender_email
        ]

        recipient_type = "ALL"

    else:

        recipient_email = normalize_email(
            query_target
        )

        if recipient_email not in participants:

            flash(
                "The selected participant is not associated "
                "with this request.",
                "danger",
            )

            return redirect(
                url_for(
                    "review_request",
                    request_number=req.request_number,
                )
            )

        if recipient_email == sender_email:

            flash(
                "You cannot send a query to yourself.",
                "warning",
            )

            return redirect(
                url_for(
                    "review_request",
                    request_number=req.request_number,
                )
            )

        recipients = [
            recipient_email
        ]

        recipient_type = "INDIVIDUAL"

    if not recipients:

        flash(
            "Please select another participant.",
            "warning",
        )

        return redirect(
            url_for(
                "review_request",
                request_number=req.request_number,
            )
        )

    new_queries = []

    for recipient_email in recipients:

        recipient_email = normalize_email(
            recipient_email
        )

        if recipient_email == normalize_email(
            req.requester_email
        ):

            recipient_name = req.requester_name

        else:

            recipient_name = get_user_name(
                recipient_email,
                fallback=recipient_email,
            )

        new_query = QueryMessage(
            request_id=req.id,
            sender_email=sender_email,
            sender_name=sender_name,
            recipient_type=recipient_type,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            message=query_comment,
            status="OPEN",
            reply_to_id=None,
            created_at=datetime.utcnow(),
        )

        new_queries.append(
            new_query
        )

    req.status = "QUERY"
    req.query_comment = query_comment

    try:

        for query in new_queries:
            db.session.add(query)

        db.session.commit()

    except Exception as e:

        db.session.rollback()

        print(
            "QUERY DATABASE ERROR:",
            e,
        )

        flash(
            "There was an error while saving the query.",
            "danger",
        )

        return redirect(
            url_for(
                "review_request",
                request_number=req.request_number,
            )
        )

    update_mis(req)

    send_query_email(
        req,
        recipients,
        sender_name,
        query_comment,
    )

    if query_target.upper() == "ALL":

        flash(
            f"Query has been sent to all participants "
            f"for {req.request_number}.",
            "success",
        )

    else:

        flash(
            f"Confidential query has been sent to "
            f"{query_target} for {req.request_number}.",
            "success",
        )

    return redirect(
        url_for(
            "request_history",
            request_number=req.request_number,
        )
    )


# =========================================================
# RESPOND TO QUERY
# =========================================================

@app.route(
    "/respond-query/<int:query_id>",
    methods=["POST"],
)
@login_required
def respond_query(query_id):

    query = QueryMessage.query.get(
        query_id
    )

    if not query:

        flash(
            "Query was not found.",
            "danger",
        )

        return redirect_to_dashboard()

    user_email = normalize_email(
        session.get("user_email")
    )

    if not user_can_access_query(
        query,
        user_email,
    ):

        flash(
            "You are not authorized to access this query.",
            "danger",
        )

        return redirect_to_dashboard()

    recipient_email = normalize_email(
        query.recipient_email
    )

    if recipient_email != user_email:

        flash(
            "Only the recipient of this query can respond.",
            "danger",
        )

        return redirect_to_dashboard()

    if query.reply_to_id is not None:

        flash(
            "This message is not an original query.",
            "warning",
        )

        return redirect_to_dashboard()

    if query.status != "OPEN":

        flash(
            "This query is no longer open for response.",
            "warning",
        )

        return redirect_to_dashboard()

    response_text = (
        request.form.get(
            "response",
            "",
        )
        .strip()
    )

    if not response_text:

        flash(
            "Response is required.",
            "danger",
        )

        req = ProcurementRequest.query.get(
            query.request_id
        )

        if req:

            return redirect(
                url_for(
                    "request_history",
                    request_number=req.request_number,
                )
            )

        return redirect_to_dashboard()

    reply = QueryMessage(
        request_id=query.request_id,
        sender_email=user_email,
        sender_name=session.get(
            "user_name"
        ),
        recipient_type="INDIVIDUAL",
        recipient_email=query.sender_email,
        recipient_name=query.sender_name,
        message=response_text,
        status="RESPONDED",
        reply_to_id=query.id,
        created_at=datetime.utcnow(),
    )

    query.status = "RESPONDED"
    query.responded_at = datetime.utcnow()

    try:

        db.session.add(
            reply
        )

        db.session.commit()

    except Exception as e:

        db.session.rollback()

        print(
            "QUERY RESPONSE DATABASE ERROR:",
            e,
        )

        flash(
            "There was an error while saving "
            "your response.",
            "danger",
        )

        return redirect_to_dashboard()

    req = ProcurementRequest.query.get(
        query.request_id
    )

    if req:

        req.status = "QUERY"

        try:

            db.session.commit()

            update_mis(req)

        except Exception as e:

            db.session.rollback()

            print(
                "QUERY REQUEST STATUS ERROR:",
                e,
            )

    send_query_response_email(
        query,
        response_text,
    )

    flash(
        "Your response has been submitted successfully.",
        "success",
    )

    if req:

        return redirect(
            url_for(
                "request_history",
                request_number=req.request_number,
            )
        )

    return redirect_to_dashboard()


# =========================================================
# CLOSE QUERY
# =========================================================

@app.route(
    "/close-query/<int:query_id>",
    methods=["POST"],
)
@approver_required
def close_query(query_id):

    query = QueryMessage.query.get(
        query_id
    )

    if not query:

        flash(
            "Query was not found.",
            "danger",
        )

        return redirect(
            url_for("approval_dashboard")
        )

    approver_email = normalize_email(
        session.get("user_email")
    )

    root_query = get_query_root(
        query
    )

    if not root_query:

        flash(
            "Original query could not be found.",
            "danger",
        )

        return redirect(
            url_for("approval_dashboard")
        )

    if normalize_email(
        root_query.sender_email
    ) != approver_email:

        flash(
            "Only the approver who raised this query "
            "can close it.",
            "danger",
        )

        return redirect(
            url_for("approval_dashboard")
        )

    req = ProcurementRequest.query.get(
        root_query.request_id
    )

    if not req:

        flash(
            "Associated procurement request was not found.",
            "danger",
        )

        return redirect(
            url_for("approval_dashboard")
        )

    if approver_email not in get_assigned_approvers(
        req
    ):

        flash(
            "You are not assigned to this request.",
            "danger",
        )

        return redirect(
            url_for("approval_dashboard")
        )

    if root_query.status != "RESPONDED":

        flash(
            "Only a responded query can be closed.",
            "warning",
        )

        return redirect(
            url_for(
                "request_history",
                request_number=req.request_number,
            )
        )

    thread = get_query_thread(
        root_query
    )

    for message in thread:

        if message.status in [
            "OPEN",
            "RESPONDED",
        ]:

            message.status = "CLOSED"

    remaining_active_queries = (
        QueryMessage.query
        .filter(
            QueryMessage.request_id == req.id,
            QueryMessage.reply_to_id.is_(None),
            QueryMessage.status.in_(
                [
                    "OPEN",
                    "RESPONDED",
                ]
            ),
        )
        .count()
    )

    if remaining_active_queries == 0:

        req.status = "SUBMITTED"
        req.query_comment = None

        message = (
            f"Query #{root_query.id} has been closed. "
            f"Request {req.request_number} is now "
            f"available for review again."
        )

    else:

        req.status = "QUERY"

        message = (
            f"Query #{root_query.id} has been closed. "
            f"There are still "
            f"{remaining_active_queries} active "
            f"query thread(s) for this request."
        )

    try:

        db.session.commit()

    except Exception as e:

        db.session.rollback()

        print(
            "CLOSE QUERY DATABASE ERROR:",
            e,
        )

        flash(
            "There was an error while closing the query.",
            "danger",
        )

        return redirect(
            url_for("approval_dashboard")
        )

    update_mis(req)

    send_query_closed_email(
        req,
        root_query,
    )

    flash(
        message,
        "success",
    )

    return redirect(
        url_for(
            "request_history",
            request_number=req.request_number,
        )
    )


# =========================================================
# REQUEST ATTACHMENT
# =========================================================

@app.route(
    "/request-attachment/<filename>"
)
@login_required
def request_attachment(filename):

    upload_folder = get_upload_folder()

    if not upload_folder:

        flash(
            "Upload folder is not configured.",
            "danger",
        )

        return redirect_to_dashboard()

    safe_filename = secure_filename(
        filename
    )

    if (
        not safe_filename
        or safe_filename != filename
    ):

        flash(
            "Invalid attachment filename.",
            "danger",
        )

        return redirect_to_dashboard()

    user_email = normalize_email(
        session.get("user_email")
    )

    requests = ProcurementRequest.query.all()

    authorized = False

    for req in requests:

        filenames = [
            item.strip()
            for item in (
                req.attachment_filename or ""
            ).split(",")
            if item.strip()
        ]

        if safe_filename not in filenames:
            continue

        requester = normalize_email(
            req.requester_email
        )

        assigned = get_assigned_approvers(
            req
        )

        if (
            user_email == requester
            or user_email in assigned
        ):

            authorized = True
            break

    if not authorized:

        flash(
            "You are not authorized to access this attachment.",
            "danger",
        )

        return redirect_to_dashboard()

    file_path = os.path.join(
        upload_folder,
        safe_filename,
    )

    if not os.path.exists(
        file_path
    ):

        flash(
            "Attachment file was not found.",
            "danger",
        )

        return redirect_to_dashboard()

    return send_from_directory(
        upload_folder,
        safe_filename,
    )


# =========================================================
# COMPLETE REQUEST HISTORY
# =========================================================

@app.route(
    "/request-history/<request_number>",
    methods=["GET"],
)
@login_required
def request_history(request_number):

    req = get_request_by_number(
        request_number
    )

    if not req:

        flash(
            "Procurement request was not found.",
            "danger",
        )

        return redirect_to_dashboard()

    user_email = normalize_email(
        session.get("user_email")
    )

    requester = normalize_email(
        req.requester_email
    )

    assigned = get_assigned_approvers(
        req
    )

    if (
        user_email != requester
        and user_email not in assigned
    ):

        flash(
            "You are not authorized to access this request.",
            "danger",
        )

        return redirect_to_dashboard()

    approval_history = get_approval_history(
        req
    )

    query_history = get_queries_for_user(
        req,
        user_email,
    )

    query_threads = get_query_threads_for_user(
        req,
        user_email,
    )

    all_query_history = get_query_history(
        req
    )

    active_queries = [
        query
        for query in get_active_queries(req)
        if user_can_access_query(
            query,
            user_email,
        )
    ]

    participant_emails = get_participant_emails(
        req
    )

    participant_details = get_participant_details(
        req
    )

    current_approver = get_current_approver(
        req
    )

    latest_query = get_latest_query_message(
        req,
        user_email,
    )

    attachments = [
        filename.strip()
        for filename in (
            req.attachment_filename or ""
        ).split(",")
        if filename.strip()
    ]

    return render_template(
        "query_history.html",

        req=req,

        requester_name=req.requester_name,
        requester_email=req.requester_email,
        employee_id=req.employee_id,
        department=req.department,
        designation=req.designation,
        request_date=req.request_date,

        request_number=req.request_number,
        status=req.status,
        item_description=req.item_description,
        business_requirement=req.business_requirement,
        boq=req.boq,
        created_at=req.created_at,
        updated_at=req.updated_at,

        approval_history=approval_history,
        current_approver=current_approver,

        query_history=query_history,
        all_query_history=all_query_history,
        query_threads=query_threads,
        active_queries=active_queries,
        latest_query=latest_query,

        participant_emails=participant_emails,
        participant_details=participant_details,

        attachments=attachments,

        user_email=user_email,
        user_role=session.get("role"),
        user_name=session.get("user_name"),

        review_url=url_for(
            "review_request",
            request_number=req.request_number,
        ),

        dashboard_url=(
            url_for("approval_dashboard")
            if session.get("role") == "APPROVER"
            else url_for("dashboard")
        ),
    )


# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(404)
def page_not_found(error):

    return render_template(
        "404.html"
    ), 404


@app.errorhandler(500)
def internal_server_error(error):

    db.session.rollback()

    return render_template(
        "500.html"
    ), 500


# =========================================================
# APPLICATION START
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )
