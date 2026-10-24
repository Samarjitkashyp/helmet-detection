"""Create (or promote) an admin user.

Usage (from the backend folder):
    python -I scripts/create_admin.py                 # prompts for name, email, password
"""
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from core.security import hash_password  # noqa: E402
from db.database import Base, SessionLocal, engine  # noqa: E402
from db.models import User  # noqa: E402


def main():
    Base.metadata.create_all(engine)
    name = input("Admin name: ").strip()
    email = input("Admin email: ").strip().lower()
    password = getpass.getpass("Password (min 8 chars): ")
    if getpass.getpass("Repeat password: ") != password:
        sys.exit("Passwords do not match.")
    if len(password) < 8:
        sys.exit("Password too short.")
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        if user:
            user.role, user.is_active, user.password_hash = "admin", True, hash_password(password)
            print(f"Existing user {email} updated and promoted to admin.")
        else:
            db.add(User(name=name, email=email, password_hash=hash_password(password), role="admin"))
            print(f"Admin {email} created.")
        db.commit()


if __name__ == "__main__":
    main()
