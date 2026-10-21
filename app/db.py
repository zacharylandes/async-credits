from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from app.config import settings

client: MongoClient = MongoClient(settings.mongo_uri)
db: Database = client[settings.mongo_db]
credits_collection: Collection = db["credits"]
users_collection: Collection = db["users"]


def ensure_indexes() -> None:
    users_collection.create_index("user_id", unique=True)
