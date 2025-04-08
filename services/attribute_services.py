import pandas,os,shutil,csv
from collections import OrderedDict
from fastapi import HTTPException,UploadFile,File
from fastapi.responses import JSONResponse
from pymongo.errors import DuplicateKeyError
from general.database import attributes
class AttributeServices:
    @staticmethod
    async def create(attribute_data):
        counter_doc=await attributes.find_one({"function":"ID_counter"})
        counter_value=counter_doc["count"]if counter_doc else 0
        attribute_data["attribute_id"]=f"ATTR_{counter_value:04d}"
        existing_doc=await attributes.find_one({"attribute_name":attribute_data["attribute_name"]})
        if existing_doc:raise HTTPException(status_code=400,detail=f"Attribute {attribute_data["attribute_name"]} already exists!")        
        try:
            result=await attributes.insert_one(attribute_data)
            inserted_doc=await attributes.find_one({"_id":result.inserted_id})
            if inserted_doc:
                await attributes.update_one({"function":"ID_counter"},{"$inc":{"count": 1}})
                inserted_doc["_id"]=str(inserted_doc["_id"])
            return inserted_doc
        except DuplicateKeyError:raise HTTPException(status_code=400,detail=f"Attribute must be unique!")
    @staticmethod
    async def update(attribute_id, base_data):
        data=base_data.dict()
        existing_doc=await attributes.find_one({"attribute_id":attribute_id})
        if not existing_doc:raise HTTPException(status_code=404,detail=f"Attribute {attribute_id} not found!")
        modified_fields={}
        for key,value in data.items():
            if key in existing_doc and existing_doc[key]!=value:modified_fields[key]={"old_value":existing_doc[key],"new_value": value}
        result=await attributes.update_one({"attribute_id":attribute_id},{"$set":data})
        if result.modified_count>0:return{"message":f"Attribute {attribute_id} updated successfully!", "modified_fields": modified_fields}
        else:raise HTTPException(status_code=400,detail="No changes detected!")
    @staticmethod
    async def get_doc_by_name(attribute_id):
        doc=await attributes.find_one({"attribute_id":attribute_id})
        if doc:
            doc["_id"]=str(doc["_id"])
            return doc
        raise HTTPException(status_code=404,detail=f"Attribute:{attribute_id} not found!")
    @staticmethod
    async def get_all_docs():
        exclude_filter={"function":"ID_counter"}
        doc_cursor=attributes.find()
        docs=await doc_cursor.to_list(length=None)
        return[{**doc,"_id":str(doc["_id"])}for doc in docs if not all(doc.get(k)==v for k,v in exclude_filter.items())]
    @staticmethod
    async def delete(attribute_id):
        existing_doc=await attributes.find_one({"attribute_id":attribute_id})
        if not existing_doc:raise HTTPException(status_code=404,detail=f"Attribute {attribute_id} not found")        
        result=await attributes.delete_one({"attribute_id":attribute_id})
        if result.deleted_count:return HTTPException(status_code=200,detail=f"Attribute:{attribute_id} deleted successfully!")
        else:raise HTTPException(status_code=500,detail=f"Failed to delete Attribute:{attribute_id}!")
    @staticmethod
    async def bulk_upload(files):
        results=[]
        inserted_count=0
        skipped_count=0
        overwritten_count=0 
        for file in files:
            UPLOAD_DIR="uploaded_files"
            file_location=f"{UPLOAD_DIR}/{file.filename}"
            with open(file_location,"wb")as buffer:shutil.copyfileobj(file.file, buffer)
            try:
                file_ext=os.path.splitext(file_location)[-1].lower()
                if file_ext==".csv":df=pandas.read_csv(file_location)
                elif file_ext in [".xls", ".xlsx"]:df=pandas.read_excel(file_location)
                else:raise HTTPException(status_code=415,detail="Unsupported file format!")
                data=df.to_dict(orient="records")
                if not data:raise HTTPException(status_code=404,detail=f"No data found!")                
                for entry in data:
                    await AttributeServices.create(entry)
                    inserted_count+=1        
            except Exception as e: results.append({"filename": file.filename, "error": str(e)})
        return JSONResponse(content={"message":f"Import completed:{inserted_count} new,{overwritten_count}overwritten,{skipped_count}skipped.","details": results})
    @staticmethod
    async def bulk_download(file_path):
        cursor=attributes.find({"function":{"$exists":False}},{"_id":0})
        data=await cursor.to_list(length=None)
        data=await cursor.to_list(length=None)
        if not data:raise HTTPException(status_code=404,detail=f"No data found!")
        dir_name=os.path.dirname(file_path)
        if dir_name and not os.path.exists(dir_name):os.makedirs(dir_name)
        file_ext=os.path.splitext(file_path)[-1].lower()
        if file_ext==".csv":
            keys=data[0].keys()
            with open(file_path,"w",newline="",encoding="utf-8") as file:
                writer=csv.DictWriter(file,fieldnames=keys)
                writer.writeheader()
                writer.writerows(data)
            return {"detail":f"Data exported successfully!","path":file_path}
        elif file_ext==".xlsx":
            df=pandas.DataFrame(data)
            df.to_excel(file_path,index=False,engine="openpyxl")
            return{"detail":f"Data exported successfully!","path":file_path}
        else:raise HTTPException(status_code=400,detail="Unsupported file format!")
    @staticmethod
    async def change_status(attribute_id:str,new_status:str):
        existing_doc=await attributes.find_one({"attribute_id":attribute_id})
        if not existing_doc:raise HTTPException(status_code=404,detail=f"Attribute not found")        
        existing_doc.get("attribute_status","Unknown")
        result=await attributes.update_one({"attribute_id":attribute_id},{"$set":{"attribute_status":new_status}})
        if result.modified_count:raise HTTPException(status_code=200,detail="Attribute status changed successfully")        
        else:raise HTTPException(status_code=400,detail="No changes detected")        