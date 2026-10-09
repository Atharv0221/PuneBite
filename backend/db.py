"""MongoDB connection for PuneBite Analyzer.
 
Reads MONGO_URI and DB_NAME from the .env file in the project root.
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
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return _client[DB_NAME]
 

