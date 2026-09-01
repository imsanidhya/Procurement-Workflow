import os

from dotenv import load_dotenv


load_dotenv()


class Config:

    # =========================================================
    # FLASK
    # =========================================================

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "dev-secret-key-change-later"
    )


    # =========================================================
    # DATABASE
    # =========================================================

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:password@localhost:5432/procurement_workflow"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False


    # =========================================================
    # FILE UPLOADS
    # =========================================================

    UPLOAD_FOLDER = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "uploads"
    )


    # =========================================================
    # MIS
    # =========================================================

    MIS_FOLDER = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "mis"
    )

    MIS_FILE = os.path.join(
        MIS_FOLDER,
        "Procurement_MIS.xlsx"
    )


    # =========================================================
    # GENERATED PDF
    # =========================================================

    PDF_FOLDER = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "generated_pdfs"
    )


   # =====================================================
    # EMAIL CONFIGURATION
    # =====================================================

    MAIL_SERVER = os.environ.get(
        "MAIL_SERVER",
        "smtp.office365.com"
    )

    MAIL_PORT = int(
        os.environ.get(
            "MAIL_PORT",
            587
        )
    )

    MAIL_USE_TLS = os.environ.get(
        "MAIL_USE_TLS",
        "true"
    ).lower() == "true"

    MAIL_USERNAME = os.environ.get(
        "MAIL_USERNAME"
    )

    MAIL_PASSWORD = os.environ.get(
        "MAIL_PASSWORD"
    )

    MAIL_DEFAULT_SENDER = os.environ.get(
        "MAIL_DEFAULT_SENDER",
        os.environ.get("MAIL_USERNAME")
    )