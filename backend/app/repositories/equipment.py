from sqlalchemy import text
from app.db.session import engine

def list_equipment():
    with engine.begin() as c:
        rows = c.execute(text("""SELECT e.id,e.asset_id,l.code AS line,e.name
                               FROM equipment e
                               JOIN lines l ON l.id=e.line_id
                               WHERE e.active=TRUE AND l.active=TRUE
                               ORDER BY l.code,e.name""")).mappings().all()
    return [dict(r) for r in rows]

def list_parameters_for_equipment(equipment_id: int):
    with engine.begin() as c:
        rows = c.execute(text("""SELECT
            p.id AS parameter_id,
            p.parameter_key AS key,
            p.parameter_name AS name,
            p.parameter_type AS type,
            p.unit,
            ep.required,
            ep.options_csv,
            ep.min_value,
            ep.max_value,
            ep.display_order
        FROM equipment_parameters ep
        JOIN parameters p ON p.id=ep.parameter_id
        WHERE ep.equipment_id=:e AND ep.active=TRUE AND p.active=TRUE
        ORDER BY ep.display_order,p.id"""), {"e":equipment_id}).mappings().all()
    result=[]
    for r in rows:
        d=dict(r)
        d["options"]=d.pop("options_csv").split(",") if d["options_csv"] else None
        result.append(d)
    return result
