import tkinter as tk
from fastapi import APIRouter,UploadFile,File,HTTPException
from tkinter import filedialog
from models.category_model import CategoryBase
from services.category_services import CategoryServices
router = APIRouter()
service=CategoryServices()
@router.post("/")
async def create_category(category: CategoryBase):
    category_data=category.model_dump()
    return await service.create(category_data)
@router.get("/{category_id}")
async def get_category_by_id(category_id:str):return await service.get_category_by_id(category_id=category_id)
@router.get("/")
async def get_all_categories():return await service.get_all_categories()
@router.put("/{category_id}")
async def update_category(category_id:str,updated_data:CategoryBase):return await service.update(category_id=category_id,data=updated_data)
@router.delete("/{category_id}")
async def delete_category(category_id:str):return await service.delete(category_id=category_id)
@router.post("/bulk_upload/")
async def bulk_import_categories(files:list[UploadFile]=File(...)):return await service.bulk_upload(files)
@router.post("/export/")
async def bulk_export_categories():
    root=tk.Tk()
    root.withdraw()
    root.attributes('-topmost',True)
    file_types=[("CSV File","*.csv"),("Excel File","*.xlsx")]
    file_path = filedialog.asksaveasfilename(title="Select Destination & File Type",filetypes=file_types,defaultextension=".xlsx")
    if not file_path:raise HTTPException(status_code=400,detail="No destination selected")
    return await service.bulk_download(file_path)
@router.post("/status")
async def category_status(category_id:str,new_status:str):return await service.change_status(category_id=category_id,new_status=new_status)