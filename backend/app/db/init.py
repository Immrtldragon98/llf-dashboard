from sqlalchemy import text
from passlib.context import CryptContext
from app.db.session import engine

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

DEFAULT_LINES = [
    ("CH2-WRM1", "WRM1"),
    ("CH2-WRM2", "WRM2"),
    ("CH2-WRM3", "WRM3"),
    ("CH2-PFA2", "PFA2"),
]

DEFAULT_EQUIPMENT_TYPES = ["Degasser", "Dam Cylinder"]

DEFAULT_PARAMETERS = {
    "Degasser": [
        ("manifold_flow_distribution","Degasser manifold flow distribution","status",None,"OK,NOT OK"),
        ("high_low_flow_condition","High flow / Low flow condition","status",None,"OK,NOT OK"),
        ("exhaust_condition","Exhaust condition","status",None,"OK,NOT OK"),
        ("bowl_condition","Degasser bowl condition","status",None,"OK,NOT OK"),
        ("baffle_plate_condition","Degasser baffle plate condition","status",None,"OK,NOT OK"),
        ("stop_when_flow_stops","Degasser should stop when flow stops","status",None,"YES,NO"),
        ("shaft_vibration_issue","Degasser shaft vibration issue","status",None,"YES,NO"),
        ("metal_level","Degasser metal level","number","mm",None),
    ],
    "Dam Cylinder": [
        ("cff_bowl_condition","CFF bowl condition","status",None,"OK,NOT OK"),
        ("cff_baffle_plate","CFF baffle plate","status",None,"OK,NOT OK"),
        ("cff_drain_point_hole","CFF drain point hole","status",None,"OK,NOT OK"),
        ("cff_dam_cylinder","CFF dam cylinder","status",None,"OK,NOT OK"),
    ],
}

def init_db():
    with engine.begin() as c:
        c.execute(text("""CREATE TABLE IF NOT EXISTS users(
            id SERIAL PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL CHECK(role IN ('operator','admin','viewer')),
            active BOOLEAN NOT NULL DEFAULT TRUE
        )"""))
        c.execute(text("""CREATE TABLE IF NOT EXISTS lines(
            id SERIAL PRIMARY KEY,
            code VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(120) NOT NULL,
            active BOOLEAN NOT NULL DEFAULT TRUE
        )"""))
        c.execute(text("""CREATE TABLE IF NOT EXISTS equipment(
            id SERIAL PRIMARY KEY,
            asset_id VARCHAR(120) UNIQUE NOT NULL,
            line_id INTEGER NOT NULL REFERENCES lines(id),
            name VARCHAR(120) NOT NULL,
            active BOOLEAN NOT NULL DEFAULT TRUE
        )"""))
        c.execute(text("""CREATE TABLE IF NOT EXISTS parameters(
            id SERIAL PRIMARY KEY,
            parameter_key VARCHAR(120) UNIQUE NOT NULL,
            parameter_name VARCHAR(200) NOT NULL,
            parameter_type VARCHAR(20) NOT NULL CHECK(parameter_type IN ('status','number','boolean','text')),
            unit VARCHAR(30),
            active BOOLEAN NOT NULL DEFAULT TRUE
        )"""))
        c.execute(text("""CREATE TABLE IF NOT EXISTS equipment_parameters(
            id SERIAL PRIMARY KEY,
            equipment_id INTEGER NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
            parameter_id INTEGER NOT NULL REFERENCES parameters(id),
            display_order INTEGER NOT NULL DEFAULT 0,
            required BOOLEAN NOT NULL DEFAULT TRUE,
            options_csv VARCHAR(255),
            min_value NUMERIC,
            max_value NUMERIC,
            active BOOLEAN NOT NULL DEFAULT TRUE,
            UNIQUE(equipment_id, parameter_id)
        )"""))
        c.execute(text("""CREATE TABLE IF NOT EXISTS shift_records(
            id SERIAL PRIMARY KEY,
            equipment_id INTEGER NOT NULL REFERENCES equipment(id),
            shift VARCHAR(1) NOT NULL CHECK(shift IN ('A','B','C')),
            record_date DATE NOT NULL,
            entered_by INTEGER NOT NULL REFERENCES users(id),
            remarks TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(equipment_id, record_date, shift)
        )"""))
        c.execute(text("""CREATE TABLE IF NOT EXISTS readings(
            id SERIAL PRIMARY KEY,
            record_id INTEGER NOT NULL REFERENCES shift_records(id) ON DELETE CASCADE,
            parameter_id INTEGER NOT NULL REFERENCES parameters(id),
            value_numeric NUMERIC,
            value_text TEXT,
            value_status VARCHAR(120),
            UNIQUE(record_id, parameter_id)
        )"""))
        if c.execute(text("SELECT COUNT(*) FROM users")).scalar_one() == 0:
            for u,p,r in [("admin","admin123","admin"),("operator","operator123","operator"),("viewer","viewer123","viewer")]:
                c.execute(text("INSERT INTO users(username,password_hash,role) VALUES(:u,:p,:r)"),
                          {"u":u,"p":pwd.hash(p),"r":r})
        if c.execute(text("SELECT COUNT(*) FROM lines")).scalar_one() == 0:
            for code,name in DEFAULT_LINES:
                c.execute(text("INSERT INTO lines(code,name) VALUES(:c,:n)"), {"c":code,"n":name})
        if c.execute(text("SELECT COUNT(*) FROM equipment")).scalar_one() == 0:
            for code,_ in DEFAULT_LINES:
                line_id = c.execute(text("SELECT id FROM lines WHERE code=:c"), {"c":code}).scalar_one()
                for eq_name in DEFAULT_EQUIPMENT_TYPES:
                    asset_id = f"{code}-{eq_name.replace(' ','-')}"
                    c.execute(text("INSERT INTO equipment(asset_id,line_id,name) VALUES(:a,:l,:n)"),
                              {"a":asset_id,"l":line_id,"n":eq_name})
        if c.execute(text("SELECT COUNT(*) FROM parameters")).scalar_one() == 0:
            for eq_name, plist in DEFAULT_PARAMETERS.items():
                for key,name,ptype,unit,_ in plist:
                    existing = c.execute(text("SELECT id FROM parameters WHERE parameter_key=:k"), {"k":key}).fetchone()
                    if not existing:
                        c.execute(text("""INSERT INTO parameters(parameter_key,parameter_name,parameter_type,unit)
                                        VALUES(:k,:n,:t,:u)"""),
                                  {"k":key,"n":name,"t":ptype,"u":unit})
        if c.execute(text("SELECT COUNT(*) FROM equipment_parameters")).scalar_one() == 0:
            for eq_name, plist in DEFAULT_PARAMETERS.items():
                eq_rows = c.execute(text("SELECT id FROM equipment WHERE name=:n"), {"n":eq_name}).fetchall()
                for eq_row in eq_rows:
                    for order,(key,_,_,_,options) in enumerate(plist, start=1):
                        pid = c.execute(text("SELECT id FROM parameters WHERE parameter_key=:k"), {"k":key}).scalar_one()
                        c.execute(text("""INSERT INTO equipment_parameters
                            (equipment_id,parameter_id,display_order,required,options_csv)
                            VALUES(:e,:p,:o,TRUE,:opts)"""),
                            {"e":eq_row[0],"p":pid,"o":order,"opts":options})
