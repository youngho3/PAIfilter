from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.services.gemini_service import get_text_embedding, get_gemini_response
from app.services.pinecone_service import upsert_context, search_similar_context
from app.core.config import settings

app = FastAPI(title="PAI Intelligence Engine", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextInput(BaseModel):
    text: str

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "PAI Intelligence Engine",
        "config": {
            "gemini_configured": bool(settings.GOOGLE_API_KEY),
            "pinecone_configured": bool(settings.PINECONE_API_KEY)
        }
    }

@app.post("/api/v1/vectorize")
async def vectorize_text(input_data: TextInput):
    vector = await get_text_embedding(input_data.text)
    if not vector:
        raise HTTPException(status_code=500, detail="Failed to generate embedding")
    return {
        "original_text": input_data.text,
        "vector_dimension": len(vector),
        "vector_preview": vector[:5]
    }

@app.post("/api/v1/context")
async def store_context(input_data: TextInput):
    """
    고민을 벡터화하여 기억장치(Pinecone)에 저장합니다.
    """
    vector_id = await upsert_context(input_data.text)
    if not vector_id:
        raise HTTPException(status_code=500, detail="Failed to store context in Vector DB")
    return {"status": "success", "id": vector_id, "message": "Context remembered."}

@app.post("/api/v1/search")
async def search_context(input_data: TextInput):
    """
    유사한 과거 고민을 검색합니다.
    """
    matches = await search_similar_context(input_data.text)
    return {"matches": matches}

@app.post("/api/v1/insight")
async def generate_insight(input_data: TextInput):
    """
    RAG 적용: 과거 기억(Pinecone)을 검색하여 Gemini에게 맥락을 제공합니다.
    """
    # 1. 관련 기억 검색 (유사도 0.7 이상만)
    matches = await search_similar_context(input_data.text, top_k=3)
    
    relevant_contexts = []
    for m in matches:
        if m['score'] > 0.7:  # 유사도가 높은 기억만 참조
            relevant_contexts.append(f"- {m['metadata']['text']} (유사도: {m['score']:.2f})")
    
    memory_text = "\n".join(relevant_contexts) if relevant_contexts else "관련된 과거 기억이 없습니다."

    # 2. 프롬프트 구성
    prompt = f"""
    당신은 사용자의 맥락을 깊이 이해하는 AI 파트너 'PAI'입니다.
    
    [사용자의 과거 고민/관심사 (Memory)]
    {memory_text}

    [현재 입력]
    {input_data.text}

    [지시사항]
    위의 '과거 기억'을 참고하여 현재 입력에 대한 통찰력 있는 피드백을 주세요. 
    과거에 했던 고민과 연결된다면 그 연관성을 언급해 주세요.
    """

    # 3. 답변 생성
    response = get_gemini_response(prompt)
    return {
        "insight": response,
        "context_used": relevant_contexts  # 디버깅용: 어떤 기억을 참고했는지 반환
    }
