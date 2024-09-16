from fastapi import FastAPI
from app.fastapi_routes import router
from app.models import Base
from app.database import engine

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(router)

