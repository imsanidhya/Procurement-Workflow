from io import BytesIO
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)


# =========================================================
# PDF COLORS
# =========================================================

PRIMARY_COLOR = colors.HexColor("#0d6efd")
DARK_COLOR = colors.HexColor("#212529")
LIGHT_COLOR = colors.HexColor("#f5f7fa")
BORDER_COLOR = colors.HexColor("#d9dee5")
SUCCESS_COLOR = colors.HexColor("#198754")
WARNING_COLOR = colors.HexColor("#ffc107")
DANGER_COLOR = colors.HexColor("#dc3545")
MUTED_COLOR = colors.HexColor("#6c757d")
INFO_COLOR = colors.HexColor("#0dcaf0")
QUERY_COLOR = colors.HexColor("#6f42c1")


# =========================================================
# HELPER - SAFE VALUE
# =========================================================

def safe_value(value, default="N/A"):
    """
    Convert a value into safe display text.

    User-entered values are escaped so that characters such as
    &, < and > do not break ReportLab Paragraph XML.
    """

    if value is None:
        return default

    if isinstance(value, str):
        value = value.strip()

        if not value:
            return default

    value = str(value)

    return escape(value)


# =========================================================
# HELPER - SAFE MULTILINE VALUE
# =========================================================

def safe_multiline(value, default="N/A"):
    """
    Safely prepare multiline user-entered text for ReportLab.
    """

    if value is None:
        return default

    if isinstance(value, str):
        value = value.strip()

        if not value:
            return default

    value = escape(str(value))

    # Preserve normal line breaks inside ReportLab Paragraphs.
    value = value.replace("\r\n", "\n")
    value = value.replace("\r", "\n")
    value = value.replace("\n", "<br/>")

    return value


# =========================================================
# HELPER - FORMAT DATE
# =========================================================

def format_date(value):
    if not value:
        return "N/A"

    if isinstance(value, datetime):
        return value.strftime("%d-%b-%Y %H:%M")

    try:
        return value.strftime("%d-%b-%Y")

    except Exception:
        return escape(str(value))


# =========================================================
# HELPER - FORMAT DATETIME
# =========================================================

def format_datetime(value):
    if not value:
        return "N/A"

    try:
        return value.strftime("%d-%b-%Y %H:%M")

    except Exception:
        return escape(str(value))


# =========================================================
# HELPER - STATUS COLOR
# =========================================================

def get_status_color(status):

    status = (
        safe_value(
            status,
            ""
        )
        .upper()
    )

    if status == "APPROVED":
        return SUCCESS_COLOR

    if status == "RETURNED":
        return DANGER_COLOR

    if status in ("SUBMITTED", "PENDING"):
        return WARNING_COLOR

    if status in ("DRAFT", "CANCELLED"):
        return MUTED_COLOR

    if status in ("QUERY", "QUERIED", "QUERY_PENDING"):
        return QUERY_COLOR

    return PRIMARY_COLOR


# =========================================================
# HELPER - ACTION COLOR
# =========================================================

def get_action_color(action):

    action = (
        safe_value(
            action,
            ""
        )
        .upper()
    )

    if action in ("APPROVED", "APPROVE"):
        return SUCCESS_COLOR

    if action in ("RETURNED", "RETURN"):
        return DANGER_COLOR

    if action in ("QUERY", "QUERIED"):
        return QUERY_COLOR

    if action in ("PENDING", "SUBMITTED"):
        return WARNING_COLOR

    return PRIMARY_COLOR


# =========================================================
# HEADER / FOOTER
# =========================================================

