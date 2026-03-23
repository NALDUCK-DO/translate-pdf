from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import fitz  # PyMuPDF
from openai import OpenAI

app = FastAPI()

# HTML에서 서버에 접속할 수 있도록 설정
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

client = OpenAI(api_key="YOUR_OPENAI_API_KEY")

@app.post("/translate")
async def translate_pdf(file: UploadFile = File(...)):
    # 1. 파일 읽기
    content = await file.read()
    doc = fitz.open(stream=content, filetype="pdf")
    
    extracted_text = ""
    for page in doc:
        # 상하단 10% 영역(헤더, 푸터)을 제외하고 텍스트 추출
        rect = page.rect
        clip = fitz.Rect(0, rect.height * 0.1, rect.width, rect.height * 0.9)
        extracted_text += page.get_text(clip=clip) + "\n"

    # 2. AI 번역 요청 (본문만 선별하도록 프롬프트 구성)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "너는 문서 번역 전문가야. 입력값에서 페이지 번호, 반복되는 제목 등 불필요한 부분은 삭제하고 오직 '본문 내용'만 자연스러운 한국어로 번역해줘."},
            {"role": "user", "content": extracted_text[:4000]} # 무료 티어/토큰 제한 고려
        ]
    )

    return {"translated_text": response.choices[0].message.content}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
