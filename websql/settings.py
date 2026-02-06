from pydantic import BaseModel
import os

class WebSQLSettings(BaseModel):
    tracelet_api: str = os.getenv("TRACELET_API", "http://127.0.0.1:8000")
    host: str = "127.0.0.1"
    port: int = 8076
    debug: bool = True

settings = WebSQLSettings()