def draw_page_header_footer(canvas, doc):

    canvas.saveState()

    width, height = A4

    # -----------------------------------------------------
    # TOP LINE
    # -----------------------------------------------------

    canvas.setStrokeColor(PRIMARY_COLOR)
    canvas.setLineWidth(1.2)

    canvas.line(
        18 * mm,
        height - 15 * mm,
        width - 18 * mm,
        height - 15 * mm
    )

    # -----------------------------------------------------
    # HEADER
    # -----------------------------------------------------

    canvas.setFont(
        "Helvetica-Bold",
        9
    )

    canvas.setFillColor(DARK_COLOR)

    canvas.drawString(
        18 * mm,
        height - 11 * mm,
        "PROCUREMENT WORKFLOW SYSTEM"
    )

    # -----------------------------------------------------
    # FOOTER LINE
    # -----------------------------------------------------

    canvas.setStrokeColor(BORDER_COLOR)
    canvas.setLineWidth(0.6)

    canvas.line(
        18 * mm,
        14 * mm,
        width - 18 * mm,
        14 * mm
    )

    # -----------------------------------------------------
    # FOOTER TEXT
    # -----------------------------------------------------

    canvas.setFont(
        "Helvetica",
        8
    )

    canvas.setFillColor(MUTED_COLOR)

    canvas.drawString(
        18 * mm,
        9 * mm,
        "Procurement Request"
    )

    canvas.drawRightString(
        width - 18 * mm,
        9 * mm,
        f"Page {doc.page}"
    )

    canvas.restoreState()


# =========================================================
# SECTION TITLE
# =========================================================

def section_title(text, styles):

    return Paragraph(
        safe_value(text),
        styles["SectionTitle"]
    )


# =========================================================
# INFORMATION TABLE
# =========================================================

def create_information_table(
    rows,
    styles,
    col_widths=None
):

    table_data = []

    for label, value in rows:

        table_data.append(
            [
                Paragraph(
                    f"<b>{safe_value(label)}</b>",
                    styles["TableLabel"]
                ),

                Paragraph(
                    safe_multiline(value),
                    styles["TableValue"]
                )
            ]
        )

    if not col_widths:

        col_widths = [
            48 * mm,
            132 * mm
        ]

    table = Table(
        table_data,
        colWidths=col_widths,
        repeatRows=0
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    LIGHT_COLOR
                ),

                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    BORDER_COLOR
                ),

                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    BORDER_COLOR
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                ),
            ]
        )
    )

    return table


# =========================================================
# APPROVAL HISTORY TABLE
# =========================================================

def create_approval_history_table(
    req,
    styles
):

    headers = [
        "Level",
        "Approver",
        "Action",
        "Comment",
        "Date"
    ]

    table_data = [
        [
            Paragraph(
                f"<b>{safe_value(header)}</b>",
                styles["TableHeader"]
            )
            for header in headers
        ]
    ]

    history = (
        req.approval_history
        if req.approval_history
        else []
    )

    # -----------------------------------------------------
    # No approval history
    # -----------------------------------------------------

    if not history:

        table_data.append(
            [
                Paragraph(
                    "—",
                    styles["TableValue"]
                ),

                Paragraph(
                    "No approval action recorded",
                    styles["TableValue"]
                ),

                Paragraph(
                    "PENDING",
                    styles["TableValue"]
                ),

                Paragraph(
                    "",
                    styles["TableValue"]
                ),

                Paragraph(
                    "",
                    styles["TableValue"]
                )
            ]
        )

    else:

        for history_item in history:

            action = safe_value(
                history_item.action
            )

            action_style = ParagraphStyle(
                "HistoryAction",
                parent=styles["TableValue"],
                textColor=get_action_color(action),
                fontName="Helvetica-Bold"
            )

            table_data.append(
                [
                    Paragraph(
                        safe_value(
                            history_item.approval_level
                        ),
                        styles["TableValue"]
                    ),

                    Paragraph(
                        safe_value(
                            history_item.approver_email
                        ),
                        styles["TableValue"]
                    ),

                    Paragraph(
                        action,
                        action_style
                    ),

                    Paragraph(
                        safe_multiline(
                            history_item.comment,
                            ""
                        ),
                        styles["TableValue"]
                    ),

                    Paragraph(
                        format_datetime(
                            history_item.created_at
                        ),
                        styles["TableValue"]
                    )
                ]
            )

    table = Table(
        table_data,
        colWidths=[
            14 * mm,
            42 * mm,
            27 * mm,
            57 * mm,
            40 * mm
        ],
        repeatRows=1
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    PRIMARY_COLOR
                ),

                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
                ),

                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    BORDER_COLOR
                ),

                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    BORDER_COLOR
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),

                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        LIGHT_COLOR
                    ]
                )
            ]
        )
    )

    return table


# =========================================================
# QUERY HISTORY
# =========================================================

