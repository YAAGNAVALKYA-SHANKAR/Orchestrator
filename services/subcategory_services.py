from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError
from general.database import sub_categories
class SubCategoryServices:
#CREATE SUB_CATEGORY
    @staticmethod
    async def create(data):
        dict = data.model_dump()
        counter_doc = await sub_categories.find_one({"function": "ID_counter"})
        counter_value = counter_doc["count"] if counter_doc else 0
        dict["sub_category_id"] = f"SUB_{counter_value:04d}"        
        existing_doc = await sub_categories.find_one({"sub_category_name": dict["sub_category_name"]})
        sub_category_name=dict["sub_category_name"]
        if existing_doc:            
            raise HTTPException(status_code=400, detail=f"Sub-Category {sub_category_name} already exists!")        
        try:
            result = await sub_categories.insert_one(dict)
            inserted_doc = await sub_categories.find_one({"_id": result.inserted_id})
            if inserted_doc:
                inserted_doc["_id"] = str(inserted_doc["_id"])
                await sub_categories.update_one({"function": "ID_counter"},{"$inc": {"count": 1}})    
            return inserted_doc
        except DuplicateKeyError:
            raise HTTPException(status_code=400, detail=f"Category must be unique!")
        
# UPDATE SUB_CATEGORY
    @staticmethod
    async def update(sub_category_id, data):
        existing_doc = await sub_categories.find_one({"sub_category_id": sub_category_id})
        if not existing_doc:
            raise HTTPException(status_code=404, detail=f"Sub-Category {sub_category_id} not found!")        
        modified_fields = {}
        for key, value in data.items():
            if key in existing_doc and existing_doc[key] != value:
                modified_fields[key] = {"old_value": existing_doc[key], "new_value": value}        
        result = await sub_categories.update_one({"sub_category_id": sub_category_id}, {"$set": data})
        if result.modified_count:
            raise HTTPException(status_code=200, detail=f"Sub-Category {sub_category_id} updated!")
        else:
            raise HTTPException(status_code=400, detail="No changes detected!")
        
# GET SUB_CATEGORY BY ID
    @staticmethod
    async def get_doc_by_id(sub_category_id):
        doc = await sub_categories.find_one({"sub_category_id": sub_category_id})
        if doc:
            doc["_id"] = str(doc["_id"])
            return doc
        raise HTTPException(status_code=404, detail=f"Sub-Category:{sub_category_id} not found!")
    
# GET ALL SUB_CATEGORIES
    @staticmethod
    async def get_all_docs(exclude_filter={"function": "ID_counter"}):
        doc_cursor = sub_categories.find()
        docs = await doc_cursor.to_list(length=None)
        return [{**doc, "_id": str(doc["_id"])} for doc in docs if not all(doc.get(k) == v for k, v in exclude_filter.items())]
    
# DELETE SUB_CATEGORY
    @staticmethod
    async def delete(sub_category_id):
        existing_doc = await sub_categories.find_one({"sub_category_id": sub_category_id})
        if not existing_doc:
            raise HTTPException(status_code=404, detail=f"Sub-Category {sub_category_id} not found")        
        result = await sub_categories.delete_one({"Sub-category_id": sub_category_id})
        if result.deleted_count:
            return HTTPException(status_code=200, detail=f"Sub-Category:{sub_category_id} deleted successfully!")
        else:
            raise HTTPException(status_code=500, detail=f"Failed to delete Sub-Category:{sub_category_id}!")
    