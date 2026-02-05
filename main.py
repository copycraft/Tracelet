import sys
import uvicorn
from sqlalchemy import create_engine, text
from app.settings import get_database_url

def check_db():
    """Check if the database is reachable."""
    try:
        engine = create_engine(get_database_url())
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print("\n" + "#"*80)
        print("\033[91m")  # Red text
        print("DATABASE ISN'T RUNNING!".center(80))
        print("\033[0m")   # Reset color
        print("#"*80 + "\n")
        print("Full error:", e, "\n")
        print("Run the database initialization script: init_db.ps1\n")
        sys.exit(1)

if __name__ == "__main__":
    check_db()

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
