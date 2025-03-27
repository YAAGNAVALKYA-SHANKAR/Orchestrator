from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError
from general.database import attributes
class AttributeServices:
#CREATE ATTRIBUTE
    @staticmethod
    async def create(data):
        dict = data.model_dump()
        counter_doc = await attributes.find_one({"function": "ID_counter"})
        counter_value = counter_doc["count"] if counter_doc else 0
        dict["attribute_id"] = f"ATTR_{counter_value:04d}"
        existing_doc = await attributes.find_one({"attribute_name": dict["attribute_name"]})
        attribute_name=dict["attribute_name"]
        if existing_doc:            
            raise HTTPException(status_code=400, detail=f"Attribute {attribute_name} already exists!")        
        else:
            try:
                result = await attributes.insert_one(dict)
                inserted_doc = await attributes.find_one({"_id": result.inserted_id})
                if inserted_doc:
                    inserted_doc["_id"] = str(inserted_doc["_id"])
                    await attributes.update_one({"function": "ID_counter"},{"$inc": {"count": 1}})
                return inserted_doc
            except DuplicateKeyError:
                print (DuplicateKeyError)
                raise HTTPException(status_code=400, detail=f"Attribute must be unique!")
        
# UPDATE ATTRIBUTE
    @staticmethod
    async def update(attribute_id, data):
        existing_doc = await attributes.find_one({"attribute_id": attribute_id})
        if not existing_doc:
            raise HTTPException(status_code=404, detail=f"Attribute {attribute_id} not found!")        
        modified_fields = {}
        for key, value in data.items():
            if key in existing_doc and existing_doc[key] != value:
                modified_fields[key] = {"old_value": existing_doc[key], "new_value": value}        
        result = await attributes.update_one({"attribute_id": attribute_id}, {"$set": data})
        if result.modified_count:
            raise HTTPException(status_code=200, detail=f"Attribute {attribute_id} updated!")
        else:
            raise HTTPException(status_code=400, detail="No changes detected!")
        
# GET ATTRIBUTE BY ID
    @staticmethod
    async def get_doc_by_name(attribute_id):
        doc = await attributes.find_one({"attribute_id": attribute_id})
        if doc:
            doc["_id"] = str(doc["_id"])
            return doc
        raise HTTPException(status_code=404, detail=f"Attribute:{attribute_id} not found!")
    
# GET ALL ATTRIBUTES
    @staticmethod
    async def get_all_docs():
        exclude_filter={"function": "ID_counter"}
        doc_cursor = attributes.find()
        docs = await doc_cursor.to_list(length=None)
        return [{**doc, "_id": str(doc["_id"])} for doc in docs if not all(doc.get(k) == v for k, v in exclude_filter.items())]
    
# DELETE ATTRIBUTE
    @staticmethod
    async def delete(attribute_id):
        existing_doc = await attributes.find_one({"attribute_id": attribute_id})
        if not existing_doc:
            raise HTTPException(status_code=404, detail=f"Attribute {attribute_id} not found")        
        result = await attributes.delete_one({"attribute_id": attribute_id})
        if result.deleted_count:
            return HTTPException(status_code=200, detail=f"Attribute:{attribute_id} deleted successfully!")
        else:
            raise HTTPException(status_code=500, detail=f"Failed to delete Attribute:{attribute_id}!")
    