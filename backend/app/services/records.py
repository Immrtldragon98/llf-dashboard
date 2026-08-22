from fastapi import HTTPException
from app.repositories.records import existing_record, create_record, insert_reading
from app.repositories.equipment import list_parameters_for_equipment

def save_shift(payload, user):
    if user["role"] == "viewer":
        raise HTTPException(403, "Viewer cannot enter data")
    if existing_record(payload.equipment_id, payload.record_date, payload.shift):
        raise HTTPException(409, "This equipment already has data for this shift and date.")

    parameter_defs = {p["parameter_id"]: p for p in list_parameters_for_equipment(payload.equipment_id)}
    submitted = {r.parameter_id: r.value for r in payload.readings}

    missing = [p["name"] for p in parameter_defs.values()
               if p["required"] and (p["parameter_id"] not in submitted or not str(submitted[p["parameter_id"]]).strip())]
    if missing:
        raise HTTPException(400, f"Complete all required parameters. Missing: {', '.join(missing[:5])}")

    abnormal = []
    for pid,value in submitted.items():
        p = parameter_defs.get(pid)
        if not p:
            raise HTTPException(400, f"Parameter {pid} is not assigned to this equipment")
        if p["type"] in ("status","boolean") and str(value).upper() in {"NOT OK","NO"}:
            abnormal.append(p["name"])
        if p["type"] == "number":
            try:
                n = float(value)
            except ValueError:
                raise HTTPException(400, f"{p['name']} must be numeric")
            if p["min_value"] is not None and n < float(p["min_value"]):
                abnormal.append(p["name"])
            if p["max_value"] is not None and n > float(p["max_value"]):
                abnormal.append(p["name"])

    if abnormal and not (payload.remarks or "").strip():
        raise HTTPException(400, "Remarks are required for abnormal readings.")

    rid = create_record(payload.equipment_id, payload.record_date, payload.shift, user["id"], payload.remarks)
    for pid,value in submitted.items():
        insert_reading(rid, pid, parameter_defs[pid]["type"], value)
    return {"id":rid,"status":"saved"}
