from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash


# =========================================================
# DATABASE
# =========================================================

db = SQLAlchemy()


# =========================================================
# PROCUREMENT REQUEST
# =========================================================

class ProcurementRequest(db.Model):

    __tablename__ = "procurement_requests"


    # =====================================================
    # PRIMARY KEY
    # =====================================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )


    # =====================================================
    # REQUEST IDENTIFICATION
    # =====================================================

    request_number = db.Column(
        db.String(30),
        unique=True,
        nullable=False
    )

    request_date = db.Column(
        db.Date,
        nullable=False
    )


    # =====================================================
    # REQUESTER INFORMATION
    # =====================================================

    requester_name = db.Column(
        db.String(150),
        nullable=False
    )

    requester_email = db.Column(
        db.String(255),
        nullable=False
    )

    employee_id = db.Column(
        db.String(50)
    )

    department = db.Column(
        db.String(150)
    )

    designation = db.Column(
        db.String(150)
    )


    # =====================================================
    # REQUEST INFORMATION
    # =====================================================

    request_type = db.Column(
        db.String(100),
        nullable=True,
        default="Procurement / Business Requirement"
    )

    subject = db.Column(
        db.String(255),
        nullable=True
    )

    priority = db.Column(
        db.String(20),
        nullable=True,
        default="Medium"
    )


    # =====================================================
    # ITEM / REQUIREMENT INFORMATION
    # =====================================================

    item_name = db.Column(
        db.String(255),
        nullable=True
    )

    item_description = db.Column(
        db.Text,
        nullable=True
    )

    quantity = db.Column(
        db.Integer,
        nullable=True
    )

    estimated_budget = db.Column(
        db.Numeric(15, 2),
        nullable=True
    )


    # =====================================================
    # BUSINESS REQUIREMENT
    # =====================================================

    business_requirement = db.Column(
        db.Text,
        nullable=True
    )

    business_justification = db.Column(
        db.Text,
        nullable=True
    )

    expected_benefits = db.Column(
        db.Text,
        nullable=True
    )


    # =====================================================
    # BOQ
    # =====================================================

    boq = db.Column(
        db.Text,
        nullable=True
    )


    # =====================================================
    # APPROVER INFORMATION
    # =====================================================

    approver_emails = db.Column(
        db.Text,
        nullable=True
    )


    # =====================================================
    # WORKFLOW STATUS
    # =====================================================

    status = db.Column(
        db.String(50),
        nullable=False,
        default="SUBMITTED"
    )


    # =====================================================
    # REVIEW INFORMATION
    # =====================================================

    reviewed_by = db.Column(
        db.String(255),
        nullable=True
    )

    reviewed_at = db.Column(
        db.DateTime,
        nullable=True
    )


    # =====================================================
    # LEGACY QUERY INFORMATION
    # =====================================================
    # Kept for compatibility with the existing application.
    # New queries will be stored in QueryMessage.

    query_comment = db.Column(
        db.Text,
        nullable=True
    )


    # =====================================================
    # RETURN INFORMATION
    # =====================================================

    return_comment = db.Column(
        db.Text,
        nullable=True
    )


    # =====================================================
    # ATTACHMENT
    # =====================================================

    attachment_filename = db.Column(
        db.String(255),
        nullable=True
    )


    # =====================================================
    # TIMESTAMPS
    # =====================================================

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


    # =====================================================
    # RELATIONSHIP - APPROVAL HISTORY
    # =====================================================

    approval_history = db.relationship(
        "ApprovalHistory",
        back_populates="request",
        cascade="all, delete-orphan",
        order_by="ApprovalHistory.created_at"
    )


    # =====================================================
    # RELATIONSHIP - QUERY HISTORY
    # =====================================================

    query_messages = db.relationship(
        "QueryMessage",
        back_populates="request",
        cascade="all, delete-orphan",
        order_by="QueryMessage.created_at"
    )


    # =====================================================
    # REPRESENTATION
    # =====================================================

    def __repr__(self):

        return f"<ProcurementRequest {self.request_number}>"


# =========================================================
# APPROVAL HISTORY
# =========================================================

