# create_tables.py

from app.db import Base, engine
import app.models  # import all models so they are registered with Base

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Tables created.")
