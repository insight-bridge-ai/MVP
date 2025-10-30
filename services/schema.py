from pydantic import BaseModel
from typing import Union


class QuestionRequest(BaseModel):
    question: str
    schema: Union[str, None] = None