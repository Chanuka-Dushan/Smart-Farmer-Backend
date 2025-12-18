from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import uvicorn

# Initialize the App
app = FastAPI()

# --- Database Setup ---
def init_db():
    """Initializes the SQLite database with a users table."""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    # Create table if not exists
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (email TEXT PRIMARY KEY, name TEXT, password TEXT)''')
    conn.commit()
    conn.close()

# Run DB setup immediately when script starts
init_db()

# --- Data Models (Input Validation) ---
class UserRegister(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

# --- API Endpoints ---

@app.get("/")
def home():
    return {"message": "Smart Farmer Backend is Running!"}

@app.post("/register")
def register(user: UserRegister):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        # Insert user data into database
        c.execute("INSERT INTO users (email, name, password) VALUES (?, ?, ?)", 
                  (user.email, user.name, user.password))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Email already exists")
    
    conn.close()
    return {"message": "User registered successfully"}

@app.post("/login")
def login(user: UserLogin):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    # Check if email and password match
    c.execute("SELECT * FROM users WHERE email=? AND password=?", 
              (user.email, user.password))
    account = c.fetchone()
    conn.close()

    if account:
        # account[1] is the 'name' column
        return {"message": "Login successful", "name": account[1]}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# Entry point to run the server directly
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)