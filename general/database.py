import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING
load_dotenv()
MONGO_URI=os.getenv("MONGO_URI")
DATABASE_NAME=os.getenv("DATABASE_NAME")
CAT_COLLECTION_NAME=os.getenv("CAT_COLLECTION_NAME")
SUB_CAT_COLLECTION_NAME=os.getenv("SUB_CAT_COLLECTION_NAME")
ATTRIBUTES_COLLECTION_NAME=os.getenv("ATTRIBUTES_COLLECTION_NAME")
ENTITY_COLLECTION_NAME=os.getenv("ENTITY_COLLECTION_NAME")
client=AsyncIOMotorClient(MONGO_URI)
db=client[DATABASE_NAME]
categories=db[CAT_COLLECTION_NAME]
sub_categories=db[SUB_CAT_COLLECTION_NAME]
attributes=db[ATTRIBUTES_COLLECTION_NAME]
entities=db[ENTITY_COLLECTION_NAME]
async def init_db():
    UPLOAD_DIR="uploaded_files"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    existing_collections=await db.list_collection_names()
    async def create_collection_with_counter(collection_name):
        if collection_name not in existing_collections:
            await db.create_collection(collection_name)
            await db[collection_name].insert_one([{"function":"ID_counter","count":1}])
    await create_collection_with_counter(CAT_COLLECTION_NAME)
    await create_collection_with_counter(SUB_CAT_COLLECTION_NAME)
    await create_collection_with_counter(ATTRIBUTES_COLLECTION_NAME)
    await create_collection_with_counter(ENTITY_COLLECTION_NAME)
    await categories.create_index([("category_name",ASCENDING)],unique=True)
    await sub_categories.create_index([("sub_category_name",ASCENDING)],unique=True)
    await attributes.create_index([("attribute_name",ASCENDING)],unique=True)
    await entities.create_index([("entity_name",ASCENDING)],unique=True)