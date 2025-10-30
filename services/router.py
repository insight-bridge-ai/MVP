from fastapi import APIRouter
from services.provider import ask_graph
from services.schema import QuestionRequest

llm_router = APIRouter()

@llm_router.post("/ask")
def ask(request: QuestionRequest):
    """
    POST /ask
    Body: { "question": "your question", "schema": optional_schema_string }
    Returns: { "answer": "Text Response" }
    """
    answer = ask_graph(request.question, schema_override=request.schema)
    return {"answer": answer}