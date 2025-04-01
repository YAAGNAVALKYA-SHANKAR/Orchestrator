import shutil, pandas, os, csv
from fastapi import HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
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
    async def get_category_by_name(category_id):
        doc = await categories.find_one({"category_id": category_id})
        if doc:
            doc["_id"] = str(doc["_id"])
            return doc
        raise HTTPException(status_code=404, detail=f"Category:{category_id} not found!")
    
# GET ALL CATEGORIES
    @staticmethod
    async def get_all_categories():
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

# BULK UPLOAD CATEGORIES
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
                    raise HTTPException(status_code=404, detail=f"No Categories found!")
                new_entries = []
                skipped_count = 0
                overwritten_count = 0 
                for entry in data:
                    name = entry.get("category_name")
                    if not name:
                        skipped_count += 1
                        continue

                    existing_doc = await categories.find_one({"category_name": name}, {"_id": 1})
                    if existing_doc:
                        if not overwrite:
                            skipped_count += 1
                            continue
                        else:
                            await categories.update_one({"category_name": name}, {"$set": entry})
                            overwritten_count += 1
                    else:
                        new_entries.append(entry)
                inserted_count = 0
                if new_entries:
                    print("New Entries:", new_entries)
                    result = await categories.insert_many(new_entries)
                    inserted_count = len(result.inserted_ids)
        
            except Exception as e:
                results.append({"filename": file.filename, "error": str(e)})

        return JSONResponse(content={"message": f"Import completed: {inserted_count} new, {overwritten_count} overwritten, {skipped_count} skipped.", "details": results})
    
#BULK DOWNLOAD CATEGORIES

    @staticmethod
    async def bulk_download(file_path):
        cursor = categories.find({"function": {"$exists": False}}, {"_id": 0})
        data = await cursor.to_list(length=None)

        if not data:
            raise HTTPException(status_code=404, detail=f"No categories found!")

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
            return {"detail": f"Categorites exported successfully!", "path": file_path}

        elif file_ext in [".xls", ".xlsx"]:
            df = pandas.DataFrame(data)
            if file_ext == ".xls":
                df.to_excel(file_path, index=False, engine="xlwriter")
            elif file_ext == ".xlsx":
                df.to_excel(file_path, index=False, engine="openpyxl")
            return {"detail": f"Categories exported successfully!", "path": file_path}

        else:
            raise HTTPException(status_code=400, detail="Unsupported file format!")

#CHANGE CATEGORY STATUS

    @staticmethod
    async def change_status(category_id: str, new_status: str):
        existing_doc = await categories.find_one({"category_id": category_id})
        if not existing_doc:
            raise HTTPException(status_code=404, detail=f"Category not found")
        
        existing_doc.get("category_status", "Unknown")
        result = await categories.update_one({"category_id": category_id}, {"$set": {"category_status": new_status}})
        if result.modified_count:
            raise HTTPException(status_code=200, detail="Category status changed successfully")        
        else:
            raise HTTPException(status_code=400, detail="No changes detected")        