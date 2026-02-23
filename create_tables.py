# create_tables.py

import sys
from sqlalchemy.exc import SQLAlchemyError
from app.db import Base, engine
import app.models  # make sure all your models are imported so they register with Base

def main():
    try:
        print("\nCreating tables...\n")
        Base.metadata.create_all(bind=engine)
        print("\n✅ Tables created successfully!\n")
    except SQLAlchemyError as e:
        print("\n❌ Failed to create tables!\n")
        print("Error:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()