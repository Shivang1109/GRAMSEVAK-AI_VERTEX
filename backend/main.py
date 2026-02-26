from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
from starlette.requests import Request
import time
import json
import glob
import asyncio
from intent_classifier import IntentClassifier

app = FastAPI(title="GramSevak AI Backend")

# Initialize intent classifier
intent_classifier = IntentClassifier()
print("✓ Intent classifier initialized")

# Initialize stats tracking
STATS = {
    "total_queries": 0,
    "cache_hits": 0,
    "llm_calls": 0,
    "total_response_bytes": 0,
    "network_2g_queries": 0,
    "network_3g_queries": 0,
    "network_4g_queries": 0,
    "category_counts": {},  # Track queries per category
    "user_type_counts": {},  # Track queries per user type
    "offline_queries": 0,  # Track offline mode queries
    "online_queries": 0,  # Track online mode queries
    "total_feedback": 0,  # Track feedback submissions
    "helpful_count": 0,  # Track helpful feedback
    "not_helpful_count": 0,  # Track not helpful feedback
}

# Rate limiting storage
RATE_LIMIT = {
    "requests": {},  # {ip: [timestamp1, timestamp2, ...]}
    "blocked_attempts": 0,
    "last_cleanup": time.time()
}

RATE_LIMIT_MAX = 20  # Max requests per minute
RATE_LIMIT_WINDOW = 60  # Time window in seconds

print("✓ Stats tracking initialized")
print("✓ Rate limiting initialized")

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

# Rate limiting helper functions
def cleanup_rate_limit_data():
    """Remove old timestamps from rate limit tracking"""
    current_time = time.time()
    cutoff_time = current_time - RATE_LIMIT_WINDOW
    
    # Clean up old entries
    for ip in list(RATE_LIMIT["requests"].keys()):
        RATE_LIMIT["requests"][ip] = [
            ts for ts in RATE_LIMIT["requests"][ip] 
            if ts > cutoff_time
        ]
        # Remove IP if no recent requests
        if not RATE_LIMIT["requests"][ip]:
            del RATE_LIMIT["requests"][ip]
    
    RATE_LIMIT["last_cleanup"] = current_time

def check_rate_limit(ip: str, is_admin: bool = False) -> tuple[bool, int]:
    """
    Check if IP has exceeded rate limit
    Returns: (is_allowed, remaining_requests)
    """
    # Skip rate limiting for admin endpoints
    if is_admin:
        return True, RATE_LIMIT_MAX
    
    # Cleanup old data every 60 seconds
    if time.time() - RATE_LIMIT["last_cleanup"] > 60:
        cleanup_rate_limit_data()
    
    current_time = time.time()
    cutoff_time = current_time - RATE_LIMIT_WINDOW
    
    # Get recent requests for this IP
    if ip not in RATE_LIMIT["requests"]:
        RATE_LIMIT["requests"][ip] = []
    
    # Filter to only recent requests
    recent_requests = [
        ts for ts in RATE_LIMIT["requests"][ip] 
        if ts > cutoff_time
    ]
    RATE_LIMIT["requests"][ip] = recent_requests
    
    # Check if limit exceeded
    if len(recent_requests) >= RATE_LIMIT_MAX:
        RATE_LIMIT["blocked_attempts"] += 1
        print(f"🚫 Rate limit exceeded for IP: {ip} ({len(recent_requests)} requests)")
        return False, 0
    
    # Add current request
    RATE_LIMIT["requests"][ip].append(current_time)
    remaining = RATE_LIMIT_MAX - len(RATE_LIMIT["requests"][ip])
    
    return True, remaining

class Query(BaseModel):
    text: str
    lang: str = "hi"
    simulate_2g: bool = False
    network_type: Optional[str] = None  # "2g", "3g", "4g", or None
    user_type: Optional[str] = None  # "farmer", "student", "worker", "general"

