from pydantic import BaseModel
from typing import TypedDict


# # BaseModel类起到了辅助校验的功能
# class User(BaseModel):
#     id: int
#     name: str
#     age: int = None  # 可选字段，有默认值None
#     email: str
#
#
# user = User(id=1, name="Alice", age=30, email="alice@example.com")
# print(user)


class User(TypedDict):
    id: int
    name: str
    age: int
    email: str


user = User(id=1, name="Alice", age=30, email="alice@example.com")
print(user)