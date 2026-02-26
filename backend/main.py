from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import time
import json
import glob
import asyncio

app = FastAPI(title="GramSevak AI Backend")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enable gzip compression
app.add_middleware(GZipMiddleware, minimum_size=100)

class Query(BaseModel):
    text: str
    lang: str = "hi"
    simulate_2g: bool = False

class QueryResponse(BaseModel):
    answer: str
    scheme_name: str
    source: str
    bytes_used: int
    response_time_ms: int
    cached: bool
    confidence: float

# Load knowledge base
try:
    import glob
    kb_dir = Path("knowledge_base")
    KNOWLEDGE_BASE = []
    
    # Load all JSON files
    for json_file in glob.glob(str(kb_dir / "*.json")):
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                KNOWLEDGE_BASE.extend(data)
    
    print(f"✓ Loaded {len(KNOWLEDGE_BASE)} entries from knowledge base")
except FileNotFoundError:
    KNOWLEDGE_BASE = []
    print("⚠ Warning: Knowledge base not found. Run build_index.py first.")

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "schemes_loaded": len(KNOWLEDGE_BASE),
        "timestamp": time.time()
    }

@app.post("/query", response_model=QueryResponse)
async def process_query(q: Query):
    start_time = time.time()
    
    # Simulate 2G latency if requested
    if q.simulate_2g:
        await asyncio.sleep(0.5)
    
    # Import RAG pipeline
    from rag_pipeline import answer_query
    
    try:
        result = await answer_query(q.text, KNOWLEDGE_BASE)
        
        response_text = result["answer"]
        response_bytes = len(response_text.encode("utf-8"))
        response_time = int((time.time() - start_time) * 1000)
        
        return QueryResponse(
            answer=response_text,
            scheme_name=result["scheme_name"],
            source=result["source"],
            bytes_used=response_bytes,
            response_time_ms=response_time,
            cached=False,
            confidence=result["confidence"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/offline-pack")
def get_offline_pack():
    """Returns top 200 Q&As for offline caching"""
    # Return most common queries
    offline_data = KNOWLEDGE_BASE[:200] if len(KNOWLEDGE_BASE) > 200 else KNOWLEDGE_BASE
    return {
        "version": "1.0",
        "count": len(offline_data),
        "data": offline_data
    }

@app.get("/stats")
def get_stats():
    """Returns usage statistics"""
    return {
        "total_schemes": len(KNOWLEDGE_BASE),
        "categories": list(set(s.get("category", "other") for s in KNOWLEDGE_BASE)),
        "languages_supported": ["hi", "en"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
