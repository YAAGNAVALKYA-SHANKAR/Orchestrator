import tkinter as tk
from fastapi import APIRouter,UploadFile,File
from tkinter import filedialog
from models.sub_cat_model import SubCategoryBase
from services.subcategory_services import SubCategoryServices
router = APIRouter()
service=SubCategoryServices()
@router.post("/")
async def create_sub_category(sub_category:SubCategoryBase):
    sub_category_data=sub_category.model_dump()
    return await service.create(sub_category_data)
@router.get("/{sub_category_id}")
async def get_sub_category_by_id(sub_category_id: str):return await service.get_doc_by_id(sub_category_id=sub_category_id)
@router.get("/")
async def get_all_sub_categories():return await service.get_all_sub_categories()
@router.get("/{category_name}")
async def get_sub_categories_by_category(category_name:str):return await service.get_sub_categories_by_category(category_name)
@router.put("/{sub_category_id}")
async def update_category(sub_category_id:str,updated_data:SubCategoryBase):return await service.update(sub_category_id=sub_category_id,data=updated_data)
@router.delete("/{sub_category_id}")
async def delete_category(sub_category_id:str):return await service.delete(sub_category_id=sub_category_id)
@router.post("/bulk_upload/")
async def bulk_import_sub_categories(files:list[UploadFile]=File(...)):return await service.bulk_upload(files)
@router.post("/export/")
async def bulk_export_categories():
    root=tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    file_types=[("CSV File","*.csv"),("Excel File","*.xlsx"),("JSON File","*.json"),]
    file_path=filedialog.asksaveasfilename(title="Select Destination & File Type",filetypes=file_types,defaultextension=".csv")
    if not file_path:return{"error": "No destination selected."}
    return await service.bulk_download(file_path)
@router.post("/status")
async def category_status(category_id:str,new_status:str):await service.change_status(category_id=category_id ,new_status=new_status)