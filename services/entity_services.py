import shutil,pandas,os,csv
from fastapi import HTTPException,UploadFile,File
from fastapi.responses import JSONResponse
from pydantic import create_model,ValidationError,Field
from pymongo.errors import DuplicateKeyError
from collections import OrderedDict
from general.database import entities,attributes,db
from models.entity_model import EntityBase
class EntityServices:
    @staticmethod
    async def create_entity(entity_data:EntityBase):
        entity_collection_name=f"entity_{entity_data.entity_name}"
        existing_collections=await db.list_collection_names()
        if entity_collection_name in existing_collections:raise HTTPException(status_code=400,detail=f"Entity '{entity_data.entity_name}' already exists!")
        entity_collection=db[entity_collection_name]
        counter_doc=await entities.find_one({"function": "ID_counter"})
        counter_value=counter_doc["count"] if counter_doc else 1
        entity_id=f"ENT_{counter_value:04d}"
        ordered_data=OrderedDict([("entity_id",entity_id),("entity_name",entity_data.entity_name),("entity_desc",entity_data.entity_desc),("entity_status",entity_data.entity_status),("entity_category",entity_data.entity_category),("entity_subcategory",entity_data.entity_subcategory),("entity_attributes",entity_data.entity_attributes),])
        await entities.insert_one(ordered_data)
        await entities.update_one({"function": "ID_counter"}, {"$inc": {"count": 1}})
        attribute_data_cursor=db["attributes"].find({"attribute_id": {"$in": entity_data.entity_attributes}})
        attribute_data_list=await attribute_data_cursor.to_list(length=1000)
        if not attribute_data_list:raise HTTPException(status_code=400, detail="Invalid attribute codes provided!")
        structured_attributes={attr["attribute_id"]:{"_id":attr["_id"],"name": attr["attribute_name"],"description":attr.get("attribute_desc","No description available"),"data_type":attr["attribute_data_type"],"default_value":attr.get("attribute_default_value",None),"value_constraints":attr.get("attribute_value_constraints",{}),"is_mandatory":attr["attribute_is_mandatory"],"is_editable":attr["attribute_is_editable"],"is_searchable":attr["attribute_is_searchable"],"id":attr["attribute_id"]}for attr in attribute_data_list}
        await entity_collection.insert_many([{"function":"ID_counter","count":1},{"function":"structure","structure":structured_attributes}])
        return{"message":f"Entity '{entity_data.entity_name}' created successfully!"}
    @staticmethod
    async def get_entity_by_name(entity_name:str):
        name=f"entity_{entity_name}"
        exclude_values=["ID_counter","structure"]
        doc_cursor=db[name].find()
        docs=await doc_cursor.to_list(length=None)
        return [{k:v for k,v in doc.items()if k!="_id"} for doc in docs if doc.get("function") not in exclude_values]
    @staticmethod
    async def get_all_entities():
        all_collections=await db.list_collection_names()
        entity_names=[col.replace("entity_","",1) for col in all_collections if col.startswith("entity_")]
        if entity_names:return entity_names
        raise HTTPException (status_code=404,detail="No Entities found!")
    @staticmethod
    async def update_entity(data, entity_name):
        existing_doc=await EntityServices.get_entity_by_name(entity_name)
        if not existing_doc:raise HTTPException(status_code=404, detail=f"Entity {entity_name} not found!")        
        dict_data=data.model_dump()               
        result1=await entities.update_one({"entity_name": entity_name}, {"$set": dict_data})
        result2=await db[entity_name].update_one({"function":"structure"},{"$set":{"structure":dict_data["entity_attributes"]}})
        if result1 and result2:
            name=dict_data["entity_name"]
            new_name=f"entity_{name}"
            old_name=f"entity_{entity_name}"
            if new_name!=old_name:
                all_entities=await EntityServices.get_all_entities()
                if name in all_entities:raise HTTPException(status_code=400,detail="Entity name already exists!")
                else: await db[old_name].rename(new_name)
            raise HTTPException(status_code=200, detail=f"Entity {entity_name} updated!")
        else:raise HTTPException(status_code=400, detail="No changes detected!")
    @staticmethod
    async def delete_entity(name):
        entity_name=f"entity_{name}"
        existing_doc=await EntityServices.get_entity_by_name(name)
        if not existing_doc:raise HTTPException(status_code=404,detail=f"Entity '{name}' does not exist!")
        else:
            await entities.delete_one({"entity_name":name})
            await db[entity_name].drop()
            raise HTTPException(status_code=200,detail=f"Successfully deleted Entity '{name}'")
    @staticmethod
    async def add_data_to_entity(entity_name: str, data: dict):
        entity=f"entity_{entity_name}"
        entity_collection=db[entity]
        structure_doc=await entity_collection.find_one({"function":"structure"})
        if not structure_doc:raise HTTPException(status_code=404,detail=f"Structure not found for entity {entity_name}")
        attribute_metadata=structure_doc.get("structure",{})
        fields={}
        data_type_map={"int":int,"float":float,"bool":bool,"string":str}
        for attr_id, attr_details in attribute_metadata.items():
            field_type=data_type_map.get(attr_details.get("data_type","string"),str)
            fields[attr_details["name"]]=(field_type, Field(default=attr_details.get("default_value",None),description=attr_details.get("description",""),))
        EntityModel=create_model(entity_name+"Model",**fields)
        try:validated_data=EntityModel(**data)
        except ValidationError as e:raise HTTPException(status_code=422,detail=e.errors())
        id_counter_doc=await entity_collection.find_one({"function":"ID_counter"})
        if not id_counter_doc:raise HTTPException(status_code=500, detail="ID_counter not found in entity collection")
        new_id=f"ID_{id_counter_doc['count']:04d}"
        validated_data=validated_data.dict()
        validated_data["ID"]=new_id
        await entity_collection.insert_one(validated_data)
        await entity_collection.update_one({"function":"ID_counter"},{"$inc":{"count":1}})
        return{"message":"Data added successfully","ID":new_id}
    @staticmethod
    async def change_entity_status(entity_name: str, new_status: str):
        existing_doc = await entities.find_one({"entity_name":entity_name})
        if not existing_doc: raise HTTPException(status_code=404, detail=f"Entity: '{entity_name}' not found")
        existing_doc.get("entity_status","Unknown")
        result=await entities.update_one({"entity_name":entity_name},{"$set":{"entity_status":new_status}})
        if result.modified_count: raise HTTPException(status_code=200,detail="Entity status changed successfully")        
        else:raise HTTPException(status_code=400, detail="No changes detected")
    @staticmethod
    async def bulk_upload(entity_name,files):
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
                    await EntityServices.add_data_to_entity(entity_name, entry)
                    inserted_count+=1        
            except Exception as e: results.append({"filename": file.filename, "error": str(e)})
        return JSONResponse(content={"message":f"Import completed:{inserted_count} new,{overwritten_count}overwritten,{skipped_count}skipped.","details": results})
    @staticmethod
    async def bulk_download(entity_name,file_path):
        entity=f"entity_{entity_name}",
        cursor=db[entity].find({"function":{"$exists": False}},{"_id": 0})
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