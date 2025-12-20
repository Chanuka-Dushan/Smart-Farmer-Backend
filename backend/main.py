import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# --- 1. Smart Database Connection ---
# This looks for 'DATABASE_URL' in your environment (DigitalOcean).
# If it can't find it, it defaults to 'sqlite:///./users.db' (Local).
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./users.db")

# Fix for DigitalOcean's Postgres URL string format if needed
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configure the connection arguments based on the database type
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. Database Model (The Table) ---
class User(Base):
    __tablename__ = "users"
    
    email = Column(String, primary_key=True, index=True)
    name = Column(String)
    password = Column(String) # Note: In a real app, you should hash this!

# Create the tables automatically
Base.metadata.create_all(bind=engine)

# --- 3. Pydantic Models (Input Validation) ---
class UserRegister(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

# --- 4. Database Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 5. API Endpoints ---
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Smart Farmer Backend is Running!"}

@app.get("/health")
def health():
    """Health check endpoint for monitoring"""
    return {"status": "healthy"}

@app.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Create new user
    new_user = User(email=user.email, name=user.name, password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User registered successfully"}

@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    # Find user by email and password
    db_user = db.query(User).filter(User.email == user.email, User.password == user.password).first()
    
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {"message": "Login successful", "name": db_user.name}

# Entry point
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)