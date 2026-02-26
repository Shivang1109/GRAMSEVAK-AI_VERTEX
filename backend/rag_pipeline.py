import os
import asyncio
from typing import List, Dict, Optional
import re
import json
from pathlib import Path
from intent_classifier import IntentClassifier
from safety_filter import SafetyFilter

# Initialize safety filter
safety_filter = SafetyFilter()

# Category-based index cache
_category_indices = {}

def load_category_index(category: str) -> List[Dict]:
    """Load category-specific index from file (cached)"""
    global _category_indices
    
    # Return from cache if already loaded
    if category in _category_indices:
        return _category_indices[category]
    
    # Load from file
    indices_dir = Path(__file__).parent / "indices"
    index_file = indices_dir / f"{category}_index.json"
    
    if not index_file.exists():
        print(f"⚠️  Category index not found: {category}")
        return []
    
    try:
        with open(index_file, "r", encoding="utf-8") as f:
            entries = json.load(f)
            _category_indices[category] = entries
            print(f"📂 Loaded {len(entries)} entries for category: {category}")
            return entries
    except Exception as e:
        print(f"❌ Error loading category index {category}: {e}")
        return []

# Enhanced keyword matching with better flexibility
def simple_keyword_match(query: str, knowledge_base: List[Dict]) -> Dict:
    """Fast keyword-based matching with fuzzy search - returns structured data"""
    query_lower = query.lower()
    
    # Expanded keyword mappings (Hindi + English + Hinglish + Common phrases)
    keywords = {
        # Government Schemes
        "किसान": ["pmkisan", "kisan", "farmer", "खेती", "kheti", "agriculture"],
        "उज्ज्वला": ["ujjwala", "gas", "lpg", "cylinder", "सिलेंडर"],
        "आयुष्मान": ["ayushman", "health", "hospital", "इलाज", "ilaj", "treatment"],
        "पेंशन": ["pension", "atal", "retirement", "बुढ़ापा"],
        "नौकरी": ["mgnrega", "job", "work", "काम", "kaam", "employment", "रोजगार"],
        "घर": ["awas", "house", "home", "मकान", "makaan", "housing"],
        "लोन": ["mudra", "loan", "credit", "कर्ज", "karj", "उधार"],
        "राशन": ["ration", "food", "खाना", "अनाज", "grain"],
        "शौचालय": ["toilet", "swachh", "sanitation", "latrine"],
        "बैंक": ["bank", "account", "खाता", "jandhan"],
        
        # Agriculture
        "फसल": ["crop", "खेती", "farming", "बुवाई", "sowing"],
        "बीज": ["seed", "beej", "variety"],
        "खाद": ["fertilizer", "urea", "npk", "manure"],
        "कीड़ा": ["pest", "insect", "disease", "रोग"],
        "पानी": ["water", "irrigation", "सिंचाई", "drip"],
        "मंडी": ["mandi", "market", "price", "भाव", "rate"],
        
        # Health
        "बीमारी": ["disease", "illness", "sick", "बुखार", "fever"],
        "दवा": ["medicine", "tablet", "गोली", "treatment"],
        "डॉक्टर": ["doctor", "hospital", "clinic", "अस्पताल"],
        "टीका": ["vaccine", "vaccination", "immunization"],
        
        # Education
        "पढ़ाई": ["education", "study", "school", "स्कूल"],
        "छात्रवृत्ति": ["scholarship", "financial_aid"],
        "नौकरी": ["job", "employment", "career"],
        
        # Financial
        "पैसा": ["money", "paisa", "rupee", "रुपया"],
        "बचत": ["savings", "save", "deposit"],
        "ब्याज": ["interest", "rate"],
        
        # Common intent words
        "कैसे": ["how", "kaise", "process", "method"],
        "क्या": ["what", "kya", "information"],
        "कितना": ["how much", "kitna", "amount", "quantity"],
        "कहां": ["where", "kahan", "location"],
        "कब": ["when", "kab", "time", "date"],
    }
    
    # Score each entry
    best_match = None
    best_score = 0
    
    for entry in knowledge_base:
        score = 0
        
        # Get all searchable text (support both old and new schema)
        entry_text = (
            entry.get("question_hi", "") + " " + 
            entry.get("summary", entry.get("answer_hi", "")) + " " +
            entry.get("title", entry.get("scheme", "")) + " " +
            " ".join(entry.get("tags", [])) + " " +
            entry.get("category", "") + " " +
            entry.get("subcategory", "") + " " +
            entry.get("eligibility", entry.get("eligibility_hi", ""))
        ).lower()
        
        # 1. Check direct keyword matches
        for hindi_word, eng_words in keywords.items():
            if hindi_word in query_lower:
                for eng_word in eng_words:
                    if eng_word in entry_text:
                        score += 10
        
        # 2. Check question variants (highest priority)
        for variant in entry.get("question_variants", []):
            variant_lower = variant.lower()
            # Exact match
            if variant_lower == query_lower:
                score += 50
            # Partial match
            elif variant_lower in query_lower or query_lower in variant_lower:
                score += 30
            # Word overlap
            else:
                query_words = set(query_lower.split())
                variant_words = set(variant_lower.split())
                overlap = len(query_words & variant_words)
                if overlap > 0:
                    score += overlap * 5
        
        # 3. Check tags
        for tag in entry.get("tags", []):
            if tag.lower() in query_lower:
                score += 15
        
        # 4. Check scheme/title name
        scheme_name = entry.get("title", entry.get("scheme", "")).lower()
        if scheme_name and scheme_name in query_lower:
            score += 20
        
        # 5. Word-by-word matching in question and answer
        query_words = query_lower.split()
        for word in query_words:
            if len(word) > 2:  # Skip very short words
                if word in entry_text:
                    score += 3
        
        # 6. Fuzzy matching for common misspellings
        fuzzy_matches = {
            "kisaan": "kisan",
            "kissan": "kisan",
            "yojna": "yojana",
            "yojana": "scheme",
            "paisa": "money",
            "paise": "money",
        }
        for wrong, correct in fuzzy_matches.items():
            if wrong in query_lower and correct in entry_text:
                score += 8
        
        if score > best_score:
            best_score = score
            best_match = entry
    
    # Return structured match if confidence is reasonable
    if best_match and best_score > 5:
        # Calculate confidence
        match_confidence = min(best_score / 50, 1.0)
        
        # Use confidence_weight from entry if available
        if best_match.get("confidence_weight"):
            entry_confidence = best_match["confidence_weight"]
            final_confidence = min((match_confidence + entry_confidence) / 2, 1.0)
        else:
            final_confidence = match_confidence
        
        # Determine retrieval method based on confidence
        if final_confidence >= 0.7:
            retrieval_method = "direct_match"
        elif final_confidence >= 0.4:
            retrieval_method = "semantic_match"
        else:
            retrieval_method = "semantic_match"  # Low confidence semantic
        
        # Extract structured fields from upgraded schema
        result = {
            "summary": best_match.get("summary", best_match.get("answer_hi", "")),
            "scheme_name": best_match.get("title", best_match.get("scheme", best_match.get("category", "सामान्य"))),
            "source": "keyword_match",
            "confidence": final_confidence,
            "retrieval_method": retrieval_method,
            "similarity_score": best_score / 100,  # Normalize to 0-1
            "last_updated": best_match.get("last_updated")  # Add freshness indicator
        }
        
        # Add optional fields if available
        if best_match.get("eligibility"):
            result["eligibility"] = best_match["eligibility"]
        
        if best_match.get("documents_required"):
            result["documents_required"] = best_match["documents_required"]
        
        if best_match.get("benefits"):
            result["benefits"] = best_match["benefits"]
        
        if best_match.get("official_link"):
            result["official_link"] = best_match["official_link"]
        
        return result
    
    return None

