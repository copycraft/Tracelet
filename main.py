import sys
import multiprocessing
import uvicorn
from sqlalchemy import create_engine, text

from app.settings import get_database_url


def check_db():
    try:
        engine = create_engine(get_database_url())
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print("\n" + "#" * 80)
        print("\033[91m")
        print("DATABASE ISN'T RUNNING!".center(80))
        print("\033[0m")
        print("#" * 80 + "\n")
        print("Full error:", e, "\n")
        print("Run the database initialization script: init_db.ps1\n")
        sys.exit(1)


def start_tracelet():
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )


def start_websql():
    uvicorn.run(
        "websql.main:app",
        host="0.0.0.0",
        port=8076,
        reload=False,
    )


if __name__ == "__main__":
    check_db()

    print("Database OK. Starting Tracelet + WebSQL...\n")

    p1 = multiprocessing.Process(target=start_tracelet)
    p2 = multiprocessing.Process(target=start_websql)

    p1.start()
    p2.start()

    p1.join()
    p2.join()
