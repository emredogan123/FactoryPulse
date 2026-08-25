from typing import Annotated

from fastapi import Depends

from app.auth.dependencies import require_roles
from app.models.user import User, UserRole


AdminUser = Annotated[
    User,
    Depends(
        require_roles(UserRole.ADMIN)
    ),
]

QualityUser = Annotated[
    User,
    Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.QUALITY_ENGINEER,
        )
    ),
]