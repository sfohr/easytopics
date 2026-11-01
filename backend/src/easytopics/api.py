from fastapi import FastAPI

app = FastAPI(title="EasyTopics")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
