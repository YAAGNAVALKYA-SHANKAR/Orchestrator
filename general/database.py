from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING
import os

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")
CAT_COLLECTION_NAME = os.getenv("CAT_COLLECTION_NAME")
SUB_CAT_COLLECTION_NAME = os.getenv("SUB_CAT_COLLECTION_NAME")
LOGS_COLLECTION_NAME = os.getenv("LOGS_COLLECTION_NAME")
ATTRIBUTES_COLLECTION_NAME= os.getenv("ATTRIBUTES_COLLECTION_NAME")

# Initialize MongoDB client
client = AsyncIOMotorClient(MONGO_URI)
db = client[DATABASE_NAME]

# Collection references
categories = db[CAT_COLLECTION_NAME]
sub_categories = db[SUB_CAT_COLLECTION_NAME]
logs = db[LOGS_COLLECTION_NAME]
attributes=db[ATTRIBUTES_COLLECTION_NAME]

async def init_db():
    print("Initializing database...")
    existing_collections = await db.list_collection_names()

    # Create collections if they don't exist
    if CAT_COLLECTION_NAME not in existing_collections:
        await db.create_collection(CAT_COLLECTION_NAME)
        await db[CAT_COLLECTION_NAME].insert_one({"function": "ID_counter", "count": 1})
        print("Category collection created!")

    if SUB_CAT_COLLECTION_NAME not in existing_collections:
        await db.create_collection(SUB_CAT_COLLECTION_NAME)
        await db[SUB_CAT_COLLECTION_NAME].insert_one({"function": "ID_counter", "count": 1})
        print("Subcategory collection created!")

    if ATTRIBUTES_COLLECTION_NAME not in existing_collections:
        await db.create_collection(ATTRIBUTES_COLLECTION_NAME)
        await db[ATTRIBUTES_COLLECTION_NAME].insert_one({"function": "ID_counter", "count": 1})
        print("Attributes collection created!")

    if LOGS_COLLECTION_NAME not in existing_collections:
        await db.create_collection(LOGS_COLLECTION_NAME)
        print("Logs collection created!")

    # Ensure indexes are created
    await categories.create_index([("name", ASCENDING)], unique=True)
    await sub_categories.create_index([("subcategory_id", ASCENDING)], unique=True)
    await logs.create_index([("event", ASCENDING)])
    await attributes.create_index([("name", ASCENDING)], unique=True)

    print("Database initialized successfully!")