import pandas, os, shutil, csv
from fastapi import HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pymongo.errors import DuplicateKeyError
from general.database import attributes
UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)
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

# BULK UPLOAD ATTRIBUTES
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
                    raise HTTPException(status_code=404, detail=f"No Attributes found!")
                new_entries = []
                skipped_count = 0
                overwritten_count = 0 
                for entry in data:
                    name = entry.get("attribute_name")
                    if not name:
                        skipped_count += 1
                        continue

                    existing_doc = await attributes.find_one({"attribute_name": name}, {"_id": 1})
                    if existing_doc:
                        if not overwrite:
                            skipped_count += 1
                            continue
                        else:
                            await attributes.update_one({"attribute_name": name}, {"$set": entry})
                            overwritten_count += 1
                    else:
                        new_entries.append(entry)
                inserted_count = 0
                if new_entries:
                    print("New Entries:", new_entries)
                    result = await attributes.insert_many(new_entries)
                    inserted_count = len(result.inserted_ids)
        
            except Exception as e:
                results.append({"filename": file.filename, "error": str(e)})

        return JSONResponse(content={"message": f"Import completed: {inserted_count} new, {overwritten_count} overwritten, {skipped_count} skipped.", "details": results})
    
#BULK DOWNLOAD ATTRIBUTES

    @staticmethod
    async def bulk_download(file_path):
        cursor = attributes.find({}, {"_id": 0})  # Exclude _id field
        data = await cursor.to_list(length=None)

        if not data:
            raise HTTPException(status_code=404, detail=f"No Attributes found!")

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
            return {"detail": f"Attributes exported successfully!", "path": file_path}

        elif file_ext in [".xls", ".xlsx"]:
            df = pandas.DataFrame(data)
            if file_ext == ".xls":
                df.to_excel(file_path, index=False, engine="xlwriter")
            elif file_ext == ".xlsx":
                df.to_excel(file_path, index=False, engine="openpyxl")
            return {"detail": f"Attributes exported successfully!", "path": file_path}

        else:
            raise HTTPException(status_code=400, detail="Unsupported file format!")

#CHANGE ATTRIBUTE STATUS

    @staticmethod
    async def change_status(attribute_id: str, new_status: str):
        existing_doc = await attributes.find_one({"attribute_id": attribute_id})
        if not existing_doc:
            raise HTTPException(status_code=404, detail=f"Attribute not found")
        
        existing_doc.get("attribute_status", "Unknown")
        result = await attributes.update_one({"attribute_id": attribute_id}, {"$set": {"attribute_status": new_status}})
        if result.modified_count:
            raise HTTPException(status_code=200, detail="Attribute status changed successfully")        
        else:
            raise HTTPException(status_code=400, detail="No changes detected")        