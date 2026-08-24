import argparse
from getpass import getpass

from pydantic import ValidationError

from app.auth.schemas import UserCreate
from app.auth.service import (
    UserAlreadyExistsError,
    create_user,
)
from app.db.session import SessionLocal
from app.models.user import UserRole


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create a FactoryPulse administrator"
        )
    )

    parser.add_argument(
        "--email",
        required=True,
        help="Administrator email address",
    )
    parser.add_argument(
        "--full-name",
        required=True,
        help="Administrator full name",
    )

    return parser


def read_password() -> str:
    password = getpass("Password: ")
    password_confirmation = getpass(
        "Confirm password: "
    )

    if password != password_confirmation:
        raise ValueError(
            "Passwords do not match"
        )

    return password


def main() -> None:
    arguments = build_parser().parse_args()

    try:
        password = read_password()

        user_data = UserCreate(
            email=arguments.email,
            full_name=arguments.full_name,
            password=password,
            role=UserRole.ADMIN,
        )
    except (ValidationError, ValueError) as error:
        print(f"Admin could not be created: {error}")
        return

    with SessionLocal() as db:
        try:
            user = create_user(
                db,
                user_data,
            )
            db.commit()
        except UserAlreadyExistsError as error:
            db.rollback()
            print(f"Admin could not be created: {error}")
            return
        except Exception:
            db.rollback()
            raise

    print("FactoryPulse administrator created")
    print(f"ID: {user.id}")
    print(f"Email: {user.email}")
    print(f"Role: {user.role.value}")


if __name__ == "__main__":
    main()