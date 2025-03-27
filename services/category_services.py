from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError
from general.database import categories
class CategoryServices:
#CREATE CATEGORY
    @staticmethod
    async def create(data):
        dict = data.model_dump()
        counter_doc = await categories.find_one({"function": "ID_counter"})
        counter_value = counter_doc["count"] if counter_doc else 0
        dict["category_id"] = f"CAT_{counter_value:04d}"
        existing_doc = await categories.find_one({"category_name": dict["category_name"]})
        category_name=dict["category_name"]
        if existing_doc:            
            raise HTTPException(status_code=400, detail=f"Category {category_name} already exists!")        
        else:
            try:
                result = await categories.insert_one(dict)
                inserted_doc = await categories.find_one({"_id": result.inserted_id})
                if inserted_doc:
                    inserted_doc["_id"] = str(inserted_doc["_id"])
                    await categories.update_one({"function": "ID_counter"},{"$inc": {"count": 1}})
                return inserted_doc
            except DuplicateKeyError:
                print (DuplicateKeyError)
                raise HTTPException(status_code=400, detail=f"Category must be unique!")
        
# UPDATE CATEGORY
    @staticmethod
    async def update(category_id, data):
        existing_doc = await categories.find_one({"category_id": category_id})
        if not existing_doc:
            raise HTTPException(status_code=404, detail=f"Category {category_id} not found!")        
        dict_data=data.model_dump()               
        result = await categories.update_one({"category_id": category_id}, {"$set": dict_data})
        if result.modified_count:
            raise HTTPException(status_code=200, detail=f"Category {category_id} updated!")
        else:
            raise HTTPException(status_code=400, detail="No changes detected!")
        
# GET CATEGORY BY ID
    @staticmethod
    async def get_doc_by_name(category_id):
        doc = await categories.find_one({"category_id": category_id})
        if doc:
            doc["_id"] = str(doc["_id"])
            return doc
        raise HTTPException(status_code=404, detail=f"Category:{category_id} not found!")
    
# GET ALL CATEGORIES
    @staticmethod
    async def get_all_docs():
        exclude_filter={"function": "ID_counter"}
        doc_cursor = categories.find()
        docs = await doc_cursor.to_list(length=None)
        return [{**doc, "_id": str(doc["_id"])} for doc in docs if not all(doc.get(k) == v for k, v in exclude_filter.items())]
    
# DELETE CATEGORY
    @staticmethod
    async def delete(category_id):
        existing_doc = await categories.find_one({"category_id": category_id})
        if not existing_doc:
            raise HTTPException(status_code=404, detail=f"Category {category_id} not found")        
        result = await categories.delete_one({"category_id": category_id})
        if result.deleted_count:
            return HTTPException(status_code=200, detail=f"Category:{category_id} deleted successfully!")
        else:
            raise HTTPException(status_code=500, detail=f"Failed to delete Category:{category_id}!")
    