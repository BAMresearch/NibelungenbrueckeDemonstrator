import uvicorn
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from app1 import app as dashboard1
from app2 import app as dashboard2


# Define the FastAPI server
app = FastAPI()
# Mount the Dash app as a sub-application in the FastAPI server
app.mount("/dashboard1", WSGIMiddleware(dashboard1.server))
app.mount("/dashboard2", WSGIMiddleware(dashboard2.server))

# Define the main API endpoint
@app.get("/")
def index():
    return "Hello"


# Start the FastAPI server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0")