class QueryResponse(BaseModel):
    summary: str
    eligibility: Optional[str] = None
    documents_required: Optional[list] = None
    official_link: Optional[str] = None
    emergency_helplines: Optional[list] = None
    source: str
    confidence: float
    mode: str
    scheme_name: str
    category: str
    category_confidence: float
    bytes_used: int
    response_time_ms: int
    cached: bool
    low_confidence_warning: Optional[bool] = None
    fallback_mode: Optional[bool] = None
    compressed: Optional[bool] = None
    original_length: Optional[int] = None
    retrieval_method: Optional[str] = None  # "direct_match", "semantic_match", "rag_llm"
    similarity_score: Optional[float] = None  # 0-1 range
    last_updated: Optional[str] = None  # Data freshness indicator
    simulate_2g_mode: Optional[bool] = None  # 2G simulation mode flag

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
async def process_query(q: Query, request: Request):
    # Check rate limit
    client_ip = request.client.host
    is_allowed, remaining = check_rate_limit(client_ip, is_admin=False)
    
    if not is_allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": "कृपया थोड़ी देर बाद प्रयास करें",
                "retry_after": 60
            }
        )
    
    start_time = time.time()
    
    # Update stats
    STATS["total_queries"] += 1
    
    # Track network type
    if q.network_type == "2g":
        STATS["network_2g_queries"] += 1
    elif q.network_type == "3g":
        STATS["network_3g_queries"] += 1
    elif q.network_type == "4g":
        STATS["network_4g_queries"] += 1
    
    # Track user type
    if q.user_type:
        STATS["user_type_counts"][q.user_type] = STATS["user_type_counts"].get(q.user_type, 0) + 1
    
    # Simulate 2G latency if requested
    if q.simulate_2g:
        await asyncio.sleep(0.5)
        # Force 2G network type for compression
        if not q.network_type:
            q.network_type = "2g"
    
    # Step 1: Classify intent to determine category
    classify_start = time.time()
    category, category_confidence = intent_classifier.classify(q.text)
    classify_time = (time.time() - classify_start) * 1000
    
    # Log classification result
    print(f"🎯 Intent Classification: {category} (confidence: {category_confidence:.2f}, time: {classify_time:.2f}ms)")
    
    # Import RAG pipeline
    from rag_pipeline import answer_query
    
    try:
        # Step 2: Pass category to RAG pipeline for filtered retrieval
        result = await answer_query(q.text, KNOWLEDGE_BASE, category_filter=category, simulate_2g=q.simulate_2g)
        
        # Track cache hits and LLM calls
        if result["source"] == "keyword_match":
            STATS["cache_hits"] += 1
        elif result["source"] == "groq_llm":
            STATS["llm_calls"] += 1
        
        # Track category
        STATS["category_counts"][category] = STATS["category_counts"].get(category, 0) + 1
        
        # Track offline vs online
        if result["source"] == "keyword_match":
            STATS["offline_queries"] += 1
        else:
            STATS["online_queries"] += 1
        
        # Step 3: Apply adaptive compression based on network type
        compressed = False
        original_length = None
        
        if q.network_type in ["2g", "3g"]:
            original_summary = result["summary"]
            original_length = len(original_summary)
            
            # Determine character limit
            char_limit = 200 if q.network_type == "2g" else 400
            
            if len(original_summary) > char_limit:
                # Compress summary
                result["summary"] = original_summary[:char_limit] + "..."
                compressed = True
                
                # Remove optional fields for 2G
                if q.network_type == "2g":
                    result.pop("eligibility", None)
                    result.pop("documents_required", None)
                    # Keep emergency_helplines if present (critical)
                
                print(f"📦 Compressed for {q.network_type.upper()}: {original_length} → {len(result['summary'])} chars")
        
        # Calculate response size
        response_json = json.dumps(result, ensure_ascii=False)
        response_bytes = len(response_json.encode("utf-8"))
        response_time = int((time.time() - start_time) * 1000)
        
        # Update stats
        STATS["total_response_bytes"] += response_bytes
        
        # Determine mode
        if result["source"] == "safety_filter":
            mode = "emergency"
        elif result["source"] == "keyword_match":
            mode = "offline"
        else:
            mode = "llm"
        
        return QueryResponse(
            summary=result["summary"],
            eligibility=result.get("eligibility"),
            documents_required=result.get("documents_required"),
            official_link=result.get("official_link"),
            emergency_helplines=result.get("emergency_helplines"),
            source=result["source"],
            confidence=result["confidence"],
            mode=mode,
            scheme_name=result["scheme_name"],
            category=category,
            category_confidence=category_confidence,
            bytes_used=response_bytes,
            response_time_ms=response_time,
            cached=result["source"] == "keyword_match",
            low_confidence_warning=result.get("low_confidence_warning"),
            fallback_mode=result.get("fallback_mode"),
            compressed=compressed,
            original_length=original_length,
            retrieval_method=result.get("retrieval_method", "semantic_match"),
            similarity_score=result.get("similarity_score", 0.5),
            last_updated=result.get("last_updated"),
            simulate_2g_mode=result.get("simulate_2g_mode", False)
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
    """Returns usage statistics and performance metrics"""
    
    # Calculate derived metrics
    total_queries = STATS["total_queries"]
    
    if total_queries > 0:
        cache_hit_ratio = STATS["cache_hits"] / total_queries
        llm_usage_percent = (STATS["llm_calls"] / total_queries) * 100
        avg_response_bytes = STATS["total_response_bytes"] / total_queries
    else:
        cache_hit_ratio = 0.0
        llm_usage_percent = 0.0
        avg_response_bytes = 0
    
    return {
        # Performance metrics
        "cache_hit_ratio": round(cache_hit_ratio, 2),
        "avg_response_bytes": int(avg_response_bytes),
        "llm_usage_percent": round(llm_usage_percent, 1),
        
        # Raw counts
        "total_queries": total_queries,
        "cache_hits": STATS["cache_hits"],
        "llm_calls": STATS["llm_calls"],
        "total_response_bytes": STATS["total_response_bytes"],
        
        # Network breakdown
        "network_breakdown": {
            "2g": STATS["network_2g_queries"],
            "3g": STATS["network_3g_queries"],
            "4g": STATS["network_4g_queries"],
            "unknown": total_queries - (
                STATS["network_2g_queries"] + 
                STATS["network_3g_queries"] + 
                STATS["network_4g_queries"]
            )
        },
        
        # Knowledge base info
        "total_schemes": len(KNOWLEDGE_BASE),
        "categories": list(set(s.get("category", "other") for s in KNOWLEDGE_BASE)),
        "languages_supported": ["hi", "en"]
    }

@app.get("/analytics")
def get_analytics(token: Optional[str] = None):
    """Admin-only analytics dashboard data (simple token auth)"""
    
    # Simple token-based auth (for demo purposes)
    ADMIN_TOKEN = "gramsevak_admin_2024"
    
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized - Invalid token")
    
    # Calculate metrics
    total_queries = STATS["total_queries"]
    
    if total_queries > 0:
        cache_hit_ratio = round(STATS["cache_hits"] / total_queries, 2)
        llm_usage_percent = round((STATS["llm_calls"] / total_queries) * 100, 1)
        offline_percent = round((STATS["offline_queries"] / total_queries) * 100, 1)
    else:
        cache_hit_ratio = 0.0
        llm_usage_percent = 0.0
        offline_percent = 0.0
    
    # Find top category
    top_category = "N/A"
    if STATS["category_counts"]:
        top_category = max(STATS["category_counts"], key=STATS["category_counts"].get)
    
    # Calculate user type distribution percentages
    user_type_distribution = {}
    if total_queries > 0 and STATS["user_type_counts"]:
        for user_type, count in STATS["user_type_counts"].items():
            user_type_distribution[user_type] = round((count / total_queries) * 100, 1)
    
    # Calculate helpful rate
    total_feedback = STATS["total_feedback"]
    helpful_rate = 0.0
    if total_feedback > 0:
        helpful_rate = round((STATS["helpful_count"] / total_feedback) * 100, 1)
    
    return {
        "total_queries": total_queries,
        "cache_hit_ratio": cache_hit_ratio,
        "llm_usage_percent": llm_usage_percent,
        "top_category": top_category,
        "user_type_distribution": user_type_distribution,
        "offline_percent": offline_percent,
        "category_counts": STATS["category_counts"],
        "avg_response_bytes": int(STATS["total_response_bytes"] / total_queries) if total_queries > 0 else 0,
        "network_breakdown": {
            "2g": STATS["network_2g_queries"],
            "3g": STATS["network_3g_queries"],
            "4g": STATS["network_4g_queries"]
        },
        "feedback_stats": {
            "total_feedback": total_feedback,
            "helpful_count": STATS["helpful_count"],
            "not_helpful_count": STATS["not_helpful_count"],
            "helpful_rate": helpful_rate
        },
        "rate_limit_stats": {
            "blocked_attempts": RATE_LIMIT["blocked_attempts"],
            "active_ips": len(RATE_LIMIT["requests"])
        }
    }

class Feedback(BaseModel):
    response_id: str
    is_helpful: bool
    category: Optional[str] = None

@app.post("/feedback")
async def submit_feedback(feedback: Feedback, request: Request):
    """Submit user feedback for a response"""
    
    # Check rate limit (use same limit as queries)
    client_ip = request.client.host
    is_allowed, remaining = check_rate_limit(client_ip, is_admin=False)
    
    if not is_allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": "कृपया थोड़ी देर बाद प्रयास करें"
            }
        )
    
    # Update stats
    STATS["total_feedback"] += 1
    if feedback.is_helpful:
        STATS["helpful_count"] += 1
    else:
        STATS["not_helpful_count"] += 1
    
    print(f"📊 Feedback received: {'👍' if feedback.is_helpful else '👎'} for {feedback.response_id}")
    
    return {
        "success": True,
        "message": "धन्यवाद आपकी प्रतिक्रिया के लिए",
        "total_feedback": STATS["total_feedback"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
