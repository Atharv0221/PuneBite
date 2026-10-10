"""MongoDB connection for PuneBite Analyzer.
 
Reads MONGO_URI and DB_NAME from the .env file in the project root.
Local:  MONGO_URI=mongodb://127.0.0.1:27017
Atlas:  MONGO_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
(see docs/ATLAS_SETUP.md)
"""
import os
from pathlib import Path
 
from dotenv import load_dotenv
from pymongo import MongoClient
 
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
 
MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
DB_NAME = os.getenv("DB_NAME", "punebite")
 
_client = None
 
 
def get_db():
    """Return the database object (one shared client per process)."""
    global _client
    if _client is None:
        kwargs = {"serverSelectionTimeoutMS": 8000}
        if MONGO_URI.startswith("mongodb+srv://") or ".mongodb.net" in MONGO_URI:
            import certifi                      # Atlas needs TLS; certifi gives a CA bundle that works on Windows too
            kwargs["tlsCAFile"] = certifi.where()
        _client = MongoClient(MONGO_URI, **kwargs)
    return _client[DB_NAME]
 



def describe_target():
    """Host only (never the password) - safe to print."""
    host = MONGO_URI.split("://", 1)[-1].split("@")[-1].split("/")[0].split("?")[0]
    return f"{host} / db '{DB_NAME}'"
