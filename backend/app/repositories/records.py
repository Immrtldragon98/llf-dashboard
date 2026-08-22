from datetime import date
from decimal import Decimal
from sqlalchemy import text
from app.db.session import engine

def existing_record(equipment_id:int, record_date:date, shift:str):
    with engine.begin() as c:
        return c.execute(text("""SELECT id FROM shift_records
                               WHERE equipment_id=:e AND record_date=:d AND shift=:s"""),
                         {"e":equipment_id,"d":record_date,"s":shift}).fetchone()

def create_record(equipment_id:int, record_date:date, shift:str, user_id:int, remarks:str|None):
    with engine.begin() as c:
        return c.execute(text("""INSERT INTO shift_records(equipment_id,shift,record_date,entered_by,remarks)
                               VALUES(:e,:s,:d,:u,:r) RETURNING id"""),
                         {"e":equipment_id,"s":shift,"d":record_date,"u":user_id,"r":remarks}).scalar_one()

def insert_reading(record_id:int, parameter_id:int, parameter_type:str, value:str):
    numeric = Decimal(value) if parameter_type=="number" else None
    text_value = value if parameter_type=="text" else None
    status = value if parameter_type in ("status","boolean") else None
    with engine.begin() as c:
        c.execute(text("""INSERT INTO readings(record_id,parameter_id,value_numeric,value_text,value_status)
                        VALUES(:r,:p,:n,:t,:s)"""),
                  {"r":record_id,"p":parameter_id,"n":numeric,"t":text_value,"s":status})
