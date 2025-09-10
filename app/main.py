from fastapi import FastAPI
from app.routers import auth, habits, stats

app = FastAPI(title="Habit Tracker API")

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(habits.router, prefix="/habits", tags=["habits"])
app.include_router(stats.router, prefix="/stats", tags=["stats"])

@app.get('/')
def read_root():
    return {"msg": "Habit Tracker API. Visit /docs for OpenAPI UI."}
