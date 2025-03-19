from fastapi import HTTPException
from services import logs

class ChangeStatus:
    @staticmethod
    async def change_status(name: str, new_status: str, changed_by: str, collection, collection_type):
        existing_doc = await collection.find_one({"name": name})
        if not existing_doc:
            raise HTTPException(status_code=404, detail=f"{collection_type} not found")
        
        previous_status = existing_doc.get("status", "Unknown")
        result = await collection.update_one({"name": name}, {"$set": {"status": new_status}})
        if result.modified_count:
            await logs.DBChangeCapture.log_change(f"{collection_type} Status Changed", {
                "name": existing_doc["name"],
                "changed_by": changed_by,
                "previous_status": previous_status,
                "new_status": new_status
            })
            return {"message": f"{collection_type} status updated successfully"}
        else:
            raise HTTPException(status_code=400, detail="No changes detected")        