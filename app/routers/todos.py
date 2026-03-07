from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select, delete
from app.database import SessionDep
from app.models import *
from app.auth import encrypt_password, verify_password, create_access_token, AuthDep
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from fastapi import status

todos_router = APIRouter(tags=["Todos"])

@todos_router.get('/todos', response_model=list[TodoResponse])
def get_todos(db:SessionDep, user: AuthDep):
    return user.todos

@todos_router.get("/todo/{id}")
def get_todo_by_id(id: int, db: SessionDep, user: AuthDep):
    user = db.exec(select(Todo).where(Todo.id, Todo.id == user.id)).one_or_none()
    if not Todo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Todo


@todos_router.post('/todos', response_model=TodoResponse)
def create_todo(db: SessionDep, user: AuthDep, todo_data:TodoCreate):
    todo = Todo(text = todo_data.text, user_id = user.id)
    try:
        db.add(todo)
        db.commit()
        db.refresh(todo)
        return todo
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="An error occurred!",
        )


@todos_router.put('/todo/{id}', response_model=TodoResponse)
def update_todo(id:int, db:SessionDep, user:AuthDep, todo_data:TodoUpdate):
    todo = db.exec(select(Todo).where(Todo.id==id, Todo.user_id==user.id)).one_or_none()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    if todo_data.text is not None:
        todo.text = todo_data.text
    if todo_data.done:
        todo.done = todo_data.done
    try:
        db.add(todo)
        db.commit()
        return todo
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while updating an item",
        )

@todos_router.delete('/todo/{id}', status_code=status.HTTP_200_OK)
def delete_todo(id:int, db:SessionDep, user:AuthDep):

    todo = db.exec(select(Todo).where(Todo.id==id, Todo.user_id==user.id)).one_or_none()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    try:
        db.delete(todo)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while deleting an item",
        )


@todos_router.post('/category', response_model=Category)
def create_category(category_data: CreateCategory, db: SessionDep, user:AuthDep):
    category = Category(user_id=user.id, text=category_data.text)

    try:
        db.add(category)
        db.commit()
        db.refresh(category)
        return category
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="An error occurred!",
        )

@todos_router.post('/todo/{todo_id}/category/{cat_id}', response_model=TodoResponse)
def add_cat_to_todo(cat_id: int, todo_id: int, db: SessionDep, user: AuthDep):
    todo = db.exec(select(Todo).where(Todo.id==todo_id)).one_or_none()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    
    category = db.exec(select(Category).where(Category.id==cat_id)).one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    
    if category is not todo.categories:
        todo.categories.append(category)
        db.add(todo)
        db.commit()
        db.refresh(todo)

    return todo

@todos_router.delete('/todo/{todo_id}/category/{cat_id}', response_model=TodoResponse)
def delete_cat_from_todo(cat_id: int, todo_id: int, db: SessionDep, user: AuthDep):
    todo = db.exec(select(Todo).where(Todo.id==todo_id)).one_or_none()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    
    statement = delete(TodoCategory).where(TodoCategory.todo_id==todo_id, TodoCategory.category_id==cat_id)
    result = db.exec(statement)
    db.commit()

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bad Request",
        )
    
    db.refresh(todo)
    return todo

@todos_router.get('/category/{cat_id}/todos', response_model=list[TodoResponse])
def list_todos_by_cat(cat_id: int, db: SessionDep, user: AuthDep):

    category = db.exec(select(Category).where(Category.id==cat_id, Category.user_id==user.id)).one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    return category.todos
    





