from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from app.core.security import current_user
from app.db.session import engine
from app.schemas.common import ShiftSaveIn
from app.services.records import save_shift

router = APIRouter(prefix="/api", tags=["records"])

@router.post("/shift-records")
def create_shift_record(payload: ShiftSaveIn, user=Depends(current_user)):
    return save_shift(payload, user)

@router.get("/shift-records")
def list_shift_records(
    equipment_id:int|None=None,
    shift:str|None=Query(None, pattern="^[ABC]$"),
    start_date:date|None=None,
    end_date:date|None=None,
    user=Depends(current_user)
):
    q=[]; p={}
    if equipment_id is not None:
        q.append("e.id=:equipment_id"); p["equipment_id"]=equipment_id
    if shift:
        q.append("sr.shift=:shift"); p["shift"]=shift
    if start_date:
        q.append("sr.record_date>=:start_date"); p["start_date"]=start_date
    if end_date:
        q.append("sr.record_date<=:end_date"); p["end_date"]=end_date
    where=(" WHERE "+" AND ".join(q)) if q else ""
    sql=f"""SELECT
        sr.id AS record_id,sr.record_date,sr.shift,sr.remarks,sr.created_at,
        e.id AS equipment_id,e.asset_id,e.name AS equipment_name,
        l.code AS line,u.username AS entered_by,
        p.parameter_name,p.parameter_type,p.unit,
        COALESCE(r.value_status,r.value_text,CAST(r.value_numeric AS TEXT)) AS value
    FROM shift_records sr
    JOIN equipment e ON e.id=sr.equipment_id
    JOIN lines l ON l.id=e.line_id
    JOIN users u ON u.id=sr.entered_by
    JOIN readings r ON r.record_id=sr.id
    JOIN parameters p ON p.id=r.parameter_id
    {where}
    ORDER BY sr.record_date DESC,sr.shift,r.id"""
    with engine.begin() as c:
        rows=c.execute(text(sql),p).mappings().all()
    return [dict(x) for x in rows]

@router.get("/completion")
def completion(record_date:date,line:str|None=None,user=Depends(current_user)):
    params={"d":record_date}
    line_clause=""
    if line:
        line_clause=" AND l.code=:line"
        params["line"]=line
    with engine.begin() as c:
        eqs=c.execute(text(f"""SELECT e.id,e.asset_id,e.name,l.code AS line
                              FROM equipment e JOIN lines l ON l.id=e.line_id
                              WHERE e.active=TRUE AND l.active=TRUE {line_clause}
                              ORDER BY l.code,e.name"""),params).mappings().all()
        done=c.execute(text("SELECT equipment_id,shift FROM shift_records WHERE record_date=:d"),
                       {"d":record_date}).mappings().all()
    completed={(r["equipment_id"],r["shift"]) for r in done}
    return [{**dict(e),"shifts":{s:(e["id"],s) in completed for s in "ABC"},
             "completed_count":sum(1 for s in "ABC" if (e["id"],s) in completed)} for e in eqs]
