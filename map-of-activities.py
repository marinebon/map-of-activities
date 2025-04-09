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

from selenium import webdriver
from bs4 import BeautifulSoup
import json


## Build some utilities
# json-ld extractor
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')  # Run Chrome in headless mode
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

def get_ld_json(url: str) -> dict:
    parser = "lxml"

    # browser = webdriver.Chrome(options=chrome_options)
    # browser.get(url)
    # html_source = browser.page_source
    # soup = BeautifulSoup(html_source, parser)

    # faster but sometimes doesn't work
    req = requests.get(url)
    soup = BeautifulSoup(req.text, parser)

    return json.loads("".join(soup.find("script", {"type":"application/ld+json"}).contents))

# read from 'box' and return WKT POLYGON
def box_to_wkt(box_str):
       """Converts a box string to WKT format."""
       try:

           # Assuming box_str is in the format 'north, west, south, east'
           south, west, north, east = map(float, box_str.split(' '))
           # Create WKT polygon string
           wkt_polygon = f'POLYGON(({west} {north}, {east} {north}, {east} {south}, {west} {south}, {west} {north}))'

           return wkt_polygon
       except (ValueError, AttributeError):
           # Handle cases where box_str is not in the expected format or is None
           return None
       
## Get ad-hoc inventory of sampling
def get_inventory():

  #url = 'https://docs.google.com/spreadsheets/d/1jBS8ASS27yV8APZ8Fh-tgX6dHdopwianrUZv0kbKcxw/edit?gid=1698140136#gid=1698140136'

  spreadsheet_id = '1V3_ncujeH_yfqh4OO0_SK4QY3Toej0AYnPwnzaWyp0o'
#sheet_id = '1284796732' # form response
  sheet_id = '1698140136' # inventory of sampling

  url = f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={sheet_id}'

  # url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vRYVhUYypHyVp2JF5Vh5463vNgKiY76U7VgTFPOHHDZkitAN4HY_VgvZrk7gYBA-R0e7l95NEPlmml0/pub?output=csv'

  # sheet = 'Inventory of Sampling'

  #df = get_sheet_data(url,sheet)
  df = pd.read_csv(url, keep_default_na=False)

  # skip empty rows
  df = df.loc[df['Lat (decimal format)']!='']

  gdf_spread = geopandas.GeoDataFrame(
                  df,
                  geometry=geopandas.points_from_xy(
                        df['Lon (decimal format)'], df['Lat (decimal format)']
                    ),
                  crs="epsg:4326",
                )
  return gdf_spread

## Get registration data

def get_registration():

  # url = 'https://docs.google.com/spreadsheets/d/1jBS8ASS27yV8APZ8Fh-tgX6dHdopwianrUZv0kbKcxw/edit?gid=1698140136#gid=1698140136'

  # sheet = 'Form Responses 1'

  # df = get_sheet_data(url, sheet)

  spreadsheet_id = '1V3_ncujeH_yfqh4OO0_SK4QY3Toej0AYnPwnzaWyp0o'
  sheet_id = '1284796732' # form response
  #sheet_id = '1698140136' # inventory of sampling

  url = f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={sheet_id}'

  df = pd.read_csv(url, keep_default_na=False)

  df = df.replace('(?i)yes$',True, regex=True).replace('(?i)no$',False,regex=True)

  df['spatialCoverage'] = pd.Series()

  for index, row in df.loc[df['If yes to above, please include appropriate link(s) here.']!='',['If yes to above, please include appropriate link(s) here.','Dataset title']].iterrows():

    url = row['If yes to above, please include appropriate link(s) here.']
    title = row['Dataset title']

    # Do some initial munging of the data
    if url.startswith('10.154'):
      url = f'https://dx.doi.org/{url}'
      #print(f'{url}\n')

    # elif '\ndata can also be accessed by using the repository\'s API.' in url:
    #   url = url.replace('data can also be accessed by using the repository\'s API.','')
    #   #print(f'{url}\n')

    elif url.endswith('.pdf'):
      continue

    elif 'usf.box.com' in url:
      continue

    elif url == 'https://portal.edirepository.org/nis/mapbrowse?scope=edi&identifier=134':
      url = 'https://portal.edirepository.org/nis/mapbrowse?scope=knb-lter-sbc&identifier=134'

      # has a list of GeoCoordinates

    # See if website has schema.org json-ld. If it doesn't bail out
    #print(f'{url}')
    df.loc[df['Dataset title'] == title, 'url'] = [url]

    try:
      json_ld = get_ld_json(url)
    except:
      print(f'{url} does not have json-ld.')
      continue

    # for sites that have json-ld look for spatial information. NCEI is special
    if 'spatialCoverage' in json_ld.keys():
      if 'ncei' in url:
        spatial = json_ld['spatialCoverage'][0]['geo']
      else:
        spatial = json_ld['spatialCoverage']['geo']
    else:
      print(f'{url} does not have spatial')
      continue

    print(f'{url} has spatial {spatial}')

    # In some cases spatial information is robust - in those cases, only grab the first point.
    if isinstance(spatial, list):
      df.loc[df['Dataset title'] == title, 'spatialCoverage'] = [spatial[0]]
    else:
      df.loc[df['Dataset title'] == title, 'spatialCoverage'] = [spatial]

  # Extract coordinate information from spatialCoverage
  df = pd.concat([df, pd.json_normalize(df['spatialCoverage'])], axis=1)

  # handle 'box' entries
  if 'box' in df.columns:
    temp = df.loc[~df['box'].isna()]
    temp['wkt'] = temp['box'].apply(box_to_wkt)
    df.loc[~df['box'].isna(),'wkt'] = temp['wkt']

  # handle polygon entries
  if 'polygon' in df.columns:#
    temp = df.loc[~df['polygon'].isna()]
    temp['wkt'] = 'POLYGON ((' + temp['polygon'].astype(str) + '))'
    df.loc[~df['polygon'].isna(),'wkt'] = temp['wkt']

  # handle GeoCoordinates
  if not df.loc[df['@type']=='GeoCoordinates'].empty:
    temp = df.loc[df['@type']=='GeoCoordinates', ['latitude','longitude']]
    gdf = geopandas.GeoDataFrame(
        temp, geometry=geopandas.points_from_xy(
            temp['longitude'],
            temp['latitude'])
        )
    df.loc[df['@type']=='GeoCoordinates','geometry'] = gdf['geometry']

  # Convert all WKT to geometry

  temp = df.loc[~df['wkt'].isna()]

  gs = geopandas.GeoSeries.from_wkt(temp['wkt'])

  gdf2 = geopandas.GeoDataFrame(
      temp,
      geometry=gs,
      crs='EPSG:4326'
      )

  df.loc[~df['wkt'].isna(),'geometry'] = gdf2['geometry']

  # Move it all to a GeoDataFrame with crs
  gdf = geopandas.GeoDataFrame(df, geometry=df['geometry'], crs = 'epsg:4326')

  return gdf

