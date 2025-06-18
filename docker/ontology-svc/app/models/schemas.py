from pydantic import BaseModel
from typing import List, Dict

class EntityRequest(BaseModel):
    concept_name: str

class Code(BaseModel):
    code: str
    system: str
    description: str
    confidence: int

class Entity(BaseModel):
    entity_name: str
    types: str
    codes: List[Code]

class EntityResponse(BaseModel):
    entities: Dict[str, Entity] 