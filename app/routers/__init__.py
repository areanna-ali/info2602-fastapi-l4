from fastapi import APIRouter
main_router = APIRouter()

from .auth import auth_router
main_router.include_router(auth_router)

from.todos import todos_router
main_router.include_router(todos_router)