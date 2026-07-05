from pathlib import Path

from app.core.database import SessionLocal
from app.modules.manifest import load_catalog


def main() -> None:
    catalog_dir = Path(__file__).resolve().parent / "catalog"
    with SessionLocal() as db:
        result = load_catalog(db, catalog_dir)
        db.commit()
    print(f"Loaded catalog: {result}")


if __name__ == "__main__":
    main()
