import pandas, os, shutil, csv
from collections import OrderedDict
from fastapi import HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pymongo.errors import DuplicateKeyError
from general.database import sub_categories, categories
class SubCategoryServices:
    @staticmethod
    async def create(sub_category_data):
        counter_doc=await sub_categories.find_one({"function":"ID_counter"})
        counter_value=counter_doc.get("count",0)if counter_doc else 0
        sub_category_id=f"SUB_{counter_value:04d}"
        existing_doc=await sub_categories.find_one({"sub_category_name":sub_category_data["sub_category_name"]})
        if existing_doc:raise HTTPException(status_code=400,detail=f"Sub-Category {sub_category_data['sub_category_name']} already exists!")        
        try:
            ordered_data=OrderedDict([("sub_category_id",sub_category_id),("sub_category_name",sub_category_data["sub_category_name"]),("sub_category_type",sub_category_data["sub_category_type"]),("sub_category_desc",sub_category_data["sub_category_desc"]),])
            result=await sub_categories.insert_one(dict(ordered_data))
            inserted_doc=await sub_categories.find_one({"_id":result.inserted_id})
            if inserted_doc:inserted_doc["_id"]=str(inserted_doc["_id"])
            await sub_categories.update_one({"function":"ID_counter"},{"$inc":{"count":1}},upsert=True)
            return inserted_doc
        except DuplicateKeyError:raise HTTPException(status_code=400,detail="Sub-Category must be unique!")
    @staticmethod
    async def update(sub_category_id, data):
        existing_doc=await sub_categories.find_one({"sub_category_id":sub_category_id})
        if not existing_doc:raise HTTPException(status_code=404,detail=f"Sub-Category {sub_category_id} not found!")        
        dict_data=data.model_dump()       
        result=await sub_categories.update_one({"sub_category_id":sub_category_id},{"$set":dict_data})
        if result.modified_count:raise HTTPException(status_code=200,detail=f"Sub-Category {sub_category_id} updated!")
        else:raise HTTPException(status_code=400,detail="No changes detected!")
    @staticmethod
    async def get_doc_by_id(sub_category_id):
        doc=await sub_categories.find_one({"sub_category_id":sub_category_id})
        if doc:
            doc["_id"]=str(doc["_id"])
            return doc
        raise HTTPException(status_code=404,detail=f"Sub-Category:{sub_category_id} not found!")
    @staticmethod
    async def get_all_sub_categories(exclude_filter={"function":"ID_counter"}):
        doc_cursor=sub_categories.find()
        docs=await doc_cursor.to_list(length=None)
        return[{**doc,"_id":str(doc["_id"])}for doc in docs if not all(doc.get(k)==v for k,v in exclude_filter.items())]    
    @staticmethod
    async def get_sub_categories_by_category(category_name):
        category=await categories.find_one({"category_name":category_name})
        if category:
            subcategories=await sub_categories.find({"sub_category_category":category_name})
            if subcategories:return subcategories
            raise HTTPException(status_code=404,detail=f"No Sub-Categories under the Category:{category_name}")
        else:raise HTTPException(status_code=404,detail=f"Category '{category_name}' not found!")
    @staticmethod
    async def delete(sub_category_id):
        existing_doc=await sub_categories.find_one({"sub_category_id":sub_category_id})
        if not existing_doc:raise HTTPException(status_code=404,detail=f"Sub-Category {sub_category_id} not found")        
        result=await sub_categories.delete_one({"Sub-category_id": sub_category_id})
        if result.deleted_count:return HTTPException(status_code=200, detail=f"Sub-Category:{sub_category_id} deleted successfully!")
        else:raise HTTPException(status_code=500,detail=f"Failed to delete Sub-Category:{sub_category_id}!")
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
                elif file_ext in [".xlsx"]:df=pandas.read_excel(file_location)
                else:raise HTTPException(status_code=415,detail="Unsupported file format!")
                data=df.to_dict(orient="records")
                if not data:raise HTTPException(status_code=404,detail=f"No data found!")                
                for entry in data:
                    await SubCategoryServices.create(entry)
                    inserted_count+=1        
            except Exception as e:results.append({"filename":file.filename,"error":str(e)})
        return JSONResponse(content={"message":f"Import completed:{inserted_count} new,{overwritten_count}overwritten,{skipped_count}skipped.","details": results})
    @staticmethod
    async def bulk_download(file_path):        
        cursor=sub_categories.find({"function":{"$exists":False}},{"_id":0})
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
    async def change_status(sub_category_id:str,new_status:str):
        existing_doc=await sub_categories.find_one({"sub_category_id":sub_category_id})
        if not existing_doc:raise HTTPException(status_code=404,detail=f"Sub-Category not found")        
        existing_doc.get("sub_category_status", "Unknown")
        result=await sub_categories.update_one({"sub_category_id":sub_category_id},{"$set":{"sub_category_status":new_status}})
        if result.modified_count:raise HTTPException(status_code=200, detail="Sub-Category status changed successfully")        
        else:raise HTTPException(status_code=400, detail="No changes detected")        