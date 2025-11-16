from typing import Union

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"Welcome to asiya fyp"}


@app.get("/expense/{expense_id}")
def read_expense(expense_id: int, q: Union[str, None] = None):
    return {"expense_id": expense_id, "q": q}