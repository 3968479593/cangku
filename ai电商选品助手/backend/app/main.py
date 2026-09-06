import logging
import os
import sys

from fastapi import Depends

# ---- 关键：必须在任何 huggingface/sentence_transformers 导入之前设置 ----
from app.config import settings

if settings.HF_ENDPOINT:
    os.environ["HF_ENDPOINT"] = settings.HF_ENDPOINT

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.deps import get_current_user, get_current_admin
from app.api.routes import documents, search, products, chat, auth, admin, analysis, feedback
from app.models.database import engine, Base

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"], dependencies=[Depends(get_current_admin)])
app.include_router(search.router, prefix="/api/search", tags=["search"], dependencies=[Depends(get_current_user)])
app.include_router(products.router, prefix="/api/products", tags=["products"], dependencies=[Depends(get_current_user)])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"], dependencies=[Depends(get_current_user)])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"], dependencies=[Depends(get_current_user)])
app.include_router(feedback.router, prefix="/api/feedback", tags=["feedback"])


@app.on_event("startup")
def load_models():
    if settings.HF_ENDPOINT:
        os.environ["HF_ENDPOINT"] = settings.HF_ENDPOINT
        logger.info(f"已设置 HuggingFace 镜像: {settings.HF_ENDPOINT}")

    logger.info("=" * 50)
    logger.info("正在预加载嵌入模型（首次启动会下载，请耐心等待进度条完成）...")
    logger.info(f"模型缓存目录: {settings.MODEL_CACHE_DIR}")
    if not settings.HF_ENDPOINT:
        logger.info("提示: 如果下载慢或卡住，可在 .env 中设置 HF_ENDPOINT=https://hf-mirror.com")
    logger.info("=" * 50)
    try:
        from app.core.embedding import get_embedding_model
        get_embedding_model()
        logger.info("嵌入模型加载完成！")
    except Exception as e:
        logger.error(f"嵌入模型加载失败: {e}")

    logger.info("=" * 50)
    logger.info("正在预加载重排序模型...")
    logger.info("=" * 50)
    try:
        from app.core.reranker import get_reranker
        get_reranker()
        logger.info("重排序模型加载完成！")
    except Exception as e:
        logger.error(f"重排序模型加载失败: {e}")

    logger.info("所有模型加载完毕，服务已就绪！")


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": settings.APP_NAME}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
