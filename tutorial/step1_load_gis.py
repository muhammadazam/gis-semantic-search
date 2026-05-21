import geopandas as gpd

gdf = gpd.read_file("places.geojson")

print("=== Shape of the data ===")
print(f"Rows: {len(gdf)}  |  Columns: {list(gdf.columns)}\n")

print("=== First 3 places ===")
for _, row in gdf.head(3).iterrows():
    print(f"Name     : {row['name']}")
    print(f"Category : {row['category']}")
    print(f"Location : {row.geometry}")
    print(f"Desc     : {row['description'][:80]}...")
    print()

print("=== Categories in the dataset ===")
print(gdf['category'].value_counts().to_string())
