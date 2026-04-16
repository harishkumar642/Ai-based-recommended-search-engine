# backend/test_local.py
from serve import load_resources, recommend, similar, autocomplete

def _print_table(items):
    if not items:
        print("(no results)")
        return
    print("product_id  product_name                      category              price  rating  rating_count  final_score")
    for it in items:
        print(
            f"{it.get('product_id','')[:10]:10}  "
            f"{it.get('product_name','')[:30]:30}  "
            f"{it.get('category','')[:18]:18}  "
            f"{int(it.get('price_num',0)):5d}  "
            f"{it.get('rating',0):>4.1f}   "
            f"{it.get('rating_count',0):>12d}  "
            f"{it.get('final_score',0):>10.4f}"
        )

if __name__ == "__main__":
    print("🔄 Loading models...")
    ok = load_resources()
    print("✅ All models loaded successfully!" if ok else "⚠️ Load failed")

    print("\n🧪 Testing Recommendation System")
    print("=" * 60)

    print("\n1️⃣ Personalized Recommendations (CF)")
    rows = recommend(user_id="A3SBTW3WS4IQSN", k=5, max_price=25000, category="Mobile")
    _print_table(rows)

    print("\n2️⃣ Popular Recommendations (Fallback)")
    rows = recommend(user_id=None, k=5)
    _print_table(rows)

    print("\n3️⃣ Similar Products")
    rows = similar("B07JWH4J1", k=5)
    _print_table(rows)

    print("\n4️⃣ Autocomplete")
    print("samsung →", autocomplete("samsung", k=5))
    print("oneplus →", autocomplete("one", k=5))
