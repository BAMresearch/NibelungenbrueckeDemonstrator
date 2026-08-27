# schemas.py
from pydantic import BaseModel
from typing import Any

class ComputationRequest(BaseModel):
    parameter1: any
    parameter2: any
    # Add more parameters as required by your model

class ComputationResponse(BaseModel):
    result: any
    # Add more fields to match the output of your model
