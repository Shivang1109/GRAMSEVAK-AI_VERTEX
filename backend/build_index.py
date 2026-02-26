#!/usr/bin/env python3
"""
Build script to prepare the knowledge base and generate offline cache
"""
import json
import os
from pathlib import Path
import glob

def load_schemes():
    """Load all knowledge base files from the knowledge_base directory"""
    kb_dir = Path(__file__).parent / "knowledge_base"
    all_data = []
    
    # Load all JSON files in knowledge_base directory
    json_files = glob.glob(str(kb_dir / "*.json"))
    
    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_data.extend(data)
                    print(f"  ✓ Loaded {len(data)} entries from {Path(json_file).name}")
                else:
                    print(f"  ⚠ Skipping {Path(json_file).name} - not a list")
        except Exception as e:
            print(f"  ✗ Error loading {Path(json_file).name}: {e}")
    
    return all_data

def generate_offline_cache(schemes, output_path):
    """Generate compressed offline cache for frontend"""
    # Take top 200 most important schemes
    offline_data = schemes[:200] if len(schemes) > 200 else schemes
    
    # Simplify data structure for offline use
    simplified = []
    for scheme in offline_data:
        simplified.append({
            "q": scheme["question_hi"],
            "a": scheme["answer_hi"],
            "s": scheme["scheme"],
            "variants": scheme.get("question_variants", [])
        })
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(simplified, f, ensure_ascii=False, separators=(',', ':'))
    
    file_size = os.path.getsize(output_path)
    print(f"✓ Generated offline cache: {file_size / 1024:.2f} KB")

def validate_schemes(schemes):
    """Validate scheme data structure"""
    required_fields = ["id", "scheme", "question_hi", "answer_hi"]
    
    for i, scheme in enumerate(schemes):
        for field in required_fields:
            if field not in scheme:
                print(f"⚠ Warning: Scheme {i} missing field '{field}'")
    
    print(f"✓ Validated {len(schemes)} schemes")

def main():
    print("🌾 GramSevak AI - Building Knowledge Base\n")
    
    # Load all knowledge bases
    print("Loading knowledge bases...")
    schemes = load_schemes()
    print(f"\n✓ Total entries loaded: {len(schemes)}\n")
    
    # Validate
    print("Validating data...")
    validate_schemes(schemes)
    print()
    
    # Generate offline cache
    print("Generating offline cache...")
    frontend_path = Path(__file__).parent.parent / "frontend" / "offline_cache.json"
    generate_offline_cache(schemes, frontend_path)
    print()
    
    # Statistics
    categories = {}
    for s in schemes:
        cat = s.get("category", "other")
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"📊 Statistics:")
    print(f"   Total entries: {len(schemes)}")
    print(f"   Categories:")
    for cat, count in sorted(categories.items()):
        print(f"      • {cat}: {count} entries")
    print(f"   Offline cache: {len(schemes[:200])} entries")
    print()
    
    print("✅ Build complete! Ready to run the backend.")
    print("\n📋 Feature Coverage:")
    print("   ✓ Government Schemes")
    print("   ✓ Agriculture & Farming")
    print("   ✓ Health & Medical")
    print("   ✓ Education & Literacy")
    print("   ✓ Financial Literacy")
    print("   ✓ Legal & Rights")
    print("   ✓ Disaster Preparedness")
    print("   ✓ Livelihood & Skills")
    print("\n🚀 Next steps:")
    print("  1. Set GROQ_API_KEY environment variable (optional)")
    print("  2. Run: uvicorn main:app --reload")
    print("  3. Open frontend/index.html in browser")
    print("  4. Test with: 'पीएम किसान योजना क्या है?'")

if __name__ == "__main__":
    main()
