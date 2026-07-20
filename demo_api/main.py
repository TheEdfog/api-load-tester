from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Load tester demo API", version="1.0.0")


class NameRequest(BaseModel):
    name: str


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/names")
async def add_name(request: NameRequest) -> dict[str, str | int]:
    return {"name": request.name, "length": len(request.name)}
