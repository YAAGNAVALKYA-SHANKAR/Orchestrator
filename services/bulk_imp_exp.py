import os
import csv
import pandas as pd
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorCollection
from services.logs import DBChangeCapture
class ImportExportService:
    @staticmethod
    async def bulk_import(
        overwrite: bool,
        file_path: str,
        user: str,
        collection: AsyncIOMotorCollection,
        collection_type: str
    ):
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found!")

        file_ext = os.path.splitext(file_path)[-1].lower()
        if file_ext == ".csv":
            df = pd.read_csv(file_path)
        elif file_ext in [".xls", ".xlsx"]:
            df = pd.read_excel(file_path)
        else:
            raise HTTPException(status_code=415, detail="Unsupported file format!")

        data = df.to_dict(orient="records")
        if not data:
            raise HTTPException(status_code=404, detail=f"No {collection_type} found!")

        new_entries = []
        skipped_count = 0
        overwritten_count = 0

        for entry in data:
            name = entry.get("name")
            if not name:
                skipped_count += 1
                continue

            existing_doc = await collection.find_one({"name": name}, {"_id": 1})
            if existing_doc:
                if not overwrite:
                    skipped_count += 1
                    continue
                else:
                    await collection.update_one({"name": name}, {"$set": entry})
                    overwritten_count += 1
                    await DBChangeCapture.log_change(f"{collection_type} Updated", {
                        "name": name,
                        "updated_by": user,
                        "fields_modified": list(entry.keys()),
                    })
            else:
                new_entries.append(entry)

        # Insert new entries
        inserted_count = 0
        if new_entries:
            print("New Entries:", new_entries)
            result = await collection.insert_many(new_entries)
            inserted_count = len(result.inserted_ids)

            for entry in new_entries:
                await DBChangeCapture.log_change(f"{collection_type} Created", {
                    "name": entry["name"],
                    "created_by": "Bulk Import",
                })

        return {
            "status_code": 200,
            "detail": f"Import completed: {inserted_count} new, {overwritten_count} overwritten, {skipped_count} skipped."
        }

    @staticmethod
    async def bulk_export(file_path, collection: AsyncIOMotorCollection, collection_type: str):
        cursor = collection.find({}, {"_id": 0})  # Exclude _id field
        data = await cursor.to_list(length=None)

        if not data:
            raise HTTPException(status_code=404, detail=f"No {collection_type} found!")

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
            return {"detail": f"{collection_type} exported successfully!", "path": file_path}

        elif file_ext in [".xls", ".xlsx"]:
            df = pd.DataFrame(data)
            if file_ext == ".xls":
                df.to_excel(file_path, index=False, engine="xlwriter")
            elif file_ext == ".xlsx":
                df.to_excel(file_path, index=False, engine="openpyxl")
            return {"detail": f"{collection_type} exported successfully!", "path": file_path}

        else:
            raise HTTPException(status_code=400, detail="Unsupported file format!")

