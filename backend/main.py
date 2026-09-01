from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI

# TODO (you): import your routers here
from backend.api.routes.upload import router as upload_router

app = FastAPI(title="SpeakSharp")
# TODO (you): register each router with app.include_router(); add prefix/tags here if you prefer to centralise them
app.include_router(upload_router)
