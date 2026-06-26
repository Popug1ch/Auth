from fastapi import FastAPI
import uvicorn
from contextlib import asynccontextmanager
from app.seed import init_db_async

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db_async()
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def read_root():
    return {"Hello": "World"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)