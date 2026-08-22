import io
from datetime import date
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from app.core.security import current_user
from app.api.records import list_shift_records

router=APIRouter(prefix="/api",tags=["reports"])

@router.get("/export.xlsx")
def export_excel(
    equipment_id:int|None=None,
    shift:str|None=Query(None,pattern="^[ABC]$"),
    start_date:date|None=None,
    end_date:date|None=None,
    user=Depends(current_user)
):
    rows=list_shift_records(equipment_id,shift,start_date,end_date,user)
    if not rows:
        raise HTTPException(404,"No data found for export.")
    df=pd.DataFrame(rows)
    out=io.BytesIO()
    with pd.ExcelWriter(out,engine="openpyxl") as writer:
        df.to_excel(writer,index=False,sheet_name="Data")
        summary=(df.groupby(["record_date","line","equipment_name","asset_id","shift"])
                   .agg(readings=("parameter_name","count"),
                        entered_by=("entered_by","first"),
                        remarks=("remarks","first")).reset_index())
        summary.to_excel(writer,index=False,sheet_name="Shift Summary")
        pivot=df.pivot_table(
            index=["record_date","shift","line","equipment_name","asset_id"],
            columns="parameter_name",values="value",aggfunc="first"
        ).reset_index()
        pivot.to_excel(writer,index=False,sheet_name="Parameter Matrix")
        for sheet in writer.book.worksheets:
            sheet.freeze_panes="A2"
            sheet.auto_filter.ref=sheet.dimensions
            for col in sheet.columns:
                max_len=max(len(str(cell.value or "")) for cell in col)
                sheet.column_dimensions[col[0].column_letter].width=min(max(max_len+2,10),45)
    out.seek(0)
    return StreamingResponse(out,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition":'attachment; filename="LLF_equipment_data.xlsx"'})
