from fastapi import HTTPException
from services.logs import DBChangeCapture

class Update:

# UPDATE DATA
    @staticmethod
    async def update(name, updated_by, data, collection, collection_type):
        existing_doc = await collection.find_one({"name": name})
        if not existing_doc:
            raise HTTPException(status_code=404, detail=f"{collection_type} {name} not found!")        
        modified_fields = {}
        for key, value in data.items():
            if key in existing_doc and existing_doc[key] != value:
                modified_fields[key] = {"old_value": existing_doc[key], "new_value": value}        
        result = await collection.update_one({"name": name}, {"$set": data})
        if result.modified_count:
            await DBChangeCapture.log_change(f"{collection_type} {name} Updated", {
                "name": existing_doc["name"],
                "updated_by": updated_by,
                "fields_modified": modified_fields
            })
            raise HTTPException(status_code=200, detail=f"{collection_type} {name} updated!")
        else:
            raise HTTPException(status_code=400, detail="No changes detected!")