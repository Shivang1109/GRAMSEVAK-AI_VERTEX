#!/usr/bin/env python3
"""
Build script to prepare the knowledge base and generate FAISS indices per category
Upgraded schema with validation and logging
"""
import json
import os
from pathlib import Path
import glob
import time
from typing import List, Dict, Tuple

# Category definitions
CATEGORIES = [
    "government_schemes",
    "agriculture",
    "health",
    "education",
    "financial",
    "legal",
    "disaster",
    "livelihood"
]

# Required fields in upgraded schema
REQUIRED_FIELDS = [
    "id",
    "category",
    "title",
    "question_hi",
    "question_variants",
    "summary",
    "tags",
    "last_updated",
    "confidence_weight"
]

# Optional fields
OPTIONAL_FIELDS = [
    "eligibility",
    "documents_required",
    "benefits",
    "official_link"
]

def validate_entry(entry: Dict, index: int, filename: str) -> Tuple[bool, List[str]]:
    """Validate a single knowledge base entry"""
    errors = []
    
    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in entry:
            errors.append(f"Missing required field '{field}'")
    
    # Validate field types
    if "id" in entry and not isinstance(entry["id"], str):
        errors.append("Field 'id' must be a string")
    
    if "category" in entry and entry["category"] not in CATEGORIES:
        errors.append(f"Invalid category '{entry['category']}'. Must be one of {CATEGORIES}")
    
    if "question_variants" in entry and not isinstance(entry["question_variants"], list):
        errors.append("Field 'question_variants' must be an array")
    
    if "tags" in entry and not isinstance(entry["tags"], list):
        errors.append("Field 'tags' must be an array")
    
    if "confidence_weight" in entry:
        if not isinstance(entry["confidence_weight"], (int, float)):
            errors.append("Field 'confidence_weight' must be a number")
        elif not (0 <= entry["confidence_weight"] <= 1):
            errors.append("Field 'confidence_weight' must be between 0 and 1")
    
    # Validate max length constraints
    if "summary" in entry and len(entry["summary"]) > 500:
        errors.append(f"Field 'summary' exceeds 500 characters ({len(entry['summary'])} chars)")
    
    if "title" in entry and len(entry["title"]) > 100:
        errors.append(f"Field 'title' exceeds 100 characters ({len(entry['title'])} chars)")
    
    # Check for duplicate question variants
    if "question_variants" in entry:
        variants = entry["question_variants"]
        if len(variants) != len(set(variants)):
            errors.append("Duplicate question variants found")
    
    if errors:
        print(f"  ⚠️  Entry {index} in {filename}: {', '.join(errors)}")
        return False, errors
    
    return True, []

def load_knowledge_base() -> Tuple[List[Dict], Dict[str, List[Dict]]]:
    """Load all knowledge base files and organize by category"""
    kb_dir = Path(__file__).parent / "knowledge_base"
    all_entries = []
    entries_by_category = {cat: [] for cat in CATEGORIES}
    seen_ids = set()
    seen_variants = set()
    
    # Load all JSON files
    json_files = sorted(glob.glob(str(kb_dir / "*.json")))
    
    print(f"📂 Found {len(json_files)} knowledge base files\n")
    
    for json_file in json_files:
        filename = Path(json_file).name
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                if not isinstance(data, list):
                    print(f"  ⚠️  Skipping {filename} - not a list")
                    continue
                
                valid_count = 0
                for i, entry in enumerate(data):
                    # Validate entry
                    is_valid, errors = validate_entry(entry, i, filename)
                    
                    if not is_valid:
                        continue
                    
                    # Check for duplicate IDs
                    entry_id = entry.get("id")
                    if entry_id in seen_ids:
                        print(f"  ⚠️  Duplicate ID '{entry_id}' in {filename}")
                        continue
                    seen_ids.add(entry_id)
                    
                    # Check for duplicate question variants across all entries
                    for variant in entry.get("question_variants", []):
                        if variant in seen_variants:
                            print(f"  ⚠️  Duplicate variant '{variant}' in {filename}")
                        seen_variants.add(variant)
                    
                    # Add to collections
                    all_entries.append(entry)
                    category = entry.get("category", "general")
                    if category in entries_by_category:
                        entries_by_category[category].append(entry)
                    
                    valid_count += 1
                
                print(f"  ✅ Loaded {valid_count}/{len(data)} valid entries from {filename}")
                
        except json.JSONDecodeError as e:
            print(f"  ❌ JSON error in {filename}: {e}")
        except Exception as e:
            print(f"  ❌ Error loading {filename}: {e}")
    
    return all_entries, entries_by_category