## Get BioEco layers
def get_bioeco_data(layer):
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


# Grab OBIS US MBON bounding boxes
# https://obis.org/institute/23070

# Grab OBIS US MBON geohash precision 8 points

## Get OBIS data
def get_obis_data():

  # Grab OBIS US MBON bounding boxes
  # https://obis.org/institute/23070
  # Grab OBIS US MBON geohash precision 8 points
  # Write OBIS records to a GeoDataFrame.
  # To save space only keep a few columns. If we include `abstract` and `metadata` the resultant map/html file is crazy big.

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

      cols = ["title", "url", "short_name", "short_name_group"]

      gdf = geopandas.GeoDataFrame(
          combined[cols],
          geometry=geopandas.points_from_xy(
              combined.decimalLongitude, combined.decimalLatitude
          ),
          crs="epsg:4326",
      )

  return gdf

## Collect all the data

# OBIS
gdf = get_obis_data()

#bio-eco layers
pk = 1043  # Matt's map
url = f"https://geonode.goosocean.org/api/v2/maps/{pk}/local_layers"

data = requests.get(url).json()

layers = {layer["name"]: get_bioeco_data(layer) for layer in data}

# Inventory sheet
gdf_spread = get_inventory()

# Registration sheet
gdf_reg = get_registration()


# Now make a map with those layers
## Initialize map
m = folium.Map(
    tiles=None,
    zoom_start=13,
)


## Add base Layers
tiles = "https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}"
gh_repo = "https://github.com/marinebon/map-of-activities"
attr = f'Tiles &copy; Esri &mdash; Sources: GEBCO, NOAA, CHS, OSU, UNH, CSUMB, National Geographic, DeLorme, NAVTEQ, and Esri | <a href="{gh_repo}" target="_blank">{gh_repo}</a>'
folium.raster_layers.TileLayer(
    name="Ocean",
    tiles=tiles,
    attr=attr,
).add_to(m)

# folium.raster_layers.TileLayer(
#     name="CartoDB",
#     tiles="cartodbdark_matter",
# ).add_to(m)

tiles = "https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Reference/MapServer/tile/{z}/{y}/{x}"
folium.raster_layers.TileLayer(
    tiles=tiles,
    name="OceanRef",
    attr=attr,
    overlay=True,
    control=False,
).add_to(m)


## Add OBIS - layer per dataset "group" (as defined above - from url)
#

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
        show=True,
    ).add_to(m)


## Add GOOS Bio-Eco layers

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
        show=True,
    ).add_to(m)


# ## Add inventory data from Google Spreasheet
#
for name, group in gdf_spread.groupby(by="MBON Project"):
    # group["ref"] = [
    #     f'<a href="{url}" target="_blank">{url}</a>' for url in group["url"]
    # ]

    folium.GeoJson(
        data=group,
        name="Spreadsheet Registration: {}".format(name),
        marker=folium.CircleMarker(radius=5, color="red"),
        tooltip=folium.features.GeoJsonTooltip(
            fields=["MBON Project"],
            aliases=[""],
        ),
        popup=folium.features.GeoJsonPopup(
            fields=["Stations Name/ID"],
            aliases=[""],
        ),
        show=True,
    ).add_to(m)

## Add registration data from Google Spreasheet
style1 = {'fillColor': '#228B22', 'color': '#228B22'}
#style2 = {'fillColor': '#00FFFFFF', 'lineColor': '#00FFFFFF'}

for name, group in gdf_reg[~gdf_reg['geometry'].isna()].groupby(by="Dataset title"):
    group["ref"] = [
        f'<a href="{url}" target="_blank">{url}</a>' for url in group["url"]
    ]

    folium.GeoJson(
        data=group,
        name="Spreadsheet Inventory: {}".format(name),
        #marker=folium.CircleMarker(radius=5, color="red"),
        tooltip=folium.features.GeoJsonTooltip(
            fields=["Dataset title"],#,'spatialCoverage','wkt','If yes to above, please include appropriate link(s) here.'],
            aliases=[""],
        ),
        popup=folium.features.GeoJsonPopup(
            fields=["ref"],
            aliases=[""],
        ),
        show=True,
        style_function=lambda x:style1,
    ).add_to(m)

## Configure the map
folium.LayerControl(collapsed=True).add_to(m)
m.fit_bounds(m.get_bounds())
m.save("docs/index.html")
