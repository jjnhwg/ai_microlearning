from dotenv import load_dotenv
load_dotenv()

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from backend.api.routes.upload import router as upload_router
from backend.api.routes.transcribe import router as transcribe_router
from backend.api.routes.report import router as report_router

app = FastAPI(title="SpeakSharp")
app.include_router(upload_router)
app.include_router(transcribe_router)
app.include_router(report_router)

_INDEX = Path(__file__).parent / "static" / "index.html"


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(_INDEX)
