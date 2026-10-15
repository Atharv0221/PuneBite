"""MongoDB connection for PuneBite Analyzer.

Reads MONGO_URI and DB_NAME from the .env file in the project root (see .env.example).
Local:  MONGO_URI=mongodb://127.0.0.1:27017
Atlas:  MONGO_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
(see docs/ATLAS_SETUP.md)
"""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017").strip()
DB_NAME = os.getenv("DB_NAME", "punebite").strip()

_client = None


def is_atlas():
    return MONGO_URI.startswith("mongodb+srv://") or ".mongodb.net" in MONGO_URI


def get_db():
    """Return the database object (one shared client per process)."""
    global _client
    if _client is None:
        # Imported here so that scripts which never touch the database
        # (load_data.py --dry-run, unit tests) work without pymongo installed.
        from pymongo import MongoClient

        kwargs = {"serverSelectionTimeoutMS": 8000}
        if is_atlas():
            import certifi  # Atlas needs TLS; certifi gives a CA bundle that also works on Windows

            kwargs["tlsCAFile"] = certifi.where()
        _client = MongoClient(MONGO_URI, **kwargs)
    return _client[DB_NAME]


def describe_target():
    """Host only (never the password) - safe to print."""
    host = MONGO_URI.split("://", 1)[-1].split("@")[-1].split("/")[0].split("?")[0]
    return f"{host} / db '{DB_NAME}'"


def database_label():
    """Short, non-sensitive label shown in the website header."""
    return "MongoDB Atlas" if is_atlas() else "MongoDB (local)"
