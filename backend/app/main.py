from fastapi import FastAPI

app = FastAPI(
    title="RotaCerta API",
    version="0.1.0",
    description="API inicial para cadastro, roteirização e acompanhamento de entregas.",
)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
