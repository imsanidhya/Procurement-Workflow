from app import app
from models import db, User


with app.app_context():

    # =====================================================
    # USER 1
    # =====================================================

    user1 = User.query.filter_by(
        email="itsystem@jamipol.com"
    ).first()

    if user1:

        print("User 1 already exists.")

    else:

        user1 = User(
            employee_id="002",
            name="Sanidhya",
            email="itsystem@jamipol.com",
            department="IT",
            designation="Intern",
            role="EMPLOYEE",
            is_active=True
        )

        user1.set_password("Test@123")

        db.session.add(user1)

        print("User 1 created.")


    # =====================================================
    # USER 2
    # =====================================================

    user2 = User.query.filter_by(
        email="finance@jamipol.com"
    ).first()

    if user2:

        print("User 2 already exists.")

    else:

        user2 = User(
            employee_id="003",
            name="Rahul Sharma",
            email="finance@jamipol.com",
            department="Finance",
            designation="Executive",
            role="EMPLOYEE",
            is_active=True
        )

        user2.set_password("Test@123")

        db.session.add(user2)

        print("User 2 created.")


    # =====================================================
    # SAVE
    # =====================================================

    db.session.commit()


    print()
    print("======================================")
    print("TEST USERS")
    print("======================================")

    print()
    print("USER 1")
    print("Name       : Sanidhya")
    print("Email      : itsystem@jamipol.com")
    print("Employee ID: 002")
    print("Department : IT")
    print("Designation: Intern")
    print("Password   : Test@123")

    print()
    print("USER 2")
    print("Name       : Rahul Sharma")
    print("Email      : finance@jamipol.com")
    print("Employee ID: 003")
    print("Department : Finance")
    print("Designation: Executive")
    print("Password   : Test@123")

    print()
    print("======================================")