def create_query_history_section(
    req,
    styles
):

    story = []

    messages = (
        req.query_messages
        if req.query_messages
        else []
    )

    # -----------------------------------------------------
    # No query history
    # -----------------------------------------------------

    if not messages:

        story.append(
            Paragraph(
                "No query or communication history recorded.",
                styles["Body"]
            )
        )

        return story

    # -----------------------------------------------------
    # Sort messages chronologically
    # -----------------------------------------------------

    messages = sorted(
        messages,
        key=lambda item: (
            item.created_at
            or datetime.min
        )
    )

    # -----------------------------------------------------
    # Query history cards
    # -----------------------------------------------------

    for index, message in enumerate(
        messages,
        start=1
    ):

        recipient = (
            message.recipient_email
            if message.recipient_email
            else message.recipient_type
        )

        sender_name = (
            message.sender_name
            if message.sender_name
            else message.sender_email
        )

        status = safe_value(
            message.status,
            "OPEN"
        ).upper()

        query_header = Table(
            [
                [
                    Paragraph(
                        f"<b>Communication #{index}</b>",
                        styles["TableLabel"]
                    ),

                    Paragraph(
                        format_datetime(
                            message.created_at
                        ),
                        styles["TableValue"]
                    )
                ]
            ],
            colWidths=[
                120 * mm,
                60 * mm
            ]
        )

        query_header.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        LIGHT_COLOR
                    ),

                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.6,
                        BORDER_COLOR
                    ),

                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP"
                    ),

                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        7
                    ),

                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        7
                    ),

                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6
                    ),

                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6
                    )
                ]
            )
        )

        story.append(
            query_header
        )

        story.append(
            Spacer(
                1,
                3
            )
        )

        details = [
            (
                "Sender",
                sender_name
            ),

            (
                "Sender Email",
                message.sender_email
            ),

            (
                "Recipient",
                recipient
            ),

            (
                "Recipient Name",
                message.recipient_name
            ),

            (
                "Status",
                status
            ),

            (
                "Message",
                message.message
            )
        ]

        if message.reply_to_id:

            details.insert(
                0,
                (
                    "Reply To",
                    f"Communication #{message.reply_to_id}"
                )
            )

        story.append(
            create_information_table(
                details,
                styles
            )
        )

        story.append(
            Spacer(
                1,
                8
            )
        )

    return story


# =========================================================
# MAIN PDF GENERATOR
# =========================================================

