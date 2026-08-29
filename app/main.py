from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.database import init_db
from app.routers import dashboard, assets, plans, trades, reviews, glossary, widget


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Swing Trading Diary",
    description="Lightweight Trading Diary & Portfolio Benchmark System (Shadcn Layout)",
    lifespan=lifespan,
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(dashboard.router)
app.include_router(assets.router)
app.include_router(plans.router)
app.include_router(trades.router)
app.include_router(reviews.router)
app.include_router(glossary.router)
app.include_router(widget.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
