"""Environment-configured MongoDB connection and auditable operations."""
import os
from datetime import datetime, timezone
from pymongo import MongoClient

def connect():
    client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:28117'), serverSelectionTimeoutMS=10000)
    client.admin.command('ping')
    return client[os.getenv('MONGODB_DATABASE', 'smart_library')]

def audit(db, action, collection, detail):
    db.audit_logs.insert_one(dict(at=datetime.now(timezone.utc), actor=os.getenv('LIBRARY_ACTOR','operator'), action=action, collection=collection, detail=detail))
