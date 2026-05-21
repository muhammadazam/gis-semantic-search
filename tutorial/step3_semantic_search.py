from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
client = QdrantClient(host="localhost", port=6333)


def search_places(query: str, top_k: int = 3):
    # Embed the query using the same model we used to embed the descriptions
    query_vector = model.encode(query).tolist()

    response = client.query_points(
        collection_name="gis_places",
        query=query_vector,
        limit=top_k,
    )

    print(f'\nQuery: "{query}"')
    print("-" * 50)
    for r in response.points:
        score_bar = "█" * int(r.score * 20)
        print(f"  {r.payload['name']:<30} score: {r.score:.2f}  {score_bar}")
        print(f"  Category : {r.payload['category']}")
        print(f"  Location : lat={r.payload['location']['lat']:.4f}, lon={r.payload['location']['lon']:.4f}")
        print()


# --- Try several queries and observe the results ---

search_places("quiet outdoor space to relax and enjoy nature")

search_places("I need urgent medical attention")

search_places("ancient history and artefacts")

search_places("live music and performing arts")

search_places("grab a bite to eat and browse local produce")
