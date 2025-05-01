from fastapi import FastAPI, HTTPException, Depends, status,APIRouter
from fastapi.security import OAuth2PasswordBearer
from bson import ObjectId
from app.database.mongodb import user_collection, event_collection, registration_collection,get_database
from app.auth.jwt_handler import create_access_token, decode_access_token
from app.auth.jwt_bearer import JWTBearer
from app.schemas.user_schema import UserRegisterSchema, UserLoginSchema
from app.schemas.event_schema import EventCreateSchema
import uuid
import qrcode
# import qrcode
from io import BytesIO
from fastapi import APIRouter
from fastapi.responses import StreamingResponse,FileResponse
from datetime import datetime
import io
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
import jwt
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime

# import base64
# from io import BytesIO
# import qrcode
# from fastapi import HTTPException





app = FastAPI()

# OAuth2 Dependency for current user
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_access_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        return payload
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

@app.post("/register")
async def register_user(user_data: UserRegisterSchema):
    # Check if user already exists
    existing_user = await user_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists.")

    # Create the new user and insert into the database
    user = {
        "email": user_data.email,
        "password": user_data.password,  # You should hash the password before saving it in real applications
        "name": user_data.name,
        "student_id": user_data.student_id
    }

    try:
        result = await user_collection.insert_one(user)
        return {"message": "User registered successfully!", "user_id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registering user: {str(e)}")

@app.post("/login")
async def login_user(user_data: UserLoginSchema):
    # Check if user exists
    user = await user_collection.find_one({"email": user_data.email})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Verify password (in a real application, you should hash and compare the password)
    if user["password"] != user_data.password:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Create and return JWT token
    token = create_access_token(data={"user_id": str(user["_id"]), "email": user["email"]})
    return {"access_token": token, "token_type": "bearer"}


@app.post("/events")
async def create_event(event: EventCreateSchema):
    # Prepare event data to be inserted
    event_data = {
        "name": event.name,
        "date": event.date,
        "location": event.location,
        "description": event.description
    }

    # Insert the event data into the MongoDB event collection
    try:
        result = await event_collection.insert_one(event_data)
        event_id = str(result.inserted_id)  # Get the ObjectId from the result
        return {"message": "Event created successfully!", "event_id": event_id }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating event: {str(e)}")
    
@app.get("/events")
async def get_all_events():
    # Fetch all events from the database
    events = await event_collection.find().to_list(100)  # Fetching up to 100 events

    # Convert ObjectId to string and return the events
    return {"events": [
        {"event_id": str(event["_id"]),  # Convert ObjectId to string
         "name": event["name"],
         "date": event["date"],
         "location": event["location"],
         "description": event["description"]}
        for event in events
    ]}


# @app.post("/events/{event_id}/register")
# async def register_for_event(event_id: str, user: dict = Depends(get_current_user)):
#     # 1. Check if event_id is a valid ObjectId
#     try:
#         event_id_obj = ObjectId(event_id)
#     except Exception:
#         raise HTTPException(status_code=400, detail="Invalid event_id format")

#     # 2. Check if event exists
#     event = await event_collection.find_one({"_id": event_id_obj})
#     if not event:
#         raise HTTPException(status_code=404, detail="Event not found.")

#     # 3. Check if user is already registered for the event
#     existing = await registration_collection.find_one({
#         "event_id": event_id,
#         "student_id": str(user["user_id"])   # <-- Fix here
#     })
#     if existing:
#         raise HTTPException(status_code=400, detail="Already registered for this event.")

#     # 4. Save new registration
#     registration = {
#         "event_id": event_id,
#         "student_id": str(user["user_id"]),  # <-- Fix here
#         "email": user["email"]
#     }
#     await registration_collection.insert_one(registration)

#     return {"message": "Successfully registered for the event!"}, status.HTTP_201_CREATED


# def generate_qr_code(event_id: str,student_id: str):
#     # The data we want to encode in the QR code (event URL or event ID)
    
#     # Combine student_id and event_id in the URL
#     data = f"http://localhost:8000/events/{event_id}/qr?student_id={student_id}"
    
#     qr = qrcode.make(data)

#     img_byte_arr = BytesIO()
#     qr.save(img_byte_arr)
#     img_byte_arr.seek(0)  # Rewind the BytesIO object to the start
#     return img_byte_arr  # You can use the appropriate event URL or event_id
    
def generate_qr_code(event_id: str, student_id: str):
    # Combine student_id and event_id in the format student_id:event_id
    data = f"{student_id}:{event_id}"
    
    # Generate the QR code for the data
    qr = qrcode.make(data)
    
    # Save the QR code to a BytesIO object
    img_byte_arr = BytesIO()
    qr.save(img_byte_arr)
    img_byte_arr.seek(0)  # Rewind the BytesIO object to the start
    
    return img_byte_arr


