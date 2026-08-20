from fastapi import FastAPI


app = FastAPI(
    title="FactoryPulse API",
    description="Manufacturing quality and process intelligence platform",
    version="0.1.0",
)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "Welcome to FactoryPulse API",
    }


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "factorypulse-api",
        "version": "0.1.0",
    }