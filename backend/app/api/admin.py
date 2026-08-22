from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from app.core.security import admin_only, pwd
from app.db.session import engine
from app.schemas.common import (
    EquipmentCreateIn,
    ParameterCreateIn,
    EquipmentParameterCreateIn,
    EquipmentParameterCreateFullIn,
    UserCreateIn,
)

router=APIRouter(prefix="/api/admin",tags=["admin"])

@router.get("/users")
def list_users(user=Depends(admin_only)):
    with engine.begin() as c:
        rows=c.execute(text("SELECT id,username,role,active FROM users ORDER BY username")).mappings().all()
    return [dict(r) for r in rows]

@router.post("/users")
def create_user(payload:UserCreateIn,user=Depends(admin_only)):
    try:
        with engine.begin() as c:
            uid=c.execute(text("""INSERT INTO users(username,password_hash,role,active)
                                VALUES(:u,:p,:r,TRUE) RETURNING id"""),
                          {"u":payload.username.strip(),"p":pwd.hash(payload.password),"r":payload.role}).scalar_one()
    except Exception:
        raise HTTPException(409,"Username already exists")
    return {"id":uid,"status":"created"}

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

@router.post("/equipment/{equipment_id}/parameters")
def create_and_assign_parameter(equipment_id:int,payload:EquipmentParameterCreateFullIn,user=Depends(admin_only)):
    with engine.begin() as c:
        exists=c.execute(text("SELECT id FROM equipment WHERE id=:e AND active=TRUE"),{"e":equipment_id}).scalar()
        if not exists:
            raise HTTPException(404,"Equipment not found")

        parameter_id=c.execute(text("SELECT id FROM parameters WHERE parameter_key=:k"),{"k":payload.parameter_key}).scalar()
        if not parameter_id:
            parameter_id=c.execute(text("""INSERT INTO parameters
                (parameter_key,parameter_name,parameter_type,unit)
                VALUES(:k,:n,:t,:u) RETURNING id"""),
                {"k":payload.parameter_key,"n":payload.parameter_name,
                 "t":payload.parameter_type,"u":payload.unit}).scalar_one()

        duplicate=c.execute(text("""SELECT id FROM equipment_parameters
            WHERE equipment_id=:e AND parameter_id=:p"""),
            {"e":equipment_id,"p":parameter_id}).scalar()
        if duplicate:
            raise HTTPException(409,"This parameter is already assigned to the equipment")

        ep_id=c.execute(text("""INSERT INTO equipment_parameters
            (equipment_id,parameter_id,display_order,required,options_csv,min_value,max_value)
            VALUES(:e,:p,:o,:r,:opts,:min,:max) RETURNING id"""),
            {"e":equipment_id,"p":parameter_id,"o":payload.display_order,
             "r":payload.required,"opts":",".join(payload.options) if payload.options else None,
             "min":payload.min_value,"max":payload.max_value}).scalar_one()

    return {"id":ep_id,"parameter_id":parameter_id,"status":"created_and_assigned"}
