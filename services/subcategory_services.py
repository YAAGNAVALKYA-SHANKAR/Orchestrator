import pandas, os, shutil, csv
from fastapi import HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pymongo.errors import DuplicateKeyError
from general.database import sub_categories
UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)
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
            raise HTTPException(status_code=400, detail=f"Sub-Category must be unique!")
        
# UPDATE SUB_CATEGORY
    @staticmethod
    async def update(sub_category_id, data):
        existing_doc = await sub_categories.find_one({"sub_category_id": sub_category_id})
        if not existing_doc:
            raise HTTPException(status_code=404, detail=f"Sub-Category {sub_category_id} not found!")        
        dict_data=data.model_dump()       
        result = await sub_categories.update_one({"sub_category_id": sub_category_id}, {"$set": dict_data})
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
    async def get_all_sub_categories(exclude_filter={"function": "ID_counter"}):
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

# BULK UPLOAD SUB-CATEGORIES
    @staticmethod
    async def bulk_upload(overwrite:bool, files: list[UploadFile] = File(...)):
        results = []
        
        for file in files:
            UPLOAD_DIR="uploaded_files"
            file_location = f"{UPLOAD_DIR}/{file.filename}"
            
            # Save the uploaded file
            with open(file_location, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            try:
                # Read and process CSV file
                file_ext = os.path.splitext(file_location)[-1].lower()
                if file_ext == ".csv":
                    df = pandas.read_csv(file_location)
                elif file_ext in [".xls", ".xlsx"]:
                    df = pandas.read_excel(file_location)
                else:
                    raise HTTPException(status_code=415, detail="Unsupported file format!")
                data = df.to_dict(orient="records")
                if not data:
                    raise HTTPException(status_code=404, detail=f"No Sub-Categories found!")
                new_entries = []
                skipped_count = 0
                overwritten_count = 0 
                for entry in data:
                    name = entry.get("sub_category_name")
                    if not name:
                        skipped_count += 1
                        continue

                    existing_doc = await sub_categories.find_one({"sub_category_name": name}, {"_id": 1})
                    if existing_doc:
                        if not overwrite:
                            skipped_count += 1
                            continue
                        else:
                            await sub_categories.update_one({"sub_category_name": name}, {"$set": entry})
                            overwritten_count += 1
                    else:
                        new_entries.append(entry)
                inserted_count = 0
                if new_entries:
                    print("New Entries:", new_entries)
                    result = await sub_categories.insert_many(new_entries)
                    inserted_count = len(result.inserted_ids)
        
            except Exception as e:
                results.append({"filename": file.filename, "error": str(e)})

        return JSONResponse(content={"message": f"Import completed: {inserted_count} new, {overwritten_count} overwritten, {skipped_count} skipped.", "details": results})
    
#BULK DOWNLOAD SUB-CATEGORIES

    @staticmethod
    async def bulk_download(file_path):
        cursor = sub_categories.find({"function": {"$exists": False}}, {"_id": 0})
        data = await cursor.to_list(length=None)

        if not data:
            raise HTTPException(status_code=404, detail=f"No Sub-Categopories found!")

        dir_name = os.path.dirname(file_path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name)

        file_ext = os.path.splitext(file_path)[-1].lower()

        if file_ext == ".csv":
            keys = data[0].keys()
            with open(file_path, "w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=keys)
                writer.writeheader()
                writer.writerows(data)
            return {"detail": f"Sub-Categories exported successfully!", "path": file_path}

        elif file_ext in [".xls", ".xlsx"]:
            df = pandas.DataFrame(data)
            if file_ext == ".xls":
                df.to_excel(file_path, index=False, engine="xlwriter")
            elif file_ext == ".xlsx":
                df.to_excel(file_path, index=False, engine="openpyxl")
            return {"detail": f"Sub-Categories exported successfully!", "path": file_path}

        else:
            raise HTTPException(status_code=400, detail="Unsupported file format!")

#CHANGE SUB-CATEGORY STATUS

    @staticmethod
    async def change_status(sub_category_id: str, new_status: str):
        existing_doc = await sub_categories.find_one({"sub_category_id": sub_category_id})
        if not existing_doc:
            raise HTTPException(status_code=404, detail=f"Sub-Category not found")
        
        existing_doc.get("sub_category_status", "Unknown")
        result = await sub_categories.update_one({"sub_category_id": sub_category_id}, {"$set": {"sub_category_status": new_status}})
        if result.modified_count:
            raise HTTPException(status_code=200, detail="Sub-Category status changed successfully")        
        else:
            raise HTTPException(status_code=400, detail="No changes detected")        