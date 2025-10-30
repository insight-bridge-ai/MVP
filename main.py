from fastapi import FastAPI
from services.router import llm_router
import os
app = FastAPI()


@app.get("/")
def root():
    print(os.environ)
    return {"Health": "OK"}


app.include_router(llm_router)

