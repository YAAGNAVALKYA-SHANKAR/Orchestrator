from fastapi import HTTPException
from services import logs

class Delete:
# DELETE CATEGORY
    @staticmethod
    async def delete(name, deleted_by, reason, collection, collection_type):
        existing_doc = await collection.find_one({"name": name})
        if not existing_doc:
            raise HTTPException(status_code=404, detail=f"{collection_type} {name} not found")        
        result = await collection.delete_one({"name": name})
        if result.deleted_count:
            await logs.DBChangeCapture.log_change(f"{collection_type} {name} Deleted", {
                "name": existing_doc["name"],
                "deleted_by": deleted_by,
                "reason": reason
            })
            return HTTPException(status_code=200, detail=f"{collection_type} {name} deleted successfully!")
        else:
            raise HTTPException(status_code=500, detail=f"Failed to delete {collection_type}:{name}!")