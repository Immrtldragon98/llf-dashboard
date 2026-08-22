from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from app.core.security import admin_only
from app.db.session import engine
from app.schemas.common import EquipmentCreateIn, ParameterCreateIn, EquipmentParameterCreateIn

router=APIRouter(prefix="/api/admin",tags=["admin"])

@router.post("/equipment")
def add_equipment(payload:EquipmentCreateIn,user=Depends(admin_only)):
    with engine.begin() as c:
        line_id=c.execute(text("SELECT id FROM lines WHERE code=:c"),{"c":payload.line_code}).scalar()
        if not line_id:
            raise HTTPException(400,"Unknown line code")
        try:
            eid=c.execute(text("""INSERT INTO equipment(asset_id,line_id,name)
                                VALUES(:a,:l,:n) RETURNING id"""),
                          {"a":payload.asset_id,"l":line_id,"n":payload.name}).scalar_one()
        except Exception:
            raise HTTPException(409,"Equipment asset ID already exists")
    return {"id":eid,"status":"created"}

@router.post("/parameters")
def add_parameter(payload:ParameterCreateIn,user=Depends(admin_only)):
    try:
        with engine.begin() as c:
            pid=c.execute(text("""INSERT INTO parameters(parameter_key,parameter_name,parameter_type,unit)
                                VALUES(:k,:n,:t,:u) RETURNING id"""),
                          {"k":payload.parameter_key,"n":payload.parameter_name,
                           "t":payload.parameter_type,"u":payload.unit}).scalar_one()
    except Exception:
        raise HTTPException(409,"Parameter key already exists")
    return {"id":pid,"status":"created"}

@router.post("/equipment-parameters")
def assign_parameter(payload:EquipmentParameterCreateIn,user=Depends(admin_only)):
    try:
        with engine.begin() as c:
            ep=c.execute(text("""INSERT INTO equipment_parameters
                (equipment_id,parameter_id,display_order,required,options_csv,min_value,max_value)
                VALUES(:e,:p,:o,:r,:opts,:min,:max) RETURNING id"""),
                {"e":payload.equipment_id,"p":payload.parameter_id,"o":payload.display_order,
                 "r":payload.required,"opts":",".join(payload.options) if payload.options else None,
                 "min":payload.min_value,"max":payload.max_value}).scalar_one()
    except Exception:
        raise HTTPException(409,"Parameter already assigned or invalid IDs")
    return {"id":ep,"status":"assigned"}
