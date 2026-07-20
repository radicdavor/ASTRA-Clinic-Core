from collections.abc import Generator
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.core.database import get_db
from app.core.security import hash_password
from app.main import app
from app.models import domain  # noqa: F401
from app.models.domain import Clinic, ClinicMembership, Permission, Role, User


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    with SessionLocal() as session:
        yield session
    Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def pg_db() -> Generator[Session, None, None]:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        if os.getenv("ASTRA_REQUIRE_TEST_DATABASE", "").lower() in {"1", "true", "yes"}:
            pytest.fail("TEST_DATABASE_URL je obavezan za PostgreSQL pilot-readiness gate.")
        pytest.skip("TEST_DATABASE_URL nije postavljen; PostgreSQL integration testovi se preskacu lokalno.")
    engine = create_engine(database_url, pool_pre_ping=True)
    with engine.begin() as connection:
        table_names = ", ".join(f'"{table.name}"' for table in reversed(Base.metadata.sorted_tables))
        connection.execute(text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE"))
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    with SessionLocal() as session:
        yield session


@pytest.fixture()
def pg_client(pg_db: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield pg_db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_setup(db: Session) -> dict[str, User]:
    permission_names = [
        "patients.read",
        "patients.write",
        "appointments.read",
        "appointments.write",
        "appointments.patient_availability.read",
        "episodes.read",
        "episodes.write",
        "clinical_plans.read",
        "clinical_plans.write",
        "clinical_documents.read",
        "clinical_documents.write",
        "clinical_documents.review",
        "services.read",
        "services.write",
        "inventory.read",
        "inventory.write",
        "inventory.adjust",
        "inventory.write_off",
        "inventory.transfer",
        "procurement.read",
        "procurement.write",
        "billing.read",
        "billing.write",
        "billing.mark_paid",
        "audit.read",
        "admin.manage_users",
        "clinical_readiness.snapshots.read",
        "clinical_readiness.snapshots.write",
        "clinical_readiness.snapshots.supersede",
        "clinical_readiness.acknowledgments.read",
        "clinical_findings.read",
        "clinical_open_questions.read",
        "clinical_evidence_timeline.read",
        "workflow_tasks.read",
        "workflow_tasks.write",
        "workflow_templates.manage",
        "knowledge_protocols.read",
        "knowledge_protocols.write",
        "knowledge_protocols.review",
        "ai.appointments.create",
        "journey.read",
        "journey.create",
        "journey.transition",
        "preparation.assign",
        "preparation.review",
        "documents.request",
        "documents.upload",
        "documents.scan",
        "documents.view_source",
        "documents.review",
        "summary.generate",
        "summary.review",
        "checkin.update",
        "checkin.clinical_review",
        "encounter.read",
        "encounter.write",
        "encounter.complete",
        "consumables.record",
        "payment.record",
        "clinical_forms.read",
        "clinical_forms.manage",
        "clinical_forms.sign",
        "service_packages.read",
        "service_packages.schedule",
        "service_packages.manage",
        "activity_preparation.read",
        "activity_preparation.update",
        "activity_preparation.clinical_review",
        "procedure_interventions.read",
        "procedure_interventions.write",
        "pathology_cases.read",
        "pathology_cases.update",
        "pathology_results.receive",
        "pathology_results.review",
        "pathology_communication.decide",
        "reports.read",
        "reports.print",
        "reports.send",
        "reports.send_alternate_recipient",
        "reports.delivery_history",
        "system.admin",
    ]
    permissions = {name: Permission(name=name, description=name) for name in permission_names}
    admin_role = Role(name="admin", description="Admin", permissions=list(permissions.values()))
    limited_role = Role(name="limited", description="Limited", permissions=[permissions["inventory.read"], permissions["billing.read"]])
    admin = User(email="admin@test.local", full_name="Admin", password_hash=hash_password("secret"), role=admin_role)
    limited = User(email="limited@test.local", full_name="Limited", password_hash=hash_password("secret"), role=limited_role)
    demo_clinic = Clinic(name="Test Clinic")
    db.add_all([*permissions.values(), admin_role, limited_role, admin, limited, demo_clinic])
    db.flush()
    db.add(ClinicMembership(user_id=admin.id, clinic_id=demo_clinic.id, created_by_user_id=admin.id))
    db.flush()
    return {"admin": admin, "limited": limited, "clinic": demo_clinic}


def login_token(client: TestClient, email: str, password: str = "secret") -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]
