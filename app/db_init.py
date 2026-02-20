from pathlib import Path
import sqlite3

# Paths
APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "lmt_defence.db"
SCHEMA_PATH = APP_DIR.parent / "schema.sql"
if not SCHEMA_PATH.exists():
    SCHEMA_PATH = APP_DIR / "schema.sql"


def init_database() -> None:
    
    #Initialize database from schema.sql if it doesn't exist.
    
    if DB_PATH.exists():
        # Database already exists, skip initialization
        return

    # Read schema.sql
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Schema file not found: {SCHEMA_PATH}. "
            "Please ensure schema.sql is in the project root."
        )

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    # Create database and execute schema
    conn = sqlite3.connect(DB_PATH)
    try:
        # Split by semicolons and execute each statement
        # Filter out empty statements and comments
        statements = [
            stmt.strip()
            for stmt in schema_sql.split(";")
            if stmt.strip() and not stmt.strip().startswith("--")
        ]

        for statement in statements:
            if statement:
                conn.execute(statement)

        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    # Allow running this script directly to initialize DB
    init_database()
    print(f"Database initialized at {DB_PATH}")
