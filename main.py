import uvicorn

from app.config import Config
from app.main import app

if __name__ == "__main__":
    config = Config()
    uvicorn.run("app.main:app", host="0.0.0.0", port=config.PORT, reload=config.DEBUG)