class ApprovalHistory(db.Model):

    __tablename__ = "approval_history"


    # =====================================================
    # PRIMARY KEY
    # =====================================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )


    # =====================================================
    # REQUEST RELATIONSHIP
    # =====================================================

    request_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "procurement_requests.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )


    request = db.relationship(
        "ProcurementRequest",
        back_populates="approval_history"
    )


    # =====================================================
    # APPROVAL LEVEL
    # =====================================================

    approval_level = db.Column(
        db.Integer,
        nullable=False
    )


    # =====================================================
    # APPROVER
    # =====================================================

    approver_email = db.Column(
        db.String(255),
        nullable=False
    )


    # =====================================================
    # ACTION
    # =====================================================

    action = db.Column(
        db.String(50),
        nullable=False
    )


    # =====================================================
    # COMMENT
    # =====================================================

    comment = db.Column(
        db.Text,
        nullable=True
    )


    # =====================================================
    # TIMESTAMP
    # =====================================================

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )


    # =====================================================
    # REPRESENTATION
    # =====================================================

    def __repr__(self):

        return (
            f"<ApprovalHistory "
            f"{self.approver_email} "
            f"{self.action}>"
        )


# =========================================================
# QUERY MESSAGE
# =========================================================

class QueryMessage(db.Model):

    __tablename__ = "query_messages"


    # =====================================================
    # PRIMARY KEY
    # =====================================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )


    # =====================================================
    # REQUEST RELATIONSHIP
    # =====================================================

    request_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "procurement_requests.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )


    request = db.relationship(
        "ProcurementRequest",
        back_populates="query_messages"
    )


    # =====================================================
    # SENDER INFORMATION
    # =====================================================

    sender_email = db.Column(
        db.String(255),
        nullable=False
    )

    sender_name = db.Column(
        db.String(150),
        nullable=True
    )


    # =====================================================
    # RECIPIENT INFORMATION
    # =====================================================
    # recipient_type:
    #
    # INDIVIDUAL = query sent to one selected participant
    # ALL        = query sent to all participants
    #
    # recipient_email is used when recipient_type is
    # INDIVIDUAL.

    recipient_type = db.Column(
        db.String(20),
        nullable=False,
        default="INDIVIDUAL"
    )

    recipient_email = db.Column(
        db.String(255),
        nullable=True
    )

    recipient_name = db.Column(
        db.String(150),
        nullable=True
    )


    # =====================================================
    # QUERY MESSAGE
    # =====================================================

    message = db.Column(
        db.Text,
        nullable=False
    )


    # =====================================================
    # QUERY STATUS
    # =====================================================

    status = db.Column(
        db.String(30),
        nullable=False,
        default="OPEN"
    )


    # =====================================================
    # REPLY RELATIONSHIP
    # =====================================================
    # Allows a future query reply to be linked to the
    # original query.

    reply_to_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "query_messages.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )


    reply_to = db.relationship(
        "QueryMessage",
        remote_side=[id],
        backref=db.backref(
            "replies",
            lazy=True
        )
    )


    # =====================================================
    # TIMESTAMP
    # =====================================================

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    responded_at = db.Column(
        db.DateTime,
        nullable=True
    )


    # =====================================================
    # REPRESENTATION
    # =====================================================

    def __repr__(self):

        return (
            f"<QueryMessage "
            f"{self.sender_email} -> "
            f"{self.recipient_email or self.recipient_type}>"
        )


# =========================================================
# USER
# =========================================================

class User(db.Model):

    __tablename__ = "users"


    # =====================================================
    # PRIMARY KEY
    # =====================================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )


    # =====================================================
    # USER INFORMATION
    # =====================================================

    employee_id = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    name = db.Column(
        db.String(150),
        nullable=False
    )

    email = db.Column(
        db.String(255),
        unique=True,
        nullable=False
    )

    department = db.Column(
        db.String(150),
        nullable=True
    )

    designation = db.Column(
        db.String(150),
        nullable=True
    )


    # =====================================================
    # AUTHENTICATION
    # =====================================================

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )


    # =====================================================
    # ROLE
    # =====================================================

    role = db.Column(
        db.String(50),
        nullable=False,
        default="EMPLOYEE"
    )


    # =====================================================
    # ACCOUNT STATUS
    # =====================================================

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )


    # =====================================================
    # TIMESTAMP
    # =====================================================

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )


    # =====================================================
    # PASSWORD FUNCTIONS
    # =====================================================

    def set_password(self, password):

        self.password_hash = generate_password_hash(
            password
        )


    def check_password(self, password):

        return check_password_hash(
            self.password_hash,
            password
        )


    # =====================================================
    # REPRESENTATION
    # =====================================================

    def __repr__(self):

        return f"<User {self.email}>"