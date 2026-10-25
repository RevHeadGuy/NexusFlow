from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.auth import ProjectInvitation, ProjectMembership, User
from app.schemas.auth import InviteCreate, InvitationRead, MemberRead
from app.services.auth_service import create_invitation

router = APIRouter(prefix="/projects", tags=["project collaboration"])


class MemberRoleUpdate(BaseModel):
    role: str = Field(pattern="^(editor|reviewer|viewer)$")


@router.get("/{project_id}/members", response_model=list[MemberRead])
def list_members(project_id: str, db: Session = Depends(get_db)) -> list[MemberRead]:
    rows = db.execute(
        select(ProjectMembership, User)
        .join(User, User.id == ProjectMembership.user_id)
        .where(ProjectMembership.project_id == project_id)
        .order_by(ProjectMembership.created_at)
    ).all()
    return [
        MemberRead(
            user_id=membership.user_id,
            email=user.email,
            display_name=user.display_name,
            role=membership.role,
            created_at=membership.created_at,
        )
        for membership, user in rows
    ]


@router.post("/{project_id}/invitations", response_model=InvitationRead, status_code=201)
def invite_member(project_id: str, payload: InviteCreate, request: Request, db: Session = Depends(get_db)) -> InvitationRead:
    if request.state.user.email.lower() == payload.email.lower():
        raise HTTPException(status_code=400, detail="You are already a project member.")
    invitation, raw_token = create_invitation(
        db,
        project_id=project_id,
        email=payload.email,
        role=payload.role,
        invited_by_user_id=request.state.user.id,
    )
    return InvitationRead(
        id=invitation.id,
        project_id=invitation.project_id,
        email=invitation.email,
        role=invitation.role,
        expires_at=invitation.expires_at,
        invite_token=raw_token,
    )


@router.get("/{project_id}/invitations", response_model=list[InvitationRead])
def list_invitations(project_id: str, db: Session = Depends(get_db)) -> list[InvitationRead]:
    now = datetime.now(timezone.utc)
    invitations = db.scalars(
        select(ProjectInvitation)
        .where(
            ProjectInvitation.project_id == project_id,
            ProjectInvitation.accepted_at.is_(None),
            ProjectInvitation.expires_at > now,
        )
        .order_by(ProjectInvitation.created_at.desc())
    ).all()
    return [
        InvitationRead(
            id=item.id,
            project_id=item.project_id,
            email=item.email,
            role=item.role,
            expires_at=item.expires_at,
        )
        for item in invitations
    ]


@router.delete("/{project_id}/invitations/{invitation_id}", status_code=204)
def revoke_invitation(project_id: str, invitation_id: str, db: Session = Depends(get_db)) -> None:
    invitation = db.scalar(
        select(ProjectInvitation).where(
            ProjectInvitation.project_id == project_id,
            ProjectInvitation.id == invitation_id,
        )
    )
    if invitation is None or invitation.accepted_at is not None:
        raise HTTPException(status_code=404, detail="Pending invitation not found.")
    db.delete(invitation)
    db.commit()


@router.patch("/{project_id}/members/{user_id}", response_model=MemberRead)
def update_member_role(
    project_id: str,
    user_id: str,
    payload: MemberRoleUpdate,
    db: Session = Depends(get_db),
) -> MemberRead:
    membership = db.scalar(
        select(ProjectMembership).where(
            ProjectMembership.project_id == project_id,
            ProjectMembership.user_id == user_id,
        )
    )
    if membership is None:
        raise HTTPException(status_code=404, detail="Project member not found.")
    if membership.role == "owner":
        raise HTTPException(status_code=400, detail="Transfer ownership before changing an owner's role.")
    user = db.get(User, user_id)
    membership.role = payload.role
    db.commit()
    db.refresh(membership)
    return MemberRead(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=membership.role,
        created_at=membership.created_at,
    )


@router.delete("/{project_id}/members/{user_id}", status_code=204)
def remove_member(project_id: str, user_id: str, db: Session = Depends(get_db)) -> None:
    membership = db.scalar(
        select(ProjectMembership).where(
            ProjectMembership.project_id == project_id,
            ProjectMembership.user_id == user_id,
        )
    )
    if membership is None:
        raise HTTPException(status_code=404, detail="Project member not found.")
    if membership.role == "owner":
        owner_count = db.scalar(
            select(func.count()).select_from(ProjectMembership).where(
                ProjectMembership.project_id == project_id,
                ProjectMembership.role == "owner",
            )
        )
        if owner_count <= 1:
            raise HTTPException(status_code=400, detail="A project must keep at least one owner.")
    db.delete(membership)
    db.commit()


@router.post("/{project_id}/members/{user_id}/transfer-ownership", response_model=MemberRead)
def transfer_ownership(
    project_id: str,
    user_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> MemberRead:
    current_owner = db.scalar(
        select(ProjectMembership).where(
            ProjectMembership.project_id == project_id,
            ProjectMembership.user_id == request.state.user.id,
            ProjectMembership.role == "owner",
        )
    )
    target = db.scalar(
        select(ProjectMembership).where(
            ProjectMembership.project_id == project_id,
            ProjectMembership.user_id == user_id,
        )
    )
    if current_owner is None or target is None:
        raise HTTPException(status_code=404, detail="Project owner or target member not found.")
    if user_id == request.state.user.id:
        raise HTTPException(status_code=400, detail="Choose another project member as the new owner.")
    current_owner.role = "editor"
    target.role = "owner"
    db.commit()
    db.refresh(target)
    user = db.get(User, user_id)
    return MemberRead(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=target.role,
        created_at=target.created_at,
    )