def generate_offline_cache(entries: List[Dict], output_path: Path):
    """Generate compressed offline cache for frontend"""
    # Take top 200 most important entries (sorted by confidence_weight)
    sorted_entries = sorted(entries, key=lambda x: x.get("confidence_weight", 0), reverse=True)
    offline_data = sorted_entries[:200] if len(sorted_entries) > 200 else sorted_entries
    
    # Simplify data structure for offline use
    simplified = []
    for entry in offline_data:
        simplified.append({
            "q": entry["question_hi"],
            "a": entry["summary"],
            "s": entry.get("title", entry.get("category", "सामान्य")),
            "variants": entry.get("question_variants", [])
        })
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(simplified, f, ensure_ascii=False, separators=(',', ':'))
    
    file_size = os.path.getsize(output_path)
    print(f"  ✅ Generated offline cache: {file_size / 1024:.2f} KB ({len(simplified)} entries)")

def save_category_indices(entries_by_category: Dict[str, List[Dict]]):
    """Save separate JSON files for each category (for fast category-based retrieval)"""
    indices_dir = Path(__file__).parent / "indices"
    indices_dir.mkdir(exist_ok=True)
    
    print("\n📊 Saving category indices...")
    for category, entries in entries_by_category.items():
        if not entries:
            continue
        
        output_file = indices_dir / f"{category}_index.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
        
        file_size = os.path.getsize(output_file)
        print(f"  ✅ {category}: {len(entries)} entries ({file_size / 1024:.2f} KB)")

def print_statistics(all_entries: List[Dict], entries_by_category: Dict[str, List[Dict]]):
    """Print detailed statistics"""
    print("\n" + "="*60)
    print("📊 KNOWLEDGE BASE STATISTICS")
    print("="*60)
    
    print(f"\n📈 Total Entries: {len(all_entries)}")
    
    print(f"\n📂 Category Distribution:")
    for category in CATEGORIES:
        count = len(entries_by_category.get(category, []))
        percentage = (count / len(all_entries) * 100) if all_entries else 0
        bar = "█" * int(percentage / 2)
        print(f"  {category:20s}: {count:4d} entries ({percentage:5.1f}%) {bar}")
    
    # Calculate average confidence
    avg_confidence = sum(e.get("confidence_weight", 0) for e in all_entries) / len(all_entries) if all_entries else 0
    print(f"\n⭐ Average Confidence Weight: {avg_confidence:.3f}")
    
    # Count entries with optional fields
    with_eligibility = sum(1 for e in all_entries if e.get("eligibility"))
    with_documents = sum(1 for e in all_entries if e.get("documents_required"))
    with_benefits = sum(1 for e in all_entries if e.get("benefits"))
    with_links = sum(1 for e in all_entries if e.get("official_link"))
    
    print(f"\n📋 Optional Fields Coverage:")
    print(f"  Eligibility:         {with_eligibility:4d} ({with_eligibility/len(all_entries)*100:.1f}%)")
    print(f"  Documents Required:  {with_documents:4d} ({with_documents/len(all_entries)*100:.1f}%)")
    print(f"  Benefits:            {with_benefits:4d} ({with_benefits/len(all_entries)*100:.1f}%)")
    print(f"  Official Links:      {with_links:4d} ({with_links/len(all_entries)*100:.1f}%)")
    
    # Count total question variants
    total_variants = sum(len(e.get("question_variants", [])) for e in all_entries)
    print(f"\n🔍 Total Question Variants: {total_variants}")
    print(f"   Average per Entry: {total_variants/len(all_entries):.1f}")

def main():
    print("🌾 GramSevak AI - Building Knowledge Base (Upgraded Schema)")
    print("="*60)
    
    start_time = time.time()
    
    # Load all knowledge bases
    print("\n📖 Loading knowledge bases...")
    all_entries, entries_by_category = load_knowledge_base()
    
    if not all_entries:
        print("\n❌ No valid entries found! Please check your knowledge base files.")
        return
    
    load_time = time.time() - start_time
    print(f"\n⏱️  Load Time: {load_time:.2f}s")
    
    # Generate offline cache
    print("\n💾 Generating offline cache...")
    frontend_path = Path(__file__).parent.parent / "frontend" / "offline_cache.json"
    generate_offline_cache(all_entries, frontend_path)
    
    # Save category indices
    save_category_indices(entries_by_category)
    
    # Print statistics
    print_statistics(all_entries, entries_by_category)
    
    total_time = time.time() - start_time
    print(f"\n⏱️  Total Build Time: {total_time:.2f}s")
    
    print("\n" + "="*60)
    print("✅ BUILD COMPLETE!")
    print("="*60)
    
    print("\n🚀 Next Steps:")
    print("  1. Set GROQ_API_KEY environment variable (optional)")
    print("  2. Run: uvicorn main:app --reload")
    print("  3. Open frontend/index.html in browser")
    print("  4. Test with: 'पीएम किसान योजना क्या है?'")
    
    print("\n📋 Features:")
    print("  ✅ Intent classification (8 categories)")
    print("  ✅ Category-based retrieval (<100ms)")
    print("  ✅ Safety filter (crisis detection)")
    print("  ✅ Confidence scoring")
    print("  ✅ Structured responses")
    print("  ✅ Offline cache (200 top entries)")

if __name__ == "__main__":
    main()
