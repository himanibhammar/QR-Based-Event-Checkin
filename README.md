# 🎟️ QR-Based Event Check-In System

A backend system for managing college event check-ins using QR codes. It allows users to register for events, receive unique QR codes, and enables event organizers to verify attendance through QR scanning—mimicking real-world ticketing systems.

---

## 🛠️ Tech Stack

- **Backend Framework**: FastAPI (Python)
- **Database**: MongoDB
- **Authentication**: JWT-based login/signup
- **QR Code Generation**: `qrcode` (Python)
- **Email Integration**: (optional) SendGrid/Nodemailer
- **Validation**: Pydantic
- **API Documentation**: Postman

---

## 🚀 Features

### ✅ 1. User Authentication
- Register using name, email, student ID, and password
- Secure login using JWT tokens
- Role-based access control: `student` and `admin`

### ✅ 2. Event Management
- **Admins** can create events: title, description, location, date, time
- **Students** can register for events
- On registration:
  - A unique QR code is generated (contains user + event metadata)
  - QR code is returned in response (and optionally emailed)

### ✅ 3. Admin Dashboard (API Level)
- View list of registered attendees
- View checked-in vs total registered users
- Export attendee data as CSV or JSON (planned)

### ✅ 4. Documentation
- Fully documented API using Postman
- Covers:
  - Authentication
  - Event creation
  - Registration
  - QR-based check-in
  - QR getting Emailed to registered participant
  - Admin data access

---

## 🧪 Testing

- All APIs tested using Postman
- JWT auth headers handled in protected routes
- Registration, event creation, and check-in fully validated

---
