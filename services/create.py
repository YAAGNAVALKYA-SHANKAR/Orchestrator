from fastapi import HTTPException
from services.logs import DBChangeCapture
from pymongo.errors import DuplicateKeyError

class Create:
# ADD DATA
    @staticmethod
    async def create(data, created_by, collection, collection_type, prefix):
        dict = data.model_dump()
        counter_doc = await collection.find_one({"function": "ID_counter"})
        counter_value = counter_doc["count"] if counter_doc else 0
        dict["id"] = f"{prefix}_{counter_value:04d}"
        await collection.update_one({"function": "ID_counter"},{"$inc": {"count": 1}})    
        existing_doc = await collection.find_one({"name": dict["name"]})
        name=dict["name"]
        if existing_doc:            
            raise HTTPException(status_code=400, detail=f"{collection_type} {name} already exists!")        
        try:
            result = await collection.insert_one(dict)
            inserted_doc = await collection.find_one({"_id": result.inserted_id})
            if inserted_doc:
                inserted_doc["_id"] = str(inserted_doc["_id"])
                await DBChangeCapture.log_change(f"{collection_type} {name} Created", {
                    "name": dict["name"],
                    "created_by": created_by
                })
            return inserted_doc
        except DuplicateKeyError:
            raise HTTPException(status_code=400, detail=f"{collection_type} must be unique!")