from app.core.database import SessionLocal
from app.services.seed import seed


def main() -> None:
    with SessionLocal() as db:
        seed(db)


if __name__ == "__main__":
    main()
