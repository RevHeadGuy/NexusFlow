from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.artifact import ArtifactCreate, ArtifactRead, ArtifactVersionCreate, ArtifactVersionRead
from app.services.artifact_service import create_artifact, create_artifact_version, export_artifact_zip, export_project_package, get_artifact_for_project, get_versions, list_artifacts
from app.services.project_service import get_project

router = APIRouter(prefix="/projects", tags=["artifacts"])


@router.get("/{project_id}/package/export")
def export_project_artifact_package(project_id: str, db: Session = Depends(get_db)) -> Response:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    payload = export_project_package(db, project_id)
    return Response(
        content=payload,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="nexusflow-project-package.zip"'},
    )


@router.post("/{project_id}/artifacts", response_model=ArtifactRead, status_code=status.HTTP_201_CREATED)
def create_project_artifact(project_id: str, payload: ArtifactCreate, db: Session = Depends(get_db)) -> ArtifactRead:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    artifact = create_artifact(db, project_id, payload.name, payload.type, payload.content)
    return ArtifactRead(
        id=artifact.id,
        project_id=artifact.project_id,
        name=artifact.name,
        type=artifact.type,
        content=artifact.content,
        current_version=artifact.current_version,
        created_at=artifact.created_at,
        updated_at=artifact.updated_at,
    )


@router.get("/{project_id}/artifacts", response_model=list[ArtifactRead])
def read_project_artifacts(project_id: str, db: Session = Depends(get_db)) -> list[ArtifactRead]:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    artifacts = list_artifacts(db, project_id)
    return [
        ArtifactRead(
            id=artifact.id,
            project_id=artifact.project_id,
            name=artifact.name,
            type=artifact.type,
            content=artifact.content,
            current_version=artifact.current_version,
            created_at=artifact.created_at,
            updated_at=artifact.updated_at,
        )
        for artifact in artifacts
    ]


@router.get("/{project_id}/artifacts/{artifact_id}", response_model=ArtifactRead)
def read_project_artifact(project_id: str, artifact_id: str, db: Session = Depends(get_db)) -> ArtifactRead:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    artifact = get_artifact_for_project(db, project_id, artifact_id)
    if artifact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")

    return ArtifactRead(
        id=artifact.id,
        project_id=artifact.project_id,
        name=artifact.name,
        type=artifact.type,
        content=artifact.content,
        current_version=artifact.current_version,
        created_at=artifact.created_at,
        updated_at=artifact.updated_at,
    )


@router.post("/{project_id}/artifacts/{artifact_id}/versions", response_model=ArtifactVersionRead, status_code=status.HTTP_201_CREATED)
def create_artifact_revision(project_id: str, artifact_id: str, payload: ArtifactVersionCreate, db: Session = Depends(get_db)) -> ArtifactVersionRead:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    artifact = get_artifact_for_project(db, project_id, artifact_id)
    if artifact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")

    version = create_artifact_version(db, artifact.id, payload.content, payload.summary)
    return ArtifactVersionRead(
        id=version.id,
        artifact_id=version.artifact_id,
        project_id=version.project_id,
        version=version.version,
        content=version.content,
        summary=version.summary,
        created_at=version.created_at,
    )


@router.get("/{project_id}/artifacts/{artifact_id}/versions", response_model=list[ArtifactVersionRead])
def read_artifact_versions(project_id: str, artifact_id: str, db: Session = Depends(get_db)) -> list[ArtifactVersionRead]:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    artifact = get_artifact_for_project(db, project_id, artifact_id)
    if artifact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")

    versions = get_versions(db, artifact.id)
    return [
        ArtifactVersionRead(
            id=version.id,
            artifact_id=version.artifact_id,
            project_id=version.project_id,
            version=version.version,
            content=version.content,
            summary=version.summary,
            created_at=version.created_at,
        )
        for version in versions
    ]


@router.get("/{project_id}/artifacts/{artifact_id}/export")
def export_artifact(project_id: str, artifact_id: str, db: Session = Depends(get_db)) -> Response:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    artifact = get_artifact_for_project(db, project_id, artifact_id)
    if artifact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")

    payload = export_artifact_zip(db, artifact.id)
    filename = f"{artifact.name}.zip"
    return Response(content=payload, media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="{filename}"'})
