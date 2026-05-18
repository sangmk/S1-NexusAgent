from typing import List,Tuple
from enum import Enum
from pydantic import BaseModel, Field, model_validator
from typing import Any

class ActionType(str, Enum):
    FINISH = "finish"
    CALL_EXECUTOR = "call_executor"

class Node(BaseModel):
    content: str

    @model_validator(mode="before")
    @classmethod
    def coerce_str_to_obj(cls, v: Any) -> Any:
        if isinstance(v, str):
            return {"content": v}
        return v

class UnknownPlan(BaseModel):
    node_id: int = Field(..., description="The id of the node")
    nodes: List[Node] = Field(default_factory=list)
    action: ActionType = Field(...)
    subtask: str = Field(...)
    information: str = Field(...)
    expected_output: str = Field(...)
    reasoning: str = Field(...)