from serve import load_resources, recommend, similar, autocomplete

def print_table(items):
    """Print items in a formatted table"""
    if not items:
        print("(no results)")
        return
    
    print(f"{'product_id':<12} {'product_name':<35} {'category':<22} {'price':>8} {'rating':>6} {'count':>8} {'score':>8}")
    print("-" * 120)
    
    for item in items:
        print(
            f"{item.get('product_id', '')[:12]:<12} "
            f"{item.get('product_name', '')[:35]:<35} "
            f"{item.get('category', '')[:22]:<22} "
            f"₹{item.get('price_num', 0):>7.0f} "
            f"{item.get('rating', 0):>6.1f} "
            f"{item.get('rating_count', 0):>8} "
            f"{item.get('final_score', 0):>8.4f}"
        )

if __name__ == "__main__":
    print("=" * 60)
    print("🔄 Loading models...")
    print("=" * 60)
    
    ok = load_resources()
    
    if ok:
        print("✅ All models loaded successfully!\n")
    else:
        print("⚠️ Load failed\n")
        exit(1)
    
    print("\n" + "=" * 60)
    print("🧪 Testing Recommendation System")
    print("=" * 60)
    
    # Test 1: Personalized Recommendations
    print("\n📌 Test 1: Personalized Recommendations (CF)")
    print("-" * 60)
    items = recommend(user_id="A3SBTW3WS4IQSN", k=5, max_price=25000, category="Mobile")
    print_table(items)
    
    # Test 2: Popular Recommendations (Fallback)
    print("\n📌 Test 2: Popular Recommendations (No User ID)")
    print("-" * 60)
    items = recommend(user_id=None, k=5)
    print_table(items)
    
    # Test 3: Similar Products
    print("\n📌 Test 3: Similar Products")
    print("-" * 60)
    if items:
        test_id = items[0].get('product_id')
        print(f"Finding products similar to: {test_id}")
        similar_items = similar(test_id, k=5)
        print_table(similar_items)
    
    # Test 4: Autocomplete
    print("\n📌 Test 4: Autocomplete")
    print("-" * 60)
    queries = ["samsung", "one", "red", "mobile"]
    for q in queries:
        suggestions = autocomplete(q, k=5)
        print(f"{q:10} → {', '.join(suggestions) if suggestions else '(no suggestions)'}")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed successfully!")
    print("=" * 60)