async def answer_query(query_text: str, knowledge_base: List[Dict], category_filter: Optional[str] = None, simulate_2g: bool = False) -> Dict:
    """
    Multi-stage retrieval with safety checks and confidence scoring:
    0. Safety filter check (crisis detection)
    1. Intent classification (category detection)
    2. Load category-specific index (if category detected)
    3. Fast keyword matching
    4. LLM-based answer if no good match (fallback)
    
    Args:
        query_text: User query
        knowledge_base: Full knowledge base (fallback only)
        category_filter: Optional category to filter KB (from intent classifier)
    """
    
    # STAGE 0: Safety Filter Check
    is_crisis, crisis_type, emergency_response = safety_filter.check_safety(query_text)
    
    if is_crisis:
        print(f"⚠️  CRISIS DETECTED: {crisis_type} - Returning emergency response")
        # Return emergency response immediately, DO NOT use LLM
        return emergency_response
    
    # STAGE 1: Load category-specific index if category is specified
    search_kb = knowledge_base  # Default to full KB
    
    if category_filter and category_filter != 'general':
        # Try to load category-specific index
        category_entries = load_category_index(category_filter)
        
        if category_entries:
            search_kb = category_entries
            print(f"🔍 Searching in category index: {category_filter} ({len(search_kb)} entries)")
        else:
            # Fallback to filtering full KB
            filtered_kb = [
                entry for entry in knowledge_base 
                if entry.get('category', '').lower() == category_filter.lower()
            ]
            search_kb = filtered_kb if filtered_kb else knowledge_base
            print(f"🔍 Searching in filtered KB: {category_filter} ({len(search_kb)} entries)")
    else:
        print(f"🔍 Searching in all categories ({len(search_kb)} entries)")
    
    # STAGE 2: Try keyword matching first
    keyword_result = simple_keyword_match(query_text, search_kb)
    
    # Check confidence threshold
    if keyword_result:
        confidence = keyword_result["confidence"]
        
        if confidence >= 0.3:
            # Good confidence - return result as is
            print(f"✅ High confidence match: {confidence:.2f} (Method: {keyword_result['retrieval_method']})")
            return keyword_result
        else:
            # Low confidence - add disclaimer
            print(f"⚠️  Low confidence match: {confidence:.2f} - Adding disclaimer")
            keyword_result["summary"] = (
                keyword_result["summary"] + 
                "\n\n⚠️ यह उत्तर अनुमान आधारित है, कृपया आधिकारिक स्रोत देखें।"
            )
            keyword_result["low_confidence_warning"] = True
            keyword_result["retrieval_method"] = "semantic_match"  # Low confidence = semantic
            return keyword_result
    
    # STAGE 3: Use LLM for complex queries or low confidence matches
    # Skip LLM if in 2G simulation mode
    if simulate_2g:
        print("🐌 2G Mode: Skipping LLM, using best keyword match")
        if keyword_result:
            keyword_result["simulate_2g_mode"] = True
            keyword_result["summary"] = keyword_result["summary"][:200] + "..." if len(keyword_result["summary"]) > 200 else keyword_result["summary"]
            return keyword_result
        else:
            return {
                "summary": "क्षमा करें, 2G मोड में यह जानकारी उपलब्ध नहीं है। कृपया बेहतर नेटवर्क पर पुनः प्रयास करें।",
                "scheme_name": "Unknown",
                "source": "fallback",
                "confidence": 0.0,
                "retrieval_method": "semantic_match",
                "similarity_score": 0.0,
                "simulate_2g_mode": True,
                "last_updated": None
            }
    
    try:
        llm_result = await llm_answer(query_text, search_kb)
        return llm_result
    except Exception as e:
        print(f"⚠️  LLM Error: {e}")
        
        # Fallback: Return best keyword match with fallback flag
        if keyword_result:
            print("📴 Fallback mode: Using best keyword match")
            keyword_result["fallback_mode"] = True
            keyword_result["retrieval_method"] = "semantic_match"
            keyword_result["summary"] = (
                keyword_result["summary"] + 
                "\n\n⚠️ यह उत्तर अनुमान आधारित है, कृपया आधिकारिक स्रोत देखें।"
            )
            return keyword_result
        
        # Ultimate fallback
        return {
            "summary": "क्षमा करें, मुझे इस प्रश्न का उत्तर नहीं मिला। कृपया 1800-180-1551 पर संपर्क करें।",
            "scheme_name": "Unknown",
            "source": "fallback",
            "confidence": 0.0,
            "retrieval_method": "semantic_match",
            "similarity_score": 0.0,
            "fallback_mode": True
        }

