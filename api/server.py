from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class PauseReq(BaseModel):
    campaign: str
    seconds: int = 900


@app.get("/health")
async def health():
    return {"ok": True}


@app.post("/pause")
async def pause(req: PauseReq):
    return {"status": "paused", "campaign": req.campaign, "seconds": req.seconds}
