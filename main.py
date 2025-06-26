from fastapi import FastAPI, Request,Depends
from zk import ZK
from dotenv import load_dotenv
import os
import logging
from fastapi.responses import JSONResponse
from database import Base
from sqlalchemy import column, Integer, String,text
from database import SessionLocal
from sqlalchemy.orm import Session
from datetime import datetime

# --- Load Environment Variables ---
load_dotenv()
ip = os.getenv("BIOMETRIC_IP_1")
ip_2 = os.getenv("BIOMETRIC_IP_2")
port = os.getenv("BIOMETRIC_PORT")

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- FastAPI App ---
app = FastAPI()

# --- Global Exception Handler ---


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled Exception at {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# --- Routes ---


@app.get("/")
def read_root():
    logger.info("Health check: IP and port read")
    return {"ip": ip, "port": port}



    """
    for fetching all registered users finger prints we use the following get_templates method
    fingerprints = conn.get_templates()
    
    conn.set_user(uid=1, name='John Doe', privilege=0, password='1234', user_id='12014')

    conn.delete_user(uid=1)

    conn.restart()

    
    conn.poweroff()
conn.enable_device()
conn.disable_device()


conn.clear_attendance()
conn.clear_users()

-> get device information
print(conn.get_device_name())
print(conn.get_firmware_version())
print(conn.get_platform())
print(conn.get_serialnumber())

    """

@app.get("/get_attendance")
def get_employees_attendance():
    conn = None
    try:
        # logger.info("Connecting to device to fetch attendance...")
        first_machine=call_biometric_machines(ip, port)
        second_machine=call_biometric_machines(ip_2, port)
        return {"first_machine_attendance": first_machine["attendance"], "second_machine_attendance": second_machine["attendance"]}
    except Exception as e:
        logger.error("Error while fetching attendance", exc_info=True)
        return {"error": str(e)}
    finally:
        if conn:
            conn.enable_device()
            conn.disconnect()
            logger.info("Disconnected from device")

@staticmethod
def call_biometric_machines(ip,port):
    conn = None
    try:
        # logger.info("Connecting to device to fetch attendance...")
        zk = ZK(ip, port=int(port), timeout=5)
        conn = zk.connect()
        conn.disable_device()
        attendance = conn.get_attendance()
        store_in_db(attendance)
        logger.info("Attendance records fetched successfully")
        return {"attendance": attendance}
    except Exception as e:
        logger.error("Error while fetching attendance", exc_info=True)
        return {"error": str(e)}
    finally:
        if conn:
            conn.enable_device()
            conn.disconnect()
            logger.info("Disconnected from device")

# Dependency to get DB session


def store_in_db(attendance):
    db: Session = SessionLocal()
    try:
        for record in attendance:
            new_record = vars(record)
            timestamp_dt = new_record["timestamp"]
            if isinstance(timestamp_dt, str):
                timestamp_dt = datetime.strptime(
                    timestamp_dt, "%Y-%m-%d %H:%M:%S")

            # Check if a record already exists for this user and *exact timestamp*
            check_sql = text("""
                SELECT 1 FROM attendance 
                WHERE user_id = :user_id AND timestamp = :timestamp
                LIMIT 1
            """)
            result = db.execute(check_sql, {
                "user_id": new_record["user_id"],
                "timestamp": timestamp_dt,
            }).first()

            # If exact timestamp exists, skip to next
            if result:
                logger.info(
                    f"Duplicate entry skipped for user {new_record['user_id']} at {timestamp_dt}")
                continue

            # Determine status based on existing entries today
            check_today_sql = text("""
                SELECT COUNT(*) as count FROM attendance
                WHERE user_id = :user_id AND DATE(timestamp) = :date_only
            """)
            date_only = timestamp_dt.date().isoformat()
            result = db.execute(check_today_sql, {
                "user_id": new_record["user_id"],
                "date_only": date_only,
            }).first()
            count_today = result[0] if result else 0

            status = 'Checked In' if count_today == 0 else 'Checked Out'

            # Insert the new record
            insert_sql = text("""
                INSERT INTO attendance (uid, user_id, timestamp, status, punch)
                VALUES (:uid, :user_id, :timestamp, :status, :punch)
            """)
            db.execute(insert_sql, {
                "uid": new_record["uid"],
                "user_id": new_record["user_id"],
                "timestamp": timestamp_dt,
                "status": status,
                "punch": new_record["punch"]
            })

        db.commit()
        logger.info("Attendance records stored in database successfully")
    except Exception as e:
        db.rollback()
        logger.error(
            "Error while storing attendance in database", exc_info=True)
    finally:
        db.close()
        
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
@app.get("/users")
def get_users_db(db: Session = Depends(get_db)):
    sql = text("SELECT user_id, name FROM users")
    result = db.execute(sql)
    users = []
    for row in result:
        users.append({"user_id": row.user_id, "name": row.name})
    return users
    
    

@app.get("/get_users")
def get_users():
    conn = None
    try:
        logger.info("Connecting to device to fetch users...")
        zk = ZK(ip, port=int(port), timeout=5)
        conn = zk.connect()
        conn.disable_device()
        users = conn.get_users()
        logger.info("User records fetched successfully")
        return {"users": users}
    except Exception as e:
        logger.error("Error while fetching users", exc_info=True)
        return {"error": str(e)}
    finally:
        if conn:
            conn.enable_device()
            conn.disconnect()
            logger.info("Disconnected from device")
