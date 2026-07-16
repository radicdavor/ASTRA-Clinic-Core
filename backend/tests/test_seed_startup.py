from app.models.domain import Clinic
from app.services.seed import seed


def test_seed_reuses_clinics_created_by_migrations(db):
    db.add_all([Clinic(name="Gastroenterologija"), Clinic(name="Estetika")])
    db.commit()

    seed(db)

    assert db.query(Clinic).filter(Clinic.name == "Gastroenterologija").count() == 1
    assert db.query(Clinic).filter(Clinic.name == "Estetika").count() == 1
