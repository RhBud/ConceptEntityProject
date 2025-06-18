from fastapi import APIRouter, HTTPException
import json
from motor.motor_asyncio import AsyncIOMotorClient
import os
from app.core.entity import (
    get_single_response,
    strip_markdown_fences
)
from app.models.schemas import EntityRequest, EntityResponse

router = APIRouter()

# MongoDB connection for health check
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://mongodb:27017")
client = AsyncIOMotorClient(MONGODB_URL)
db = client.pipeline_db

@router.post("/analyze-entity", 
         response_model=EntityResponse,
         summary="Analyze a medical concept and return its entity type and associated codes",
         description="Takes a medical concept name and returns its entity type (diagnosis, procedure, etc.) along with associated medical codes from appropriate vocabularies (ICD-10, CPT, LOINC, RxNorm, ATC).")
async def analyze_entity(request: EntityRequest):
    """
    Analyze a medical concept and return its entity type and associated codes.
    
    Args:
        request (EntityRequest): The request containing the concept name to analyze
        
    Returns:
        EntityResponse: The response containing the entity type and associated codes
        
    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        # Get the initial response from the LLM
        response = await get_single_response(request.concept_name)
        
        if isinstance(response, dict):
            result = response
        else:
            cleaned_response = strip_markdown_fences(response)
            result = json.loads(cleaned_response)
        
        # Check if there are any entities in the result
        if not result.get('entities') or len(result.get('entities', {})) == 0:
            # Return an empty, properly structured response
            return {"entities": {}}
        
        return result
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error parsing LLM response: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """
    Health check endpoint to verify the API and MongoDB are running.
    """
    try:
        # Check MongoDB connection
        await db.command("ping")
        return {"status": "healthy", "mongodb": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e)) 