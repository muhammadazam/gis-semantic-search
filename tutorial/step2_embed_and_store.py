import geopandas as gpd
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

# --- 1. Load GIS data ---
gdf = gpd.read_file("places.geojson")
print(f"Loaded {len(gdf)} places from GeoJSON\n")

# --- 2. Load embedding model ---
print("Loading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2")
print("Model ready.\n")

# --- 3. Connect to Qdrant ---
client = QdrantClient(host="localhost", port=6333)

# Create (or recreate) a collection for our GIS places
client.recreate_collection(
    collection_name="gis_places",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
)
print("Qdrant collection 'gis_places' created.\n")

# --- 4. Embed each place and store it ---
points = []

for i, row in gdf.iterrows():
    # Turn the description into a vector
    embedding = model.encode(row["description"]).tolist()

    # GeoJSON uses [longitude, latitude] order — we must swap for Qdrant
    lon = row.geometry.x
    lat = row.geometry.y

    point = PointStruct(
        id=i,
        vector=embedding,
        payload={
            "name": row["name"],
            "category": row["category"],
            "description": row["description"],
            # Qdrant's geo format: dict with "lat" and "lon" keys
            "location": {
                "lat": lat,
                "lon": lon,
            },
        },
    )
    points.append(point)
    print(f"  [{i+1:02d}] Embedded: {row['name']}")

# Upload all points in one batch
client.upsert(collection_name="gis_places", points=points)

print(f"\nDone! Stored {len(points)} places in Qdrant.")
print("\nEach point contains:")
print("  - vector     : 384-dimensional embedding of the description")
print("  - payload    : name, category, description, location {lat, lon}")
