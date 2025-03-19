from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

# GET ALL DOCUMENTS
class Find:
    @staticmethod
    async def get_all_docs(collection, exclude_filter:dict):
        doc_cursor = collection.find()
        docs = await doc_cursor.to_list(length=None)
        return [{**doc, "_id": str(doc["_id"])} for doc in docs if not all(doc.get(k) == v for k, v in exclude_filter.items())]
    
# GET DOCUMENT BY NAME
    @staticmethod
    async def get_doc_by_name(name, collection,collection_type):
        doc = await collection.find_one({"name": name})
        if doc:
            doc["_id"] = str(doc["_id"])
            return doc
        raise HTTPException(status_code=404, detail=f"{collection_type}:{name} not found!")