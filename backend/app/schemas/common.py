from datetime import date
from typing import Optional, Literal
from pydantic import BaseModel, Field

Role = Literal["admin","operator","viewer"]
ParameterType = Literal["status","number","boolean","text"]

class LoginIn(BaseModel):
    username: str
    password: str

class UserCreateIn(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=8, max_length=128)
    role: Role

class ReadingIn(BaseModel):
    parameter_id: int
    value: str

class ShiftSaveIn(BaseModel):
    equipment_id: int
    shift: str = Field(pattern="^[ABC]$")
    record_date: date
    remarks: Optional[str] = None
    readings: list[ReadingIn]

class EquipmentCreateIn(BaseModel):
    asset_id: str
    line_code: str
    name: str

class ParameterCreateIn(BaseModel):
    parameter_key: str
    parameter_name: str
    parameter_type: ParameterType
    unit: Optional[str] = None

class EquipmentParameterCreateIn(BaseModel):
    equipment_id: int
    parameter_id: int
    display_order: int = 0
    required: bool = True
    options: Optional[list[str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None

class EquipmentParameterCreateFullIn(BaseModel):
    parameter_key: str
    parameter_name: str
    parameter_type: ParameterType
    unit: Optional[str] = None
    display_order: int = 0
    required: bool = True
    options: Optional[list[str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
