from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Establishment, User
from app.schemas import LoginIn, RegisterIn, TokenOut, UserOut
from app.security import ADMIN, create_access_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def ensure_email_available(db: Session, email: str, ignore_user_id: int | None = None) -> None:
    query = select(User.id).where(func.lower(User.email) == email.lower())
    if ignore_user_id is not None:
        query = query.where(User.id != ignore_user_id)
    if db.scalar(query) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe um usuário com este e-mail.")


def token_for(user: User) -> TokenOut:
    return TokenOut(access_token=create_access_token(user), user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)) -> TokenOut:
    user = db.scalar(select(User).where(func.lower(User.email) == data.email.lower()))
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-mail ou senha inválidos.")
    if not user.active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Usuário desativado. Procure o administrador.")
    return token_for(user)


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register_establishment(data: RegisterIn, db: Session = Depends(get_db)) -> TokenOut:
    """Cadastra um novo estabelecimento e o seu primeiro administrador."""

    ensure_email_available(db, data.email)
    establishment = Establishment(name=data.establishment_name, depot_address=data.depot_address)
    user = User(
        establishment=establishment,
        full_name=data.full_name,
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        role=ADMIN,
    )
    db.add(user)
    db.commit()
    return token_for(user)


@router.get("/me", response_model=UserOut)
def current_user(user: User = Depends(get_current_user)) -> User:
    return user
