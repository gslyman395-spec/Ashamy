from fastapi import FastAPI, HTTPException

app = FastAPI()

# مسار رئيسي للتأكد أن السيرفر يعمل
@app.get("/")
def home():
    return {"message": "Server is running successfully!"}

# مسار حالة السيرفر
@app.get("/status")
def status():
    return {"status": "ok", "service": "ashamy-backend"}

# نموذج بسيط لتسجيل مستخدم (بدون قاعدة بيانات حالياً)
@app.post("/register")
def register_user(data: dict):
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password are required")

    return {
        "status": "success",
        "message": f"User '{username}' registered successfully (demo, no DB yet)."
    }

# نموذج بسيط لتسجيل دخول (تحقق شكلي فقط)
@app.post("/login")
def login_user(data: dict):
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password are required")

    return {
        "status": "success",
        "message": f"User '{username}' logged in successfully (demo, no real auth yet)."
    }

