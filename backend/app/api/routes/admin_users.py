from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.api.routes.auth import get_auth_service
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import UserAdminUpdate, UserRead
from app.services.auth_service import AuthService, ForbiddenSelfChange, UserNotFound

router = APIRouter()


@router.get("", response_model=list[UserRead])
def list_users(_: User = Depends(require_admin), service: AuthService = Depends(get_auth_service)) -> list[User]:
    return service.list_users()


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    changes: UserAdminUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
    service: AuthService = Depends(get_auth_service),
) -> User:
    try:
        user = service.update_user(admin, user_id, changes)
    except UserNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.") from None
    except ForbiddenSelfChange:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Un administrador no puede modificar su propia cuenta."
        ) from None
    db.commit()
    return user
