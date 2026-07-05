from sqlalchemy.orm import Session

from app.models.domain import AuditLog


def audit(db: Session, action: str, entity_type: str, entity_id: int | None = None, summary: str | None = None, actor_user_id: int | None = None) -> None:
    db.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            summary=summary,
        )
    )