@app.post("/events/{event_id}/register")
async def register_for_event(event_id: str, user: dict = Depends(get_current_user)):
    # 1. Check if event_id is a valid ObjectId
    try:
        event_id_obj = ObjectId(event_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid event_id format")

    # 2. Check if event exists
    event = await event_collection.find_one({"_id": event_id_obj})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")

    # 3. Check if user is already registered for the event
    existing_registration = await registration_collection.find_one({
        "event_id": event_id_obj,
        "student_id": str(user["user_id"])  # Use the user ID from the JWT token
    })
    
    if existing_registration:
        raise HTTPException(status_code=400, detail="Already registered for this event.")

    # 4. Save new registration
    registration = {
        "event_id": event_id_obj,
        "student_id": str(user["user_id"]),  # Ensure to use the user ID from the token
        "email": user["email"]
    }

    try:
        result = await registration_collection.insert_one(registration)
        registration_id = str(result.inserted_id)
        img_byte_arr = generate_qr_code(event_id, str(user["user_id"]))
        img_byte_arr.seek(0)  # Rewind the BytesIO object
        img_base64 = base64.b64encode(img_byte_arr.read()).decode("utf-8")
        return {"message": "Successfully registered for the event!", "registration_id": str(result.inserted_id),"qr_code_base64": img_base64}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registering for event: {str(e)}")



# Endpoint to get the QR code for an event

@app.get("/events/{event_id}/qr")
async def get_event_qr(event_id: str, student_id: str):
    # Generate the QR code for the given event_id and student_id
    img = generate_qr_code(event_id, student_id)
    
    # Return the image as a streaming response
    return StreamingResponse(img, media_type="image/png")




@app.get("/download_qr/{event_id}")
async def download_qr(event_id: str):
    try:
        # Generate the QR code for the event_id
        qr = qrcode.make(event_id)

        # Save the QR code to a BytesIO object (in-memory)
        img_io = io.BytesIO()
        qr.save(img_io, format='PNG')
        img_io.seek(0)  # Move the cursor to the beginning of the BytesIO object

        # Return the QR code image as a downloadable file
        return StreamingResponse(img_io, media_type="image/png", headers={"Content-Disposition": f"attachment; filename={event_id}_qr.png"})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating QR code: {str(e)}")

# cfrom pydantic import BaseModel

# Request Body Model
class CheckInRequest(BaseModel):
    student_id: str

@app.post("/check_in/{event_id}")
async def check_in(event_id: str, check_in_data: CheckInRequest):
    # Convert string event_id to ObjectId
    try:
        event_id_obj = ObjectId(event_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid event_id format")
    
    # Check if the event exists
    event = await event_collection.find_one({"_id": event_id_obj})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Find the user in the event's attendance list
    user = await user_collection.find_one({"student_id": check_in_data.student_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Mark the user as checked-in
    check_in_entry = {
        "student_id": check_in_data.student_id,
        "checked_in": True,
        "event_id": event_id,
        # "timestamp": datetime.datetime.now()
    }

    try:
        # Update the event document by pushing the check-in data into the attendance array
        result=await event_collection.update_one(
            {"_id": event_id_obj},
            {"$push": {"attendance": check_in_entry}}  # Push to the attendance field
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="Check-in failed: No document updated")
        else:
            print("✅ Successfully pushed attendance into MongoDB!")
        return {"message": "User checked in successfully!"}
    
    except Exception as e:

        raise HTTPException(status_code=500, detail=f"Error during check-in: {str(e)}")
# API to Get Attendance
@app.get("/event_attendance/{event_id}")
async def get_event_attendance(event_id: str):
    try:
        event_id_obj = ObjectId(event_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid event_id format")
    
    event = await event_collection.find_one({"_id": event_id_obj})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    attendance = event.get("attendance", [])
    return {"attendance": attendance}


def extract_student_id_from_token(token: str) -> str:
    try:
        # Decode the token (Assuming you're using JWT and the student_id is in the payload)
        decoded_token = jwt.decode(token, "HimaniSuperSecretKey", algorithms=["HS256"])
        student_id = decoded_token.get("student_id")
        if not student_id:
            raise HTTPException(status_code=400, detail="Student ID not found in the token.")
        return student_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token.")

@app.post("/check_in_by_qr")
async def check_in_by_qr(event_id: str, token: str):
    # Step 1: Extract student_id from the access token
    student_id = extract_student_id_from_token(token)
    
    # Step 2: Convert event_id to ObjectId
    try:
        event_id_obj = ObjectId(event_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid event_id format")

    # Step 3: Check if the event exists
    event = await event_collection.find_one({"_id": event_id_obj})
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")

    # Step 4: Check if the student is registered for the event
    registration = await registration_collection.find_one({
        "event_id": event_id_obj,
        "student_id": student_id
    })
    
    if not registration:
        raise HTTPException(status_code=400, detail="Student is not registered for this event.")

    # Step 5: Mark the student as checked-in
    check_in_entry = {
        "student_id": student_id,
        "checked_in": True,
        "event_id": event_id_obj,
        "timestamp": datetime.now()
    }

    # Step 6: Update the event's attendance (if necessary)
    try:
        result = await event_collection.update_one(
            {"_id": event_id_obj},
            {"$push": {"attendance": check_in_entry}}  # Push to the attendance field
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="Check-in failed: No document updated")
        
        return {"message": "Student successfully checked in!"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during check-in: {str(e)}")

# Function to send an email with the QR code as an attachment
def send_email_with_qr(to_email: str, event_id: str, student_id: str):
    try:
        # SMTP setup (example with Gmail)
        from_email = "himanibhammar@gmail.com"  # Your email address
        password = "rmkd icqd xhpx mqeb"
        
        # Prepare the email message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = f"Your QR Code for Event {event_id}"

        # Add body text to the email
        body = "Please find attached your QR code for the event."
        msg.attach(MIMEText(body, 'plain'))

        # Generate the QR code image
        qr_image = generate_qr_code(event_id, student_id)

        # Attach the QR code image
        img = MIMEImage(qr_image.read(), name="qr_code.png")
        msg.attach(img)

        # Establish the SMTP connection and send the email
        server = smtplib.SMTP('smtp.gmail.com', 587)  # Use the SMTP server for Gmail
        server.starttls()  # Secure the connection
        server.login(from_email, password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()

        return {"message": "Email sent successfully!"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending email: {str(e)}")


@app.post("/send_qr_by_email")
async def send_qr_email(event_id: str, student_id: str, to_email: str):
    # Call the function to send the email
    response = send_email_with_qr(to_email, event_id, student_id)
    return response