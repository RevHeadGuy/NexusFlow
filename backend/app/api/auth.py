from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.auth import ProjectMembership, User
from app.models.project import Project
from app.schemas.auth import InviteAccept, LoginRequest, RegisterRequest, TokenRead, UserRead
from app.services.auth_service import create_access_token, get_user_by_email, register_user, verify_password

router = APIRouter(prefix="/auth", tags=["authentication"])


def serialize_user(user: User) -> UserRead:
    return UserRead(id=user.id, email=user.email, display_name=user.display_name, created_at=user.created_at)


@router.post("/register", response_model=TokenRead, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenRead:
    if get_user_by_email(db, payload.email):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    is_first_user = db.scalar(select(func.count()).select_from(User)) == 0
    try:
        user = register_user(db, email=payload.email, display_name=payload.display_name, password=payload.password)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists.") from exc

    # Existing local-first installations have projects without owners. The first account
    # claims those legacy projects so local data remains usable after upgrading.
    if is_first_user:
        projects = db.scalars(select(Project)).all()
        for project in projects:
            db.add(ProjectMembership(project_id=project.id, user_id=user.id, role="owner"))
        db.commit()

    token, expires_in = create_access_token(user)
    return TokenRead(access_token=token, expires_in=expires_in, user=serialize_user(user))


@router.post("/login", response_model=TokenRead)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenRead:
    user = get_user_by_email(db, payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")
    token, expires_in = create_access_token(user)
    return TokenRead(access_token=token, expires_in=expires_in, user=serialize_user(user))


@router.get("/me", response_model=UserRead)
def me(request: Request) -> UserRead:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=401, detail="Sign in to access NexusFlow.")
    return serialize_user(user)


@router.post("/invitations/accept")
def accept_invitation(payload: InviteAccept, request: Request, db: Session = Depends(get_db)) -> dict:
    from app.services.auth_service import accept_invitation, find_invitation

    user = request.state.user
    invitation = find_invitation(db, payload.token)
    if invitation is None or invitation.accepted_at is not None:
        raise HTTPException(status_code=404, detail="Invitation is invalid or has already been used.")
    expires_at = invitation.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Invitation has expired.")
    if invitation.email.lower() != user.email.lower():
        raise HTTPException(status_code=403, detail="Sign in with the invited email address to accept this invitation.")
    membership = accept_invitation(db, invitation, user)
    return {"project_id": membership.project_id, "role": membership.role, "status": "accepted"}
