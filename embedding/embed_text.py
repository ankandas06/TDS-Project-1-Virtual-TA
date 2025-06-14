import openai
import os, json
import chromadb
from chromadb.config import Settings,DEFAULT_TENANT, DEFAULT_DATABASE
from dotenv import load_dotenv

load_dotenv()
openai.api_key = r"{}".format(os.getenv("OPENAI_API_KEY"))


FILE_PATH = "./embedding/final_text.json"
with open(FILE_PATH,"r", encoding="utf-8") as f:
    records = json.load(f)

client = chromadb.PersistentClient(
    path="./chroma_db",
    settings=Settings(
        anonymized_telemetry=False
    ),
    tenant=DEFAULT_TENANT,
    database=DEFAULT_DATABASE
)

collection = client.get_or_create_collection(
    name="tds_final_text",
    metadata={"hnsw:space": "cosine"}
)

BATCH_SIZE = 300
for i in range(0, len(records), BATCH_SIZE):
    batch = records[i : i + BATCH_SIZE]
    texts = [r["text"] for r in batch]
    urls  = [r["url"]  for r in batch]

    resp = openai.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )
    vectors = [item.embedding for item in resp.data]

    collection.add(
        ids        = urls,
        embeddings = vectors,
        metadatas  = [{"url": u} for u in urls],
        documents  = texts
    )
    print(f"Upserted batch {i}–{i + len(batch) - 1}")
