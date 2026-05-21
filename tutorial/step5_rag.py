from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, GeoRadius, GeoPoint
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
qdrant = QdrantClient(host="localhost", port=6333)


def retrieve_places(question: str, center_lat: float, center_lon: float, radius_m: float, top_k: int = 4):
    query_vector = model.encode(question).tolist()

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

    response = qdrant.query_points(
        collection_name="gis_places",
        query=query_vector,
        query_filter=geo_filter,
        limit=top_k,
    )

    return response.points


def ask(question: str, center_lat: float, center_lon: float, radius_m: float):
    # Step 1 — retrieve relevant nearby places from Qdrant
    places = retrieve_places(question, center_lat, center_lon, radius_m)

    if not places:
        print("No nearby places found to answer from.")
        return

    # Step 2 — format retrieved places as context for Claude
    context_lines = []
    for p in places:
        loc = p.payload["location"]
        context_lines.append(
            f"- {p.payload['name']} ({p.payload['category']}): "
            f"{p.payload['description']} "
            f"[lat={loc['lat']:.4f}, lon={loc['lon']:.4f}]"
        )
    context = "\n".join(context_lines)

    prompt = f"""You are a helpful local guide. A user is standing near coordinates \
({center_lat}, {center_lon}) and has asked:

"{question}"

Based ONLY on these nearby places retrieved from a GIS database, give a helpful, \
conversational answer. Do not mention or suggest any places not in this list.

Nearby places:
{context}
"""

    print(f'\nQuestion: "{question}"')
    print(f"Searching within {radius_m/1000:.1f}km...\n")

    print("Retrieved these places from Qdrant:")
    for p in places:
        print(f"  [{p.score:.2f}] {p.payload['name']}")

    print("\nPrompt that would be sent to Claude:")
    print("-" * 55)
    print(prompt)
    print("-" * 55)
    print()


# --- Scenario: standing near Waterloo Station ---
MY_LAT = 51.5031
MY_LON = -0.1132

ask(
    question="Where should I take my kids for history and culture?",
    center_lat=MY_LAT,
    center_lon=MY_LON,
    radius_m=2000,
)

ask(
    question="I want somewhere peaceful and quiet to sit and think",
    center_lat=MY_LAT,
    center_lon=MY_LON,
    radius_m=3000,
)

ask(
    question="Where can I get good food and drinks?",
    center_lat=MY_LAT,
    center_lon=MY_LON,
    radius_m=2000,
)
