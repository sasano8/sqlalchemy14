import uvicorn
from sqlalchemy14.main import app

# # uvicorn.run("main:app", port=1111, host="127.0.0.1")
uvicorn.run("sqlalchemy14:app", reload=True)
