import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
qdrant = QdrantClient(host="qdrant", port=6333)

COLLECTION = "gis_places"
GEOJSON    = Path(__file__).parent / "places.geojson"


def seed_if_empty():
    collections = [c.name for c in qdrant.get_collections().collections]

    if COLLECTION in collections and qdrant.count(COLLECTION).count > 0:
        print(f"Collection '{COLLECTION}' already has data — skipping seed.")
        return

    print("Seeding Qdrant from places.geojson ...")
    data = json.loads(GEOJSON.read_text())

    qdrant.recreate_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )

    points = []
    for i, feature in enumerate(data["features"]):
        props = feature["properties"]
        lon, lat = feature["geometry"]["coordinates"]
        embedding = model.encode(props["description"]).tolist()
        points.append(PointStruct(
            id=i,
            vector=embedding,
            payload={
                "name": props["name"],
                "category": props["category"],
                "description": props["description"],
                "location": {"lat": lat, "lon": lon},
            },
        ))
        print(f"  embedded: {props['name']}")

    qdrant.upsert(collection_name=COLLECTION, points=points)
    print(f"Seeded {len(points)} places into Qdrant.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_if_empty()
    yield


app = FastAPI(lifespan=lifespan)


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/search")
def search(req: SearchRequest):
    try:
        vector = model.encode(req.query).tolist()
        response = qdrant.query_points(
            collection_name=COLLECTION,
            query=vector,
            limit=req.top_k,
        )
        return {
            "results": [
                {
                    "name": r.payload["name"],
                    "category": r.payload["category"],
                    "score": round(r.score, 3),
                }
                for r in response.points
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
