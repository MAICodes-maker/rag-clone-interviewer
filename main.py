import logging
import uvicorn 
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from routes import job_router

app = FastAPI()
logging.basicConfig(
    filename="app.log",level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(job_router)

@app.get("/")
async def home():
    return {
        "message": "Welcome to the Application. Access the documentation at /docs or /redoc."
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app=app, port=5007)