from typing import List,Tuple
from enum import Enum
from pydantic import BaseModel, Field, model_validator
from typing import Any

class Node(BaseModel):
    content: str

    @model_validator(mode="before")
    @classmethod
    def coerce_str_to_obj(cls, v: Any) -> Any:
        if isinstance(v, str):
            return {"content": v}
        return v

class PrePlan(BaseModel):
    node_id: int = Field(..., description="The id of the node")
    nodes: List[Node] = Field(default_factory=list)