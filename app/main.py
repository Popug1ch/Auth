from fastapi import FastAPI
import uvicorn
from contextlib import asynccontextmanager
from app.seed import init_db_async
from app.routers import auth, users, admin, resources

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db_async()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(resources.router)



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)