from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI

from backend.api.routes.upload import router as upload_router
from backend.api.routes.transcribe import router as transcribe_router

app = FastAPI(title="SpeakSharp")
app.include_router(upload_router)
app.include_router(transcribe_router)
