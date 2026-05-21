from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, GeoRadius, GeoPoint
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
client = QdrantClient(host="localhost", port=6333)


def search_nearby(query: str, center_lat: float, center_lon: float, radius_m: float, top_k: int = 3):
    query_vector = model.encode(query).tolist()

    # Build a geo filter — only consider places within radius_m metres of center
    geo_filter = Filter(
        must=[
            FieldCondition(
                key="location",
                geo_radius=GeoRadius(
                    center=GeoPoint(lat=center_lat, lon=center_lon),
                    radius=radius_m,
                ),
            )
        ]
    )

    response = client.query_points(
        collection_name="gis_places",
        query=query_vector,
        query_filter=geo_filter,
        limit=top_k,
    )

    print(f'\nQuery : "{query}"')
    print(f"Within: {radius_m/1000:.1f}km of ({center_lat}, {center_lon})")
    print("-" * 55)

    if not response.points:
        print("  No results found within that radius.")
        return

    for r in response.points:
        score_bar = "█" * int(r.score * 20)
        print(f"  {r.payload['name']:<30} score: {r.score:.2f}  {score_bar}")
        print(f"  Category : {r.payload['category']}")
        print()


# --- Scenario: You are standing near Waterloo Station ---
# lat=51.5031, lon=-0.1132

MY_LAT = 51.5031
MY_LON = -0.1132

print("=" * 55)
print("SEARCH WITHOUT SPATIAL FILTER (Step 3 style)")
print("=" * 55)

# Re-run the same query from Step 3 without any filter
query_vector = model.encode("quiet outdoor space to relax").tolist()
response = client.query_points(collection_name="gis_places", query=query_vector, limit=3)
print('\nQuery: "quiet outdoor space to relax"  (no location filter)')
print("-" * 55)
for r in response.points:
    print(f"  {r.payload['name']:<30} score: {r.score:.2f}")
print()

print("=" * 55)
print("SAME SEARCH WITH SPATIAL FILTER (Step 4)")
print("=" * 55)

# Now restrict to 2km radius — Hyde Park is ~3.5km away and disappears
search_nearby(
    query="quiet outdoor space to relax",
    center_lat=MY_LAT,
    center_lon=MY_LON,
    radius_m=2000,
)

# A different query with a tighter radius
search_nearby(
    query="art, culture, and performances",
    center_lat=MY_LAT,
    center_lon=MY_LON,
    radius_m=1500,
)

# Widen the radius to see more results
search_nearby(
    query="quiet outdoor space to relax",
    center_lat=MY_LAT,
    center_lon=MY_LON,
    radius_m=5000,
)
