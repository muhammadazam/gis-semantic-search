# GIS Semantic Search — Vector Embeddings Tutorial

A hands-on tutorial project that combines **GIS data**, **vector embeddings**, and **semantic search** to build an interactive map where you can find places by meaning — not just keywords.

> **Example:** Searching *"quiet outdoor space to relax"* surfaces parks and gardens, even though none of those words appear in their descriptions.

---

## What This Project Does

Traditional GIS search is spatial: *"find parks within 1km of this point."*  
This project adds **semantic search**: *"find somewhere peaceful to sit and think, near me."*

The result is a self-hosted map application where a natural language query:
1. Gets converted into a vector embedding
2. Is matched against embedded place descriptions in a vector database
3. Returns semantically similar places, highlighted on an interactive map

---

## Architecture

```
Browser (https://localhost)
        │
        ▼
┌───────────────────────────────────────────────────────┐
│                    Docker Compose                     │
│                                                       │
│  ┌─────────────┐  /api/*   ┌───────────────────────┐ │
│  │    Caddy    │ ────────► │  FastAPI  (search_api) │ │
│  │   (HTTPS)   │           │                        │ │
│  │    :443     │ ◄── HTML ─│  1. auto-seeds Qdrant  │ │
│  └─────────────┘           │  2. embeds queries     │ │
│         ▲                  │  3. returns matches    │ │
│         │ HTTPS            └──────────┬─────────────┘ │
│      Browser                          │ vector search  │
│                            ┌──────────▼─────────────┐ │
│                            │        Qdrant          │ │
│                            │  stores vectors +      │ │
│                            │  GPS coordinates       │ │
│                            └────────────────────────┘ │
└───────────────────────────────────────────────────────┘
                  +
  OpenStreetMap tile CDN  (map background tiles)
```

**On first startup**, the FastAPI container reads `places.geojson`, converts each place description into a 384-dimensional vector embedding using `sentence-transformers`, and stores it in Qdrant alongside the GPS coordinates. Subsequent startups skip this step.

**On each search**, the query text is embedded with the same model, and Qdrant returns the places whose description vectors are most similar (cosine similarity).

---

## Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Compose)

### Run

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
docker compose up --build -d
```

Open your browser and go to:

```
https://localhost
```

> **Browser warning:** Caddy uses a self-signed certificate for local HTTPS. Click **Advanced → Proceed to localhost** to continue. This is expected for local development.

The first startup takes 2–3 minutes while Docker downloads the embedding model (~90 MB). Search will work once the API is ready.

### Stop

```bash
docker compose down
```

---

## Project Structure

```
.
├── docker-compose.yml      # orchestrates all three services
├── Dockerfile.search       # builds the FastAPI search container
├── search_api.py           # FastAPI app — seeds Qdrant, handles search
├── places.geojson          # GIS data — your points of interest
│
├── map/
│   ├── index.html          # the map page (Leaflet.js, vanilla JS)
│   └── Caddyfile           # Caddy config — HTTPS + API proxy
│
└── tutorial/               # step-by-step learning scripts
    ├── step1_load_gis.py       # load and explore GeoJSON with geopandas
    ├── step2_embed_and_store.py # embed descriptions → store in Qdrant
    ├── step3_semantic_search.py # search by meaning
    ├── step4_spatial_filter.py  # combine semantic + geo radius filter
    └── step5_rag.py             # build a RAG prompt for an LLM
```

---

## How It Works — Tutorial Steps

The `tutorial/` scripts walk through each concept individually. To run them, set up a local Python environment:

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# or: source venv/bin/activate  (Mac/Linux)

pip install geopandas qdrant-client sentence-transformers
```

Make sure Qdrant is running first:

```bash
docker compose up qdrant -d
```

Then run the steps in order:

| Script | What you learn |
|--------|---------------|
| `step1_load_gis.py` | Load and explore GeoJSON data with `geopandas` |
| `step2_embed_and_store.py` | Convert descriptions to vectors, store in Qdrant with GPS coords |
| `step3_semantic_search.py` | Search by meaning using natural language queries |
| `step4_spatial_filter.py` | Combine semantic search with a geo radius filter |
| `step5_rag.py` | Build the prompt that would be sent to an LLM (RAG pattern) |

