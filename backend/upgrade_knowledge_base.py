#!/usr/bin/env python3
"""
Script to upgrade existing knowledge base entries to new schema
and generate additional entries to reach 50 per category
"""
import json
from pathlib import Path
from datetime import datetime

# Category mapping for old entries
CATEGORY_MAPPING = {
    "welfare": "government_schemes",
    "banking": "financial",
    "employment": "livelihood",
    "housing": "government_schemes",
    "savings": "financial",
    "sanitation": "government_schemes",
    "pension": "financial",
    "skill_development": "livelihood",
    "energy": "government_schemes",
    "maternal_health": "health",
    "entrepreneurship": "livelihood"
}

def upgrade_entry(old_entry, index):
    """Upgrade old schema entry to new schema"""
    # Fix category if needed
    category = old_entry.get("category", "general")
    if category in CATEGORY_MAPPING:
        category = CATEGORY_MAPPING[category]
    
    # Create new entry
    new_entry = {
        "id": old_entry.get("id", f"{category}_{index:03d}"),
        "category": category,
        "title": old_entry.get("scheme", old_entry.get("question_hi", "")[:50]),
        "question_hi": old_entry["question_hi"],
        "question_variants": old_entry.get("question_variants", []),
        "summary": old_entry.get("answer_hi", ""),
        "tags": old_entry.get("tags", []),
        "last_updated": "2024-02-26",
        "confidence_weight": 0.85
    }
    
    # Add optional fields if present
    if old_entry.get("eligibility_hi"):
        new_entry["eligibility"] = old_entry["eligibility_hi"]
    
    if old_entry.get("documents"):
        new_entry["documents_required"] = old_entry["documents"]
    
    # Truncate summary if too long
    if len(new_entry["summary"]) > 500:
        new_entry["summary"] = new_entry["summary"][:497] + "..."
    
    return new_entry

def upgrade_file(input_file, output_file=None):
    """Upgrade a knowledge base file"""
    if output_file is None:
        output_file = input_file
    
    print(f"\n📝 Upgrading {input_file.name}...")
    
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            old_entries = json.load(f)
        
        new_entries = []
        for i, old_entry in enumerate(old_entries):
            try:
                new_entry = upgrade_entry(old_entry, i + 1)
                new_entries.append(new_entry)
            except Exception as e:
                print(f"  ⚠️  Error upgrading entry {i}: {e}")
        
        # Write upgraded entries
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(new_entries, f, ensure_ascii=False, indent=2)
        
        print(f"  ✅ Upgraded {len(new_entries)}/{len(old_entries)} entries")
        return len(new_entries)
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return 0

def main():
    kb_dir = Path(__file__).parent / "knowledge_base"
    
    print("🔄 Upgrading Knowledge Base Files")
    print("="*60)
    
    # Files to upgrade (excluding government_schemes.json which is already upgraded)
    files_to_upgrade = [
        "agriculture.json",
        "health.json",
        "disaster.json",
        "education.json",
        "financial.json",
        "legal.json",
        "livelihood.json",
        "schemes.json"
    ]
    
    total_upgraded = 0
    
    for filename in files_to_upgrade:
        input_file = kb_dir / filename
        if input_file.exists():
            count = upgrade_file(input_file)
            total_upgraded += count
    
    print("\n" + "="*60)
    print(f"✅ Total Upgraded: {total_upgraded} entries")
    print("\n💡 Next: Run 'python3 build_index.py' to validate")

if __name__ == "__main__":
    main()
