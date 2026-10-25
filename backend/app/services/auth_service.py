from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.auth import ProjectInvitation, ProjectMembership, User

PASSWORD_ITERATIONS = 310_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PASSWORD_ITERATIONS)
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt.hex()}${derived.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = encoded.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations))
        return hmac.compare_digest(candidate.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def create_access_token(user: User) -> tuple[str, int]:
    settings = get_settings()
    expires_in = settings.auth_token_expire_minutes * 60
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {"sub": user.id, "iat": now, "exp": now + timedelta(seconds=expires_in)},
        settings.auth_secret_key,
        algorithm="HS256",
    )
    return token, expires_in


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, get_settings().auth_secret_key, algorithms=["HS256"])
        subject = payload.get("sub")
        return subject if isinstance(subject, str) else None
    except jwt.PyJWTError:
        return None


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def list_user_project_ids(db: Session, user_id: str) -> list[str]:
    return list(db.scalars(select(ProjectMembership.project_id).where(ProjectMembership.user_id == user_id)).all())


def register_user(db: Session, *, email: str, display_name: str, password: str) -> User:
    user = User(email=email.lower(), display_name=display_name.strip(), password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_invitation(
    db: Session,
    *,
    project_id: str,
    email: str,
    role: str,
    invited_by_user_id: str,
) -> tuple[ProjectInvitation, str]:
    token = secrets.token_urlsafe(36)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    invitation = ProjectInvitation(
        project_id=project_id,
        email=email.lower(),
        role=role,
        token_hash=token_hash,
        invited_by_user_id=invited_by_user_id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation, token


def find_invitation(db: Session, token: str) -> ProjectInvitation | None:
    digest = hashlib.sha256(token.encode()).hexdigest()
    return db.scalar(select(ProjectInvitation).where(ProjectInvitation.token_hash == digest))


def accept_invitation(db: Session, invitation: ProjectInvitation, user: User) -> ProjectMembership:
    membership = db.scalar(
        select(ProjectMembership).where(
            ProjectMembership.project_id == invitation.project_id,
            ProjectMembership.user_id == user.id,
        )
    )
    if membership is None:
        membership = ProjectMembership(project_id=invitation.project_id, user_id=user.id, role=invitation.role)
        db.add(membership)
    invitation.accepted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(membership)
    return membership
