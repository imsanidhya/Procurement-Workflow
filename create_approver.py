from app import app
from models import db, User


with app.app_context():

    # =========================================================
    # APPROVER 1
    # =========================================================

    approver1_email = "approver@jamipol.com"

    existing_user = User.query.filter_by(
        email=approver1_email
    ).first()

    if existing_user:

        print("Approver 1 already exists.")

    else:

        approver1 = User(

            employee_id="004",

            name="Test Approver",

            email=approver1_email,

            department="Finance",

            designation="Manager",

            role="APPROVER",

            is_active=True

        )

        approver1.set_password(
            "Test@123"
        )

        db.session.add(
            approver1
        )

        print("Approver 1 created successfully.")


    # =========================================================
    # APPROVER 2
    # =========================================================

    approver2_email = "approver2@jamipol.com"

    existing_user = User.query.filter_by(
        email=approver2_email
    ).first()

    if existing_user:

        print("Approver 2 already exists.")

    else:

        approver2 = User(

            employee_id="005",

            name="Test Approver 2",

            email=approver2_email,

            department="Finance",

            designation="Senior Manager",

            role="APPROVER",

            is_active=True

        )

        approver2.set_password(
            "Test@123"
        )

        db.session.add(
            approver2
        )

        print("Approver 2 created successfully.")


    # =========================================================
    # APPROVER 3 - ABHAY
    # =========================================================

    approver3_email = "abhay@jamipol.com"

    existing_user = User.query.filter_by(
        email=approver3_email
    ).first()

    if existing_user:

        print("Approver 3 (Abhay) already exists.")

    else:

        approver3 = User(

            employee_id="006",

            name="Abhay",

            email=approver3_email,

            department="Finance",

            designation="Manager",

            role="APPROVER",

            is_active=True

        )

        approver3.set_password(
            "Abhay@123"
        )

        db.session.add(
            approver3
        )

        print("Approver 3 (Abhay) created successfully.")


    # =========================================================
    # APPROVER 4 - SHASHI
    # =========================================================

    approver4_email = "shashi@jamipol.com"

    existing_user = User.query.filter_by(
        email=approver4_email
    ).first()

    if existing_user:

        print("Approver 4 (Shashi) already exists.")

    else:

        approver4 = User(

            employee_id="007",

            name="Shashi",

            email=approver4_email,

            department="Finance",

            designation="Senior Manager",

            role="APPROVER",

            is_active=True

        )

        approver4.set_password(
            "Shashi@123"
        )

        db.session.add(
            approver4
        )

        print("Approver 4 (Shashi) created successfully.")


    # =========================================================
    # SAVE ALL USERS
    # =========================================================

    db.session.commit()


    # =========================================================
    # LOGIN DETAILS
    # =========================================================

    print("")
    print("========================================")
    print("APPROVER TEST ACCOUNTS")
    print("========================================")

    print("")
    print("Approver 1")
    print("Name: Test Approver")
    print("Email: approver@jamipol.com")
    print("Password: Test@123")

    print("")
    print("Approver 2")
    print("Name: Test Approver 2")
    print("Email: approver2@jamipol.com")
    print("Password: Test@123")

    print("")
    print("Approver 3")
    print("Name: Abhay")
    print("Email: abhay@jamipol.com")
    print("Password: Abhay@123")

    print("")
    print("Approver 4")
    print("Name: Shashi")
    print("Email: shashi@jamipol.com")
    print("Password: Shashi@123")

    print("")
    print("========================================")
    print("All approver accounts are ready.")
    print("========================================")
