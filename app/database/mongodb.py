from motor.motor_asyncio import AsyncIOMotorClient

MONGO_DETAILS = "mongodb://localhost:27017" # default connection string

client = AsyncIOMotorClient(MONGO_DETAILS)

database = client.gdg_db # your database name
user_collection = database.get_collection("users") # uers collection
event_collection = database.get_collection("events")# events collection
registration_collection = database.get_collection("registrations") # new registrations collection

def get_database():
    if database is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    return database