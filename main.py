from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.router import llm_router
import os
app = FastAPI()


app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    print(os.environ)
    return {"Health": "OK"}


app.include_router(llm_router)

