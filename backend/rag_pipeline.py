import os
import asyncio
from typing import List, Dict
import re

# Enhanced keyword matching with better flexibility
def simple_keyword_match(query: str, knowledge_base: List[Dict]) -> Dict:
    """Fast keyword-based matching with fuzzy search"""
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
        
        # Get all searchable text
        entry_text = (
            entry.get("question_hi", "") + " " + 
            entry.get("answer_hi", "") + " " +
            entry.get("scheme", "") + " " +
            " ".join(entry.get("tags", [])) + " " +
            entry.get("category", "") + " " +
            entry.get("subcategory", "")
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
        
        # 4. Check scheme name
        scheme_name = entry.get("scheme", "").lower()
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
    
    # Return match if confidence is reasonable
    if best_match and best_score > 5:
        return {
            "answer": best_match["answer_hi"],
            "scheme_name": best_match.get("scheme", best_match.get("category", "सामान्य")),
            "source": "keyword_match",
            "confidence": min(best_score / 50, 1.0)  # Normalize to 0-1
        }
    
    return None

async def answer_query(query_text: str, knowledge_base: List[Dict]) -> Dict:
    """
    Two-stage retrieval:
    1. Fast keyword matching (0ms)
    2. LLM-based answer if no good match (fallback)
    """
    
    # Stage 1: Try keyword matching first
    keyword_result = simple_keyword_match(query_text, knowledge_base)
    
    # Use keyword match if confidence is good enough
    if keyword_result and keyword_result["confidence"] > 0.3:
        return keyword_result
    
    # Stage 2: Use LLM for complex queries or low confidence matches
    try:
        llm_result = await llm_answer(query_text, knowledge_base)
        return llm_result
    except Exception as e:
        # Fallback to best keyword match even if confidence is low
        if keyword_result:
            return keyword_result
        
        # Ultimate fallback
        return {
            "answer": "क्षमा करें, मुझे इस प्रश्न का उत्तर नहीं मिला। कृपया 1800-180-1551 पर संपर्क करें।",
            "scheme_name": "Unknown",
            "source": "fallback",
            "confidence": 0.0
        }

async def llm_answer(query_text: str, knowledge_base: List[Dict]) -> Dict:
    """Use Groq API for intelligent answers"""
    
    # Check if Groq API key is available
    groq_api_key = os.getenv("GROQ_API_KEY")
    
    if not groq_api_key:
        # Return a mock response for development
        return {
            "answer": "यह एक परीक्षण उत्तर है। कृपया GROQ_API_KEY सेट करें।",
            "scheme_name": "Test",
            "source": "mock",
            "confidence": 0.5
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
            "answer": answer_text,
            "scheme_name": "AI Generated",
            "source": "groq_llm",
            "confidence": 0.8
        }
    
    except Exception as e:
        print(f"LLM Error: {e}")
        raise
