import os
import base64
import io

import openai
import chromadb
import pytesseract
from PIL import Image
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from chromadb.config import Settings, DEFAULT_TENANT, DEFAULT_DATABASE
from dotenv import load_dotenv

load_dotenv()

openai.api_key = r"{}".format(os.getenv("OPENAI_API_KEY"))

client = chromadb.PersistentClient(
    path="./chroma_db",
    settings=Settings(anonymized_telemetry=False),
    tenant=DEFAULT_TENANT,
    database=DEFAULT_DATABASE,
)
collection = client.get_collection("tds_final_text")

class Query(BaseModel):
    question: str
    image: str | None = None

app = FastAPI()

@app.post("/api", summary="Ask the TDS Virtual TA")
async def answer(q: Query):
    question = q.question.strip()
    if q.image:
        try:
            img = Image.open(io.BytesIO(base64.b64decode(q.image)))
            ocr_text = pytesseract.image_to_string(img).strip()
            question += f"\n\n[OCR text]\n{ocr_text}"
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"OCR error: {e}")

    try:
        emb_resp = openai.embeddings.create(
            model="text-embedding-3-small",
            input=[question]
        )
    except openai.OpenAIError as e:
        raise HTTPException(status_code=502, detail=f"Embedding failed: {e}")

    qvec = emb_resp.data[0].embedding

    results = collection.query(
        query_embeddings=[qvec],
        n_results=5,
        include=["documents", "metadatas"]
    )
    docs  = results["documents"][0]
    metas = results["metadatas"][0]

    context = "\n\n---\n\n".join(docs)
    system_prompt = (
        "You are a knowledgeable Teaching Assistant for IIT Madras’ Tools in Data Science course.\n"
        "Be concise and answer shortly not long passages\n"
        "Answer only from the context given to you and do not hallucinate."
        "Dont answer to specifics like exam dates as they are tentative just say 'I don't know'."
        f"Context:\n{context}\n"
    )
    user_prompt = f"Question: {question}"

    try:
        chat = openai.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.0
        )
    except openai.OpenAIError as e:
        raise HTTPException(status_code=502, detail=f"ChatCompletion failed: {e}")

    answer_text = chat.choices[0].message.content.strip()

    links = [
        {"url": m["url"], "text": m.get("title", m["url"])}
        for m in metas
    ]

    return {"answer": answer_text, "links": links}