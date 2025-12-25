from pinecone import Pinecone
from app.core.config import settings
from app.services.gemini_service import get_text_embedding
import uuid

# Pinecone 초기화
pc = Pinecone(api_key=settings.PINECONE_API_KEY)
index = pc.Index(name=settings.PINECONE_INDEX_NAME, host=settings.PINECONE_HOST)

async def upsert_context(text: str, metadata: dict = None):
    """
    텍스트를 벡터화하여 Pinecone에 저장합니다.
    """
    vector = await get_text_embedding(text)
    if not vector:
        return False
    
    # ID 생성 및 메타데이터 구성
    vector_id = str(uuid.uuid4())
    payload = {
        "id": vector_id,
        "values": vector,
        "metadata": {
            "text": text,
            **(metadata or {})
        }
    }
    
    try:
        index.upsert(vectors=[payload])
        return vector_id
    except Exception as e:
        print(f"Pinecone Upsert Error: {e}")
        return None

async def search_similar_context(text: str, top_k: int = 3):
    """
    유사한 맥락을 검색합니다. (Sprint 1 검증용)
    """
    vector = await get_text_embedding(text)
    if not vector:
        return []
    
    try:
        results = index.query(
            vector=vector,
            top_k=top_k,
            include_metadata=True
        )
        return results['matches']
    except Exception as e:
        print(f"Pinecone Query Error: {e}")
        return []
