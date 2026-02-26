"""
Intent Classifier for GramSevak AI
Fast rule-based classifier using keyword mapping (<5ms)
"""

import re
from typing import Dict, Tuple

class IntentClassifier:
    def __init__(self):
        """Initialize keyword mappings for each category"""
        
        # Category keyword mappings (Hindi + English + Hinglish)
        self.category_keywords = {
            'government_schemes': [
                # Hindi
                'योजना', 'सरकारी', 'आवेदन', 'पात्रता', 'लाभ', 'किस्त', 'रजिस्ट्रेशन',
                'प्रधानमंत्री', 'मुख्यमंत्री', 'केंद्र', 'राज्य', 'सब्सिडी', 'अनुदान',
                # English
                'scheme', 'yojana', 'government', 'sarkar', 'apply', 'benefit', 'registration',
                'pm', 'pradhan mantri', 'subsidy', 'grant', 'eligibility', 'patrata',
                # Specific schemes
                'pmkisan', 'pm-kisan', 'kisan', 'ayushman', 'ujjwala', 'jan dhan', 'mgnrega',
                'nrega', 'awas', 'mudra', 'pension', 'scholarship'
            ],
            
            'agriculture': [
                # Hindi
                'खेती', 'फसल', 'किसान', 'बीज', 'खाद', 'कीटनाशक', 'सिंचाई', 'मौसम',
                'बुवाई', 'कटाई', 'मंडी', 'भाव', 'कीड़े', 'रोग', 'जैविक', 'उर्वरक',
                # English
                'farming', 'crop', 'farmer', 'seed', 'fertilizer', 'pesticide', 'irrigation',
                'weather', 'sowing', 'harvest', 'mandi', 'price', 'pest', 'disease', 'organic',
                # Specific crops
                'गेहूं', 'धान', 'चावल', 'मक्का', 'दाल', 'सब्जी', 'टमाटर', 'आलू', 'प्याज',
                'wheat', 'rice', 'paddy', 'maize', 'dal', 'vegetable', 'tomato', 'potato', 'onion'
            ],
            
            'health': [
                # Hindi
                'स्वास्थ्य', 'बीमारी', 'इलाज', 'दवा', 'डॉक्टर', 'अस्पताल', 'बुखार', 'दर्द',
                'खांसी', 'सर्दी', 'पेट', 'चोट', 'प्राथमिक', 'टीका', 'गर्भावस्था', 'बच्चा',
                # English
                'health', 'disease', 'treatment', 'medicine', 'doctor', 'hospital', 'fever',
                'pain', 'cough', 'cold', 'stomach', 'injury', 'first aid', 'vaccine', 'pregnancy',
                # Symptoms
                'बुखार', 'दस्त', 'उल्टी', 'सिरदर्द', 'चक्कर', 'कमजोरी',
                'bukhar', 'dast', 'ulti', 'headache', 'weakness', 'diarrhea'
            ],
            
            'education': [
                # Hindi
                'शिक्षा', 'पढ़ाई', 'स्कूल', 'कॉलेज', 'छात्रवृत्ति', 'परीक्षा', 'कोर्स',
                'प्रशिक्षण', 'कौशल', 'डिग्री', 'सर्टिफिकेट', 'ऑनलाइन', 'पुस्तक',
                # English
                'education', 'study', 'school', 'college', 'scholarship', 'exam', 'course',
                'training', 'skill', 'degree', 'certificate', 'online', 'book', 'learning',
                # Specific
                'साक्षरता', 'व्यावसायिक', 'तकनीकी', 'कंप्यूटर', 'अंग्रेजी',
                'literacy', 'vocational', 'technical', 'computer', 'english'
            ],
            
            'financial': [
                # Hindi
                'पैसा', 'बैंक', 'खाता', 'लोन', 'ब्याज', 'बचत', 'निवेश', 'बीमा',
                'क्रेडिट', 'डेबिट', 'एटीएम', 'चेक', 'ट्रांसफर', 'जमा', 'निकासी',
                # English
                'money', 'bank', 'account', 'loan', 'interest', 'saving', 'investment', 'insurance',
                'credit', 'debit', 'atm', 'cheque', 'transfer', 'deposit', 'withdrawal',
                # Specific
                'upi', 'paytm', 'phonepe', 'gpay', 'bhim', 'netbanking', 'mobile banking',
                'kcc', 'kisan credit', 'mudra', 'microfinance', 'shg'
            ],
            
            'legal': [
                # Hindi
                'कानून', 'अधिकार', 'न्याय', 'वकील', 'कोर्ट', 'केस', 'शिकायत', 'पुलिस',
                'जमीन', 'संपत्ति', 'विवाद', 'दस्तावेज', 'रजिस्ट्री', 'उपभोक्ता',
                # English
                'law', 'legal', 'right', 'justice', 'lawyer', 'court', 'case', 'complaint', 'police',
                'land', 'property', 'dispute', 'document', 'registry', 'consumer',
                # Specific
                'rti', 'fir', 'domestic violence', 'घरेलू हिंसा', 'helpline', 'legal aid',
                'land rights', 'भूमि अधिकार', 'consumer rights', 'उपभोक्ता अधिकार'
            ],
            
            'disaster': [
                # Hindi
                'आपदा', 'बाढ़', 'सूखा', 'भूकंप', 'तूफान', 'आग', 'दुर्घटना', 'आपातकाल',
                'बचाव', 'राहत', 'सुरक्षा', 'चेतावनी', 'निकासी', 'शरण',
                # English
                'disaster', 'flood', 'drought', 'earthquake', 'cyclone', 'fire', 'accident', 'emergency',
                'rescue', 'relief', 'safety', 'warning', 'evacuation', 'shelter',
                # Specific
                'snake bite', 'सांप', 'बिजली', 'lightning', 'storm', 'तूफान',
                'emergency number', 'आपातकालीन नंबर', '108', '112'
            ],
            
            'livelihood': [
                # Hindi
                'रोजगार', 'व्यवसाय', 'काम', 'नौकरी', 'कमाई', 'आय', 'उद्यम', 'स्वरोजगार',
                'दुकान', 'व्यापार', 'बिक्री', 'बाजार', 'ग्राहक', 'मुनाफा',
                # English
                'livelihood', 'business', 'work', 'job', 'earning', 'income', 'enterprise', 'self-employment',
                'shop', 'trade', 'sale', 'market', 'customer', 'profit',
                # Specific
                'मुर्गी पालन', 'डेयरी', 'बकरी', 'मधुमक्खी', 'मशरूम', 'हस्तशिल्प',
                'poultry', 'dairy', 'goat', 'bee', 'mushroom', 'handicraft',
                'small business', 'छोटा व्यवसाय', 'startup', 'women entrepreneurship'
            ]
        }
        
        # Compile regex patterns for faster matching
        self.category_patterns = {}
        for category, keywords in self.category_keywords.items():
            # Create regex pattern with word boundaries
            pattern = '|'.join([re.escape(kw) for kw in keywords])
            self.category_patterns[category] = re.compile(pattern, re.IGNORECASE)
    
    def classify(self, query: str) -> Tuple[str, float]:
        """
        Classify query into a category
        
        Args:
            query: User query text
            
        Returns:
            Tuple of (category, confidence_score)
            category: One of the 8 categories or 'general'
            confidence_score: 0.0 to 1.0
        """
        # Normalize query
        query_lower = query.lower().strip()
        
        # Count matches for each category
        category_scores = {}
        
        for category, pattern in self.category_patterns.items():
            matches = pattern.findall(query_lower)
            if matches:
                # Score based on number of matches and match length
                score = len(matches) + sum(len(m) for m in matches) / 100
                category_scores[category] = score
        
        # If no matches found, return general
        if not category_scores:
            return 'general', 0.0
        
        # Get category with highest score
        best_category = max(category_scores, key=category_scores.get)
        max_score = category_scores[best_category]
        
        # Calculate confidence (normalize to 0-1 range)
        # High confidence if score > 2, medium if > 1, low otherwise
        if max_score >= 3:
            confidence = 0.95
        elif max_score >= 2:
            confidence = 0.85
        elif max_score >= 1:
            confidence = 0.70
        else:
            confidence = 0.50
        
        return best_category, confidence
    
    def get_category_file(self, category: str) -> str:
        """
        Get knowledge base filename for a category
        
        Args:
            category: Category name
            
        Returns:
            Filename (e.g., 'schemes.json')
        """
        category_files = {
            'government_schemes': 'schemes.json',
            'agriculture': 'agriculture.json',
            'health': 'health.json',
            'education': 'education.json',
            'financial': 'financial.json',
            'legal': 'legal.json',
            'disaster': 'disaster.json',
            'livelihood': 'livelihood.json',
            'general': None  # Search all files
        }
        
        return category_files.get(category, None)


# Test function
if __name__ == "__main__":
    classifier = IntentClassifier()
    
    # Test queries
    test_queries = [
        "पीएम किसान योजना क्या है?",
        "टमाटर में कीड़े लगे हैं",
        "बुखार में क्या करें?",
        "UPI कैसे use करें?",
        "RTI कैसे file करें?",
        "बाढ़ में क्या करें?",
        "मुर्गी पालन कैसे शुरू करें?",
        "scholarship के लिए apply कैसे करें?"
    ]
    
    print("Testing Intent Classifier:\n")
    for query in test_queries:
        category, confidence = classifier.classify(query)
        print(f"Query: {query}")
        print(f"Category: {category} (Confidence: {confidence:.2f})")
        print(f"File: {classifier.get_category_file(category)}")
        print("-" * 50)