---

## Adding Your Own Points of Interest

All place data lives in `places.geojson`. Each entry follows the standard [GeoJSON](https://geojson.org/) format.

### 1. Find your coordinates

Go to [openstreetmap.org](https://www.openstreetmap.org), right-click any location, and choose **"Show address"** — the URL updates with the coordinates.

Or use [geojson.io](https://geojson.io) to click on a map and get coordinates interactively.

> **Important:** GeoJSON uses `[longitude, latitude]` order — the opposite of what most people expect.

### 2. Add a new feature to `places.geojson`

Open `places.geojson` and add a new object inside the `"features"` array:

```json
{
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [-0.1276, 51.5074]
  },
  "properties": {
    "name": "Your Place Name",
    "category": "cafe",
    "description": "Write a rich, descriptive sentence here. This text is what gets embedded — the more descriptive it is, the better the semantic search will work."
  }
}
```

**Fields:**

| Field | Required | Notes |
|-------|----------|-------|
| `coordinates` | Yes | `[longitude, latitude]` — note the order |
| `name` | Yes | Shown on the map marker popup |
| `category` | Yes | Used for marker colour — see categories below |
| `description` | Yes | **This is the most important field.** It becomes the search embedding. Write 1–3 descriptive sentences about what the place is like, what you do there, and what kind of visitor would enjoy it. |

**Available categories and their colours:**

| Category | Colour |
|----------|--------|
| `park` | Green |
| `hospital` | Red |
| `museum` | Blue |
| `gallery` | Purple |
| `market` | Orange |
| `transport` | Grey |
| `landmark` | Yellow |
| `religious` | Teal |
| `theatre` | Pink |
| `education` | Indigo |
| `arts` | Violet |

To add a new category, also add it to the `COLOURS` object in `map/index.html`.

### 3. Tips for writing good descriptions

The description is embedded into a vector — the richer and more specific it is, the better your search results will be.

**Less useful:**
> "A coffee shop in the city centre."

**More useful:**
> "A cosy independent coffee shop with exposed brick walls, single-origin pour-overs, and communal wooden tables. Popular with remote workers and students looking for a quiet place to focus during the day."

Think about: *Who comes here? What do they do? What does it feel like? What makes it different?*

### 4. Apply your changes

After editing `places.geojson`, you need to reseed Qdrant with the new embeddings:

```bash
# Remove the old Qdrant data volume and rebuild
docker compose down -v
docker compose up --build -d
```

The `-v` flag removes the named volumes (including Qdrant's storage), so the seeder runs fresh with your updated data.

---

## Tech Stack

| Tool | Role |
|------|------|
| [Qdrant](https://qdrant.tech/) | Vector database — stores embeddings and GPS coordinates, handles similarity search |
| [sentence-transformers](https://www.sbert.net/) | Converts text descriptions into 384-dimensional vectors (`all-MiniLM-L6-v2` model) |
| [FastAPI](https://fastapi.tiangolo.com/) | Lightweight Python API — handles search requests from the browser |
| [Leaflet.js](https://leafletjs.com/) | Open-source JavaScript map library |
| [OpenStreetMap](https://www.openstreetmap.org/) | Free map tile provider |
| [Caddy](https://caddyserver.com/) | Web server — serves the map page and proxies API calls over HTTPS |

---

## Troubleshooting

**Search returns no results**  
The Qdrant collection may be empty. Check the `search` container logs:
```bash
docker compose logs search
```
You should see `"Seeded 12 places into Qdrant."` on first run.

**Browser shows a blank map**  
Check that all containers are running:
```bash
docker compose ps
```

**"Proceed to localhost" warning on HTTPS**  
This is expected. Caddy generates a self-signed certificate for local development. Click **Advanced → Proceed to localhost**.

**Port 443 already in use**  
Another service is using port 443. Stop it, or change the port in `docker-compose.yml`:
```yaml
ports:
  - "8443:443"   # access via https://localhost:8443
```