def generate_request_pdf(req):

    buffer = BytesIO()

    # =====================================================
    # DOCUMENT
    # =====================================================

    document = SimpleDocTemplate(

        buffer,

        pagesize=A4,

        rightMargin=18 * mm,

        leftMargin=18 * mm,

        topMargin=22 * mm,

        bottomMargin=20 * mm,

        title=(
            f"Procurement Request "
            f"{safe_value(req.request_number)}"
        ),

        author="Procurement Workflow System",

        subject=(
            f"Procurement Request "
            f"{safe_value(req.request_number)}"
        )
    )

    # =====================================================
    # STYLES
    # =====================================================

    base_styles = getSampleStyleSheet()

    styles = {}

    styles["TitleCustom"] = ParagraphStyle(

        "TitleCustom",

        parent=base_styles["Title"],

        fontName="Helvetica-Bold",

        fontSize=18,

        leading=22,

        textColor=PRIMARY_COLOR,

        alignment=TA_CENTER,

        spaceAfter=5
    )

    styles["Subtitle"] = ParagraphStyle(

        "Subtitle",

        parent=base_styles["Normal"],

        fontName="Helvetica",

        fontSize=9,

        leading=12,

        textColor=MUTED_COLOR,

        alignment=TA_CENTER,

        spaceAfter=12
    )

    styles["SectionTitle"] = ParagraphStyle(

        "SectionTitle",

        parent=base_styles["Heading2"],

        fontName="Helvetica-Bold",

        fontSize=11,

        leading=14,

        textColor=DARK_COLOR,

        spaceBefore=12,

        spaceAfter=6
    )

    styles["TableLabel"] = ParagraphStyle(

        "TableLabel",

        parent=base_styles["Normal"],

        fontName="Helvetica-Bold",

        fontSize=8.5,

        leading=11,

        textColor=DARK_COLOR
    )

    styles["TableValue"] = ParagraphStyle(

        "TableValue",

        parent=base_styles["Normal"],

        fontName="Helvetica",

        fontSize=8.5,

        leading=11,

        textColor=DARK_COLOR
    )

    styles["TableHeader"] = ParagraphStyle(

        "TableHeader",

        parent=base_styles["Normal"],

        fontName="Helvetica-Bold",

        fontSize=8,

        leading=10,

        textColor=colors.white,

        alignment=TA_LEFT
    )

    styles["Body"] = ParagraphStyle(

        "Body",

        parent=base_styles["Normal"],

        fontName="Helvetica",

        fontSize=9,

        leading=13,

        textColor=DARK_COLOR,

        spaceAfter=6
    )

    # =====================================================
    # STORY
    # =====================================================

    story = []

    # =====================================================
    # TITLE
    # =====================================================

    story.append(
        Paragraph(
            "PROCUREMENT REQUEST",
            styles["TitleCustom"]
        )
    )

    story.append(
        Paragraph(
            (
                f"Request Number: "
                f"<b>{safe_value(req.request_number)}</b>"
            ),
            styles["Subtitle"]
        )
    )

    # =====================================================
    # STATUS
    # =====================================================

    status = safe_value(
        req.status
    ).upper()

    status_style = ParagraphStyle(
        "StatusValue",
        parent=styles["TableValue"],
        fontName="Helvetica-Bold",
        textColor=get_status_color(status)
    )

    status_table = Table(
        [
            [
                Paragraph(
                    "<b>Current Status</b>",
                    styles["TableLabel"]
                ),

                Paragraph(
                    status,
                    status_style
                )
            ]
        ],
        colWidths=[
            48 * mm,
            132 * mm
        ]
    )

    status_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, 0),
                    LIGHT_COLOR
                ),

                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.8,
                    BORDER_COLOR
                ),

                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    BORDER_COLOR
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                )
            ]
        )
    )

    story.append(
        status_table
    )

    story.append(
        Spacer(
            1,
            8
        )
    )

    # =====================================================
    # REQUEST INFORMATION
    # =====================================================

    story.append(
        section_title(
            "Request Information",
            styles
        )
    )

    story.append(
        create_information_table(
            [
                (
                    "Request Number",
                    req.request_number
                ),

                (
                    "Request Date",
                    format_date(
                        req.request_date
                    )
                ),

                (
                    "Request Type",
                    req.request_type
                ),

                (
                    "Subject",
                    req.subject
                ),

                (
                    "Priority",
                    req.priority
                ),

                (
                    "Created",
                    format_datetime(
                        req.created_at
                    )
                ),

                (
                    "Last Updated",
                    format_datetime(
                        req.updated_at
                    )
                )
            ],
            styles
        )
    )

    # =====================================================
    # REQUESTER INFORMATION
    # =====================================================

    story.append(
        section_title(
            "Requester Information",
            styles
        )
    )

    story.append(
        create_information_table(
            [
                (
                    "Requester Name",
                    req.requester_name
                ),

                (
                    "Organization Email",
                    req.requester_email
                ),

                (
                    "Employee ID",
                    req.employee_id
                ),

                (
                    "Department",
                    req.department
                ),

                (
                    "Designation",
                    req.designation
                )
            ],
            styles
        )
    )

    # =====================================================
    # REQUIREMENT INFORMATION
    # =====================================================

    story.append(
        section_title(
            "Requirement Information",
            styles
        )
    )

    story.append(
        create_information_table(
            [
                (
                    "Item Name",
                    req.item_name
                ),

                (
                    "Requirement Description",
                    req.item_description
                ),

                (
                    "Quantity",
                    req.quantity
                ),

                (
                    "Estimated Budget",
                    req.estimated_budget
                ),

                (
                    "Business Requirement",
                    req.business_requirement
                ),

                (
                    "Business Justification",
                    req.business_justification
                ),

                (
                    "Expected Benefits",
                    req.expected_benefits
                ),

                (
                    "BOQ / Quantity Details",
                    req.boq
                )
            ],
            styles
        )
    )

    # =====================================================
    # APPROVAL WORKFLOW
    # =====================================================

    story.append(
        section_title(
            "Approval Workflow",
            styles
        )
    )

    assigned_approvers = [

        email.strip()

        for email in (
            req.approver_emails or ""
        ).split(",")

        if email.strip()
    ]

    approver_rows = []

    for index, email in enumerate(
        assigned_approvers,
        start=1
    ):

        approver_rows.append(
            (
                f"Level {index}",
                email
            )
        )

    if not approver_rows:

        approver_rows.append(
            (
                "—",
                "No approvers configured"
            )
        )

    story.append(
        create_information_table(
            approver_rows,
            styles,
            col_widths=[
                48 * mm,
                132 * mm
            ]
        )
    )

    # =====================================================
    # APPROVAL HISTORY
    # =====================================================

    story.append(
        section_title(
            "Approval History",
            styles
        )
    )

    story.append(
        create_approval_history_table(
            req,
            styles
        )
    )

    # =====================================================
    # QUERY / COMMUNICATION HISTORY
    # =====================================================

    story.append(
        section_title(
            "Query & Communication History",
            styles
        )
    )

    story.extend(
        create_query_history_section(
            req,
            styles
        )
    )

    # =====================================================
    # LEGACY LATEST QUERY
    # =====================================================

    # Keep this for compatibility with older records.
    # It will only appear when there is a legacy query
    # that is not already represented in QueryMessage.

    if req.query_comment:

        story.append(
            section_title(
                "Legacy Query Comment",
                styles
            )
        )

        story.append(
            Paragraph(
                safe_multiline(
                    req.query_comment
                ),
                styles["Body"]
            )
        )

    # =====================================================
    # RETURN COMMENT
    # =====================================================

    if req.return_comment:

        story.append(
            section_title(
                "Return Comment",
                styles
            )
        )

        story.append(
            Paragraph(
                safe_multiline(
                    req.return_comment
                ),
                styles["Body"]
            )
        )

    # =====================================================
    # REVIEW INFORMATION
    # =====================================================

    if req.reviewed_by or req.reviewed_at:

        story.append(
            section_title(
                "Review Information",
                styles
            )
        )

        story.append(
            create_information_table(
                [
                    (
                        "Reviewed By",
                        req.reviewed_by
                    ),

                    (
                        "Reviewed At",
                        format_datetime(
                            req.reviewed_at
                        )
                    )
                ],
                styles
            )
        )

    # =====================================================
    # ATTACHMENT INFORMATION
    # =====================================================

    if req.attachment_filename:

        story.append(
            section_title(
                "Supporting Documents",
                styles
            )
        )

        attachments = [

            filename.strip()

            for filename in (
                req.attachment_filename or ""
            ).split(",")

            if filename.strip()
        ]

        for filename in attachments:

            story.append(
                Paragraph(
                    f"• {safe_value(filename)}",
                    styles["Body"]
                )
            )

    # =====================================================
    # DECLARATION
    # =====================================================

    story.append(
        section_title(
            "Declaration",
            styles
        )
    )

    story.append(
        Paragraph(
            (
                "This document represents the procurement request "
                "record maintained by the Procurement Workflow System. "
                "The information contained in this document reflects "
                "the request, communication history, approval history "
                "and workflow status recorded in the system at the "
                "time the PDF was generated."
            ),
            styles["Body"]
        )
    )

    # =====================================================
    # GENERATED INFORMATION
    # =====================================================

    story.append(
        Spacer(
            1,
            8
        )
    )

    generated_at = datetime.now().strftime(
        "%d-%b-%Y %H:%M"
    )

    generated_table = Table(
        [
            [
                Paragraph(
                    "<b>PDF Generated</b>",
                    styles["TableLabel"]
                ),

                Paragraph(
                    safe_value(generated_at),
                    styles["TableValue"]
                )
            ]
        ],
        colWidths=[
            48 * mm,
            132 * mm
        ]
    )

    generated_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, 0),
                    LIGHT_COLOR
                ),

                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    BORDER_COLOR
                ),

                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    BORDER_COLOR
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                )
            ]
        )
    )

    story.append(
        generated_table
    )

    # =====================================================
    # BUILD PDF
    # =====================================================

    document.build(
        story,
        onFirstPage=draw_page_header_footer,
        onLaterPages=draw_page_header_footer
    )

    buffer.seek(0)

    return buffer
