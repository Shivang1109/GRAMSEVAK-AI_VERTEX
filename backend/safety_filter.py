"""
Safety Filter for GramSevak AI
Detects emergency/crisis queries and returns predefined safe responses
Prevents LLM hallucination on sensitive topics
"""

import re
from typing import Dict, Optional, Tuple

class SafetyFilter:
    def __init__(self):
        """Initialize safety keywords for crisis detection"""
        
        # Crisis keywords (Hindi + English + Hinglish)
        self.crisis_keywords = {
            'suicide': [
                # Hindi
                'आत्महत्या', 'खुदकुशी', 'मरना चाहता', 'मरना चाहती', 'जीना नहीं',
                'जान देना', 'मौत', 'खुद को मार', 'जहर खा', 'फांसी',
                # English
                'suicide', 'kill myself', 'end my life', 'want to die', 'death wish',
                'suicidal', 'hanging', 'jump off', 'overdose',
                # Hinglish
                'khudkushi', 'marna chahta', 'jaan dena', 'zindagi khatam'
            ],
            
            'poison': [
                # Hindi
                'जहर', 'विष', 'कीटनाशक पी', 'दवा की ओवरडोज', 'जहर खा',
                'रासायनिक', 'जहरीला', 'नशा',
                # English
                'poison', 'poisoning', 'toxic', 'pesticide drink', 'chemical ingestion',
                'rat poison', 'insecticide drink',
                # Hinglish
                'zeher', 'vish', 'keetnaashak pee'
            ],
            
            'overdose': [
                # Hindi
                'दवा की अधिक मात्रा', 'गोलियां खा ली', 'बहुत सारी दवा',
                'नशीली दवा', 'ड्रग्स ओवरडोज',
                # English
                'overdose', 'too many pills', 'drug overdose', 'medication overdose',
                'sleeping pills', 'tablet overdose',
                # Hinglish
                'dawai ki adhik matra', 'goliya kha li', 'pills overdose'
            ],
            
            'violence': [
                # Hindi
                'मारपीट', 'हिंसा', 'घरेलू हिंसा', 'पति मारता', 'पत्नी को मारना',
                'बच्चे को मारना', 'शारीरिक हिंसा', 'यौन हिंसा', 'बलात्कार',
                'मुझे मारता', 'मुझे पीटता', 'मार खाती', 'पीटता है',
                # English
                'violence', 'domestic violence', 'physical abuse', 'beating',
                'assault', 'rape', 'sexual violence', 'abuse', 'beats me', 'hitting me',
                # Hinglish
                'marpeet', 'hinsa', 'ghar ki hinsa', 'pati maarta', 'mujhe maarta'
            ],
            
            'self_harm': [
                # Hindi
                'खुद को चोट', 'खुद को काटना', 'खुद को जलाना', 'नुकसान पहुंचाना',
                # English
                'self harm', 'cut myself', 'hurt myself', 'burn myself',
                'self injury', 'cutting',
                # Hinglish
                'khud ko chot', 'khud ko kaatna'
            ]
        }
        
        # Compile regex patterns for faster matching
        self.crisis_patterns = {}
        for category, keywords in self.crisis_keywords.items():
            pattern = '|'.join([re.escape(kw) for kw in keywords])
            self.crisis_patterns[category] = re.compile(pattern, re.IGNORECASE)
    
    def check_safety(self, query: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Check if query contains crisis/emergency keywords
        
        Args:
            query: User query text
            
        Returns:
            Tuple of (is_crisis, crisis_type, emergency_response)
            - is_crisis: True if crisis detected
            - crisis_type: Type of crisis (suicide, poison, etc.)
            - emergency_response: Predefined safe response dict
        """
        query_lower = query.lower().strip()
        
        # Check each crisis category
        for category, pattern in self.crisis_patterns.items():
            if pattern.search(query_lower):
                # Crisis detected - return emergency response
                emergency_response = self._get_emergency_response(category)
                return True, category, emergency_response
        
        # No crisis detected
        return False, None, None
    
    def _get_emergency_response(self, crisis_type: str) -> Dict:
        """
        Get predefined emergency response for crisis type
        
        Args:
            crisis_type: Type of crisis detected
            
        Returns:
            Structured emergency response dict
        """
        
        # Base emergency response
        base_response = {
            "summary": "",
            "scheme_name": "आपातकालीन सहायता",
            "source": "safety_filter",
            "confidence": 1.0,
            "emergency_helplines": [
                {
                    "name": "राष्ट्रीय आपातकालीन नंबर",
                    "number": "112",
                    "description": "सभी आपातकालीन सेवाओं के लिए"
                },
                {
                    "name": "एम्बुलेंस सेवा",
                    "number": "108",
                    "description": "चिकित्सा आपातकाल"
                }
            ]
        }
        
        # Category-specific responses
        if crisis_type == 'suicide':
            base_response["summary"] = """🚨 आपातकालीन सहायता

यदि आप या कोई परेशानी में है, तो कृपया तुरंत मदद लें:

📞 तुरंत संपर्क करें:
• राष्ट्रीय आपातकालीन: 112
• मानसिक स्वास्थ्य हेल्पलाइन: 08046110007
• वंदरेवाला फाउंडेशन: 9999666555

आप अकेले नहीं हैं। मदद उपलब्ध है। कृपया किसी विश्वसनीय व्यक्ति से बात करें।"""
            
            base_response["emergency_helplines"].extend([
                {
                    "name": "मानसिक स्वास्थ्य हेल्पलाइन",
                    "number": "08046110007",
                    "description": "24x7 परामर्श सेवा"
                },
                {
                    "name": "वंदरेवाला फाउंडेशन",
                    "number": "9999666555",
                    "description": "संकट परामर्श"
                }
            ])
        
        elif crisis_type == 'poison' or crisis_type == 'overdose':
            base_response["summary"] = """🚨 जहर/ओवरडोज आपातकाल

तुरंत कार्रवाई करें:

1️⃣ तुरंत एम्बुलेंस बुलाएं: 108 या 112
2️⃣ व्यक्ति को उल्टी न कराएं (जब तक डॉक्टर न कहे)
3️⃣ व्यक्ति को करवट पर लिटाएं
4️⃣ जहर/दवा की बोतल साथ रखें
5️⃣ नजदीकी अस्पताल जाएं

📞 आपातकालीन नंबर:
• एम्बुलेंस: 108
• राष्ट्रीय आपातकालीन: 112
• पॉइजन कंट्रोल: 1800-11-4088"""
            
            base_response["emergency_helplines"].append({
                "name": "पॉइजन कंट्रोल सेंटर",
                "number": "1800-11-4088",
                "description": "जहर संबंधी आपातकाल"
            })
        
        elif crisis_type == 'violence':
            base_response["summary"] = """🚨 हिंसा/दुर्व्यवहार सहायता

आप सुरक्षित हैं। मदद उपलब्ध है:

📞 तुरंत संपर्क करें:
• पुलिस: 100 या 112
• महिला हेल्पलाइन: 181
• चाइल्ड हेल्पलाइन: 1098

🛡️ सुरक्षा कदम:
1. सुरक्षित स्थान पर जाएं
2. पुलिस को सूचित करें
3. चोट लगी हो तो अस्पताल जाएं
4. विश्वसनीय व्यक्ति को बताएं

कानूनी सहायता और परामर्श उपलब्ध है।"""
            
            base_response["emergency_helplines"].extend([
                {
                    "name": "पुलिस",
                    "number": "100",
                    "description": "कानून व्यवस्था"
                },
                {
                    "name": "महिला हेल्पलाइन",
                    "number": "181",
                    "description": "महिलाओं के लिए 24x7"
                },
                {
                    "name": "चाइल्ड हेल्पलाइन",
                    "number": "1098",
                    "description": "बच्चों की सुरक्षा"
                }
            ])
        
        elif crisis_type == 'self_harm':
            base_response["summary"] = """🚨 मानसिक स्वास्थ्य सहायता

कृपया तुरंत मदद लें:

📞 हेल्पलाइन:
• मानसिक स्वास्थ्य: 08046110007
• आपातकालीन: 112
• वंदरेवाला: 9999666555

आप अकेले नहीं हैं। पेशेवर मदद उपलब्ध है।

🏥 नजदीकी:
• सरकारी अस्पताल जाएं
• मनोचिकित्सक से मिलें
• परिवार/दोस्त को बताएं"""
            
            base_response["emergency_helplines"].append({
                "name": "मानसिक स्वास्थ्य हेल्पलाइन",
                "number": "08046110007",
                "description": "24x7 परामर्श"
            })
        
        return base_response


# Test function
if __name__ == "__main__":
    filter = SafetyFilter()
    
    # Test queries
    test_queries = [
        "मैं आत्महत्या करना चाहता हूं",
        "जहर कैसे पीऊं",
        "पति मुझे मारता है",
        "बहुत सारी गोलियां खा ली",
        "पीएम किसान योजना क्या है?",  # Safe query
        "खेती में कीड़े लगे हैं"  # Safe query
    ]
    
    print("Testing Safety Filter:\n")
    for query in test_queries:
        is_crisis, crisis_type, response = filter.check_safety(query)
        print(f"Query: {query}")
        if is_crisis:
            print(f"⚠️  CRISIS DETECTED: {crisis_type}")
            print(f"Emergency Response: {response['summary'][:100]}...")
        else:
            print("✅ Safe query - proceed with normal retrieval")
        print("-" * 70)
