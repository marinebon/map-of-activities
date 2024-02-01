"""
Creating US MBON Map of Activities portal

This notebook creates the US MBON Map of Activities portal.
It harvests information from the [GOOS Bio-Eco portal](https://bioeco.goosocean.org/) and [OBIS](https://obis.org/).
GOOS BioEco collection - https://geonode.goosocean.org/maps/1043
OBIS US MBON collection - https://obis.org/institute/23070

Grab the GOOS BioEco portal US MBON collection

https://geonode.goosocean.org/maps/1043

"""


import folium
import geopandas
import numpy as np
import pandas as pd
import pyobis
import requests

pk = 1043  # Matt's map
url = f"https://geonode.goosocean.org/api/v2/maps/{1043}/local_layers"

data = requests.get(url).json()


def get_original_data(layer):
    # we can use WFS GeoJSON response when https://github.com/iobis/bioeco-geonode/issues/166 is solved.
    url = f"https://geonode.goosocean.org/download/{layer['pk']}"

    fmat = "json"
    url2 = f"https://geonode.goosocean.org/geoserver/ows?service=WFS&version=1.0.0&request=GetFeature&typename=geonode%3A{layer['name']}&outputFormat={fmat}&srs=EPSG%3A4326&format_options=charset%3AUTF-8"

    try:
        gdf = geopandas.read_file(url)
    except Exception as err:
        print(f"Could not read {url=}.\nGot {err}.\nTrying\n{url2}\n")
        gdf = geopandas.read_file(url2)

    return gdf


layers = {layer["name"]: get_original_data(layer) for layer in data}


# Grab OBIS US MBON bounding boxes
# https://obis.org/institute/23070

# Grab OBIS US MBON geohash precision 8 points


combined = pd.DataFrame()

query = pyobis.dataset.search(instituteid="23070")

df = pd.DataFrame(query.execute())

df_meta = pd.DataFrame.from_records(df["results"])

for datasetid in df_meta["id"]:
    dset = pyobis.occurrences.getpoints(datasetid=datasetid).execute()

    meta = pyobis.dataset.get(id=datasetid).execute()["results"][0]
    short_name = meta["url"].split("=")[-1]

    df = pd.DataFrame(dset)

    df["dataset_id"] = datasetid
    df["short_name"] = meta["url"].split("=")[-1]
    df["short_name_group"] = (
        df["short_name"].replace(r"\d", "", regex=True).str.rstrip("_")
    )
    df["url"] = meta["url"].replace(
        "https://www1.usgs.gov/obis-usa/ipt", "https://ipt-obis.gbif.us"
    )
    df["metadata"] = str(meta)
    df["title"] = meta["title"]
    df["abstract"] = meta["abstract"]

    df[["decimalLongitude", "decimalLatitude"]] = pd.DataFrame(
        df["coordinates"].tolist()
    )

    combined = pd.concat([combined, df], ignore_index=True)


# Write OBIS records to a GeoDataFrame.
# To save space only keep a few columns. If we include `abstract` and `metadata` the resultant map/html file is crazy big.

cols = ["title", "url", "short_name", "short_name_group"]

gdf = geopandas.GeoDataFrame(
    combined[cols],
    geometry=geopandas.points_from_xy(
        combined.decimalLongitude, combined.decimalLatitude
    ),
    crs="epsg:4326",
)


# Now make a map with those layers
m = folium.Map(
    tiles=None,
    zoom_start=13,
)


# Base Layers
tiles = "https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}"
gh_repo = "https://github.com/marinebon/map-of-activities"
attr = f'Tiles &copy; Esri &mdash; Sources: GEBCO, NOAA, CHS, OSU, UNH, CSUMB, National Geographic, DeLorme, NAVTEQ, and Esri | <a href="{gh_repo}" target="_blank">{gh_repo}</a>'
folium.raster_layers.TileLayer(
    name="Ocean",
    tiles=tiles,
    attr=attr,
).add_to(m)

folium.raster_layers.TileLayer(
    name="CartoDB",
    tiles="cartodbdark_matter",
).add_to(m)

tiles = "https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Reference/MapServer/tile/{z}/{y}/{x}"
folium.raster_layers.TileLayer(
    tiles=tiles,
    name="OceanRef",
    attr=attr,
    overlay=True,
    control=False,
).add_to(m)

# OBIS - layer per dataset "group" (as defined above - from url)
for name, group in gdf.groupby(by="short_name_group"):
    group["ref"] = [
        f'<a href="{url}" target="_blank">{url}</a>' for url in group["url"]
    ]

    folium.GeoJson(
        data=group,
        name="OBIS: {}".format(name),
        marker=folium.CircleMarker(radius=1, color="green"),
        tooltip=folium.features.GeoJsonTooltip(
            fields=["title"],
            aliases=[""],
        ),
        popup=folium.features.GeoJsonPopup(
            fields=["ref"],
            aliases=[""],
        ),
        show=False,
    ).add_to(m)


# GOOS Bio-Eco layers
for layer in layers.keys():
    name = next(item for item in data if item["name"] == layer)["name"]
    tooltip = next(item for item in data if item["name"] == layer)["title"]
    url = next(item for item in data if item["name"] == layer)["detail_url"]
    # abst    = next(item for item in data if item["name"] == layer)['abstract']
    popup = folium.map.Popup(
        f'<a href="{url}" target="_blank">{url}</a>'
    )  # "<p>{abst}</p>")

    folium.GeoJson(
        data=layers[layer],
        name="BioEco: {}".format(name),
        tooltip=tooltip,
        popup=popup,
        show=False,
    ).add_to(m)

folium.LayerControl(collapsed=True).add_to(m)
m.fit_bounds(m.get_bounds())
m.save("docs/index.html")
