from fastapi import APIRouter,UploadFile,File
import tkinter as tk
from tkinter import filedialog
from models.attribute_model import AttributeBase
from services.attribute_services import AttributeServices
router = APIRouter()
service=AttributeServices()
@router.post("/")
async def create_attribute(attribute:AttributeBase):
    attribute_data=attribute.model_dump()
    return await service.create(attribute_data)
@router.get("/{attribute_name}")
async def get_attribute_by_name(attribute_id:str):return await service.get_doc_by_name(attribute_id=attribute_id)
@router.get("/")
async def get_all_attributes():return await service.get_all_docs()
@router.put("/{attribute_id}")
async def update_attribute(attribute_id:str,updated_data:AttributeBase):return await service.update(attribute_id=attribute_id,base_data=updated_data)
@router.delete("/{attribute_id}")
async def delete_attribute(attribute_id: str):return await service.delete(attribute_id=attribute_id)
@router.post("/bulk_upload/")
async def bulk_import_sub_categories(files:list[UploadFile]=File(...)):return await service.bulk_upload(files)
@router.post("/export/")
async def bulk_export_attributes():
    root=tk.Tk()
    root.withdraw()
    root.attributes('-topmost',True)
    file_types=[("CSV File","*.csv"),("Excel File","*.xlsx"),("JSON File","*.json"),]
    file_path=filedialog.asksaveasfilename(title="Select Destination & File Type",filetypes=file_types,defaultextension=".csv")
    if not file_path:return{"error":"No destination selected."}
    return await service.bulk_download(file_path)
@router.post("/status")
async def attribute_status(attribute_id:str,new_status:str):return await service.change_status(attribute_id=attribute_id,new_status=new_status)