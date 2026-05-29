import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db import create_db_and_tables, get_async_session, Post
from src.images import imagekit

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создаем таблицы при запуске приложения
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    caption: str = Form(...),
    session: AsyncSession = Depends(get_async_session)
): 
    try:
        # Читаем файл в байты из веб-формы FastAPI
        file_bytes = await file.read()
        
        # Загружаем по новому синтаксису документации
        response = imagekit.files.upload(
            file=file_bytes,
            file_name=file.filename,
            folder="/posts"  # Передаем настройки напрямую аргументами!
        )
        
        # Новый SDK возвращает Pydantic-модель. Доступ к полям через точку:
        file_url = response.url
        file_id_name = response.file_id  # или response.name в зависимости от модели

    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Ошибка ImageKit SDK: {str(e)}"
        )
    finally:
        await file.close()

    # Сохраняем в базу данных
    file_type = "video" if file.content_type and file.content_type.startswith("video/") else "photo"
    
    post = Post(
        caption=caption,
        url=file_url,
        file_type=file_type,
        file_name=file.filename
    )

    session.add(post)
    await session.commit()
    await session.refresh(post)
    
    return post


@app.get("/feed")
async def get_feed(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Post).order_by(Post.created_at.desc()))
    
    # scalars() — более красивый способ получить объекты SQLAlchemy, вместо row[0]
    posts = result.scalars().all()

    posts_data = []
    for post in posts:
        posts_data.append({
            "id": post.id,
            "caption": post.caption,
            "url": post.url,
            "file_type": post.file_type,
            "file_name": post.file_name,
            "created_at": post.created_at.isoformat()
        })

    return {"posts": posts_data}