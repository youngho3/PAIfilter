import google.generativeai as genai
from app.core.config import settings

# Gemini 설정
genai.configure(api_key=settings.GOOGLE_API_KEY)

async def get_text_embedding(text: str) -> list[float]:
    """
    텍스트를 입력받아 Gemini text-embedding-004 모델의 벡터(768차원)를 반환합니다.
    """
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document",
        )
        return result['embedding']
    except Exception as e:
        print(f"Gemini Embedding Error: {e}")
        return []

def get_gemini_response(prompt: str) -> str:
    """
    Gemini 최신 프리뷰 모델을 사용하여 텍스트 생성을 수행합니다.
    """
    try:
        model = genai.GenerativeModel('gemini-3-flash-preview')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini Generation Error: {e}")
        return str(e)
