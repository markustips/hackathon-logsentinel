"""Initialize the database - creates all tables."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import create_db_and_tables
from config import get_settings

if __name__ == "__main__":
    print("Initializing LogSentinel AI database...")

    settings = get_settings()
    print(f"Database URL: {settings.database_url}")

    create_db_and_tables()

    print("✅ Database initialized successfully!")
    print("\nTables created:")
    print("  - log_files")
    print("  - log_records")
    print("  - anomalies")
    print("\nYou can now start the server:")
    print("  uvicorn main:app --reload --port 8000")
