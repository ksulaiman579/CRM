from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, or_, update
from app.db.session import get_db
from app.schemas.kb import KbArticleResponse, KbArticleCreate, KbCategoryResponse
from app.models.kb import KbArticle, KbCategory
from app.core.deps import get_current_user

router = APIRouter()

@router.get("/categories", response_model=list[KbCategoryResponse])
async def list_categories(session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(KbCategory))
    return result.scalars().all()

@router.get("/articles", response_model=list[KbArticleResponse])
async def list_articles(
    category_id: int | None = Query(None),
    q: str | None = Query(None, description="Search term for title or body"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db)
):
    query = select(KbArticle).where(KbArticle.status == "published")
    
    if category_id:
        query = query.where(KbArticle.category_id == category_id)
        
    if q:
        query = query.where(
            or_(
                KbArticle.title.ilike(f"%{q}%"),
                KbArticle.body.ilike(f"%{q}%")
            )
        )
        
    query = query.order_by(desc(KbArticle.created_at)).offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    return result.scalars().all()

@router.get("/articles/{id}", response_model=KbArticleResponse)
async def get_article(id: int, session: AsyncSession = Depends(get_db)):
    article = await session.get(KbArticle, id)
    if not article or article.status != "published":
        raise HTTPException(status_code=404, detail="Article not found")
        
    # Increment view count
    article.view_count += 1
    await session.commit()
    await session.refresh(article)
    
    return article

@router.post("/articles", response_model=KbArticleResponse)
async def create_article(
    request: KbArticleCreate, 
    session: AsyncSession = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    new_article = KbArticle(**request.model_dump(), author_id=current_user["id"])
    session.add(new_article)
    await session.commit()
    await session.refresh(new_article)
    return new_article
