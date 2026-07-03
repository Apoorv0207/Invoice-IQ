from pydantic import BaseModel, Field
from typing import Optional, List


class GLCode(BaseModel):
    code: str
    description: str
    category: str
    keywords: List[str] = []
    embedding: Optional[List[float]] = None  # stored in MongoDB after seeding

    class Config:
        populate_by_name = True
