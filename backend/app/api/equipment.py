from fastapi import APIRouter, Depends
from app.core.security import current_user
from app.repositories.equipment import list_equipment, list_parameters_for_equipment

router = APIRouter(prefix="/api", tags=["equipment"])

@router.get("/equipment")
def equipment(user=Depends(current_user)):
    return list_equipment()

@router.get("/equipment/{equipment_id}/parameters")
def equipment_parameters(equipment_id:int, user=Depends(current_user)):
    return list_parameters_for_equipment(equipment_id)