async def llm_answer(query_text: str, knowledge_base: List[Dict]) -> Dict:
    """Use Groq API for intelligent answers - returns structured data"""
    
    # Check if Groq API key is available
    groq_api_key = os.getenv("GROQ_API_KEY")
    
    if not groq_api_key:
        # Return a mock response for development
        return {
            "summary": "यह एक परीक्षण उत्तर है। कृपया GROQ_API_KEY सेट करें।",
            "scheme_name": "Test",
            "source": "mock",
            "confidence": 0.5,
            "retrieval_method": "rag_llm",
            "similarity_score": 0.5,
            "last_updated": None
        }
    
    try:
        from groq import Groq
        client = Groq(api_key=groq_api_key)
        
        # Build context from top schemes
        context_schemes = knowledge_base[:10]  # Use top 10 for context
        context = "\n".join([
            f"विषय: {s.get('scheme', s.get('category', 'सामान्य'))}\nप्रश्न: {s.get('question_hi', '')}\nउत्तर: {s.get('answer_hi', '')}"
            for s in context_schemes
        ])
        
        prompt = f"""तुम एक सरकारी योजना सहायक हो। नीचे दिए गए संदर्भ का उपयोग करके प्रश्न का उत्तर दो।

संदर्भ:
{context}

प्रश्न: {query_text}

उत्तर (केवल 3-4 वाक्यों में, सरल हिंदी में):"""
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.1
        )
        
        answer_text = response.choices[0].message.content.strip()
        
        return {
            "summary": answer_text,
            "scheme_name": "AI Generated",
            "source": "groq_llm",
            "confidence": 0.8,
            "retrieval_method": "rag_llm",
            "similarity_score": 0.8,
            "last_updated": None  # LLM responses don't have fixed update date
        }
    
    except Exception as e:
        print(f"LLM Error: {e}")
        raise
