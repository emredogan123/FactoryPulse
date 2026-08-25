from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.auth.schemas import UserRead
from app.auth.service import get_users
from app.db.session import get_db
from app.models.user import User, UserRole


router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get(
    "",
    response_model=list[UserRead],
)
def read_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN)
    ),
) -> list[User]:
    return get_users(db)