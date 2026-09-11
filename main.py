from fastapi import FastAPI 
from app.routers.flights import router as flights_router 

app = FastAPI() 

app.include_router(flights_router) 

@app.get("/health")
def health_check():
    return {"status": "ok"}