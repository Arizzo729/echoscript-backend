from fastapi import FastAPI

app = FastAPI(title="Mini OK")


@app.get("/health")
def health():
    return {"ok": True}
