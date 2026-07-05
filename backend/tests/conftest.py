from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.core.database import get_db
from app.core.security import hash_password
from app.main import app
from app.models import domain  # noqa: F401
from app.models.domain import Permission, Role, User


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
def auth_setup(db: Session) -> dict[str, User]:
    permission_names = [
        "patients.read",
        "patients.write",
        "appointments.read",
        "appointments.write",
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
        "ai.appointments.create",
    ]
    permissions = {name: Permission(name=name, description=name) for name in permission_names}
    admin_role = Role(name="admin", description="Admin", permissions=list(permissions.values()))
    limited_role = Role(name="limited", description="Limited", permissions=[permissions["inventory.read"], permissions["billing.read"]])
    admin = User(email="admin@test.local", full_name="Admin", password_hash=hash_password("secret"), role=admin_role)
    limited = User(email="limited@test.local", full_name="Limited", password_hash=hash_password("secret"), role=limited_role)
    db.add_all([*permissions.values(), admin_role, limited_role, admin, limited])
    db.flush()
    return {"admin": admin, "limited": limited}


def login_token(client: TestClient, email: str, password: str = "secret") -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]
