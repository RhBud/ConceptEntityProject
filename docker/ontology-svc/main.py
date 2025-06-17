from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
import os
from typing import Dict, Any

app = FastAPI(title="Data Pipeline API")

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://mongodb:27017")
client = AsyncIOMotorClient(MONGODB_URL)
db = client.pipeline_db

@app.get("/health/{client_name}/{config_name}/{environment}/{process}")
async def health_check():
    """Health check endpoint"""
    try:
        # Check MongoDB connection
        await db.command("ping")
        return {"status": "healthy", "mongodb": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.post("/process")
async def process_data(data: Dict[str, Any]):
    """Process data endpoint"""
    try:
        # Store the data in MongoDB
        result = await db.processed_data.insert_one(data)
        return {
            "status": "success",
            "message": "Data processed successfully",
            "id": str(result.inserted_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data")
async def get_data():
    """Retrieve processed data"""
    try:
        cursor = db.processed_data.find()
        data = await cursor.to_list(length=None)
        return {"data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 