# packages ----
if (!require("librarian")){
  install.packages("librarian") }
librarian::shelf(
  dplyr, fs, geojsonsf, glue, here, htmltools, httr2, leaflet,
  mapview, purrr, readr, sf, stringr, tibble, zip,
  cran_repo = "https://cloud.r-project.org")
options(readr.show_col_types = F)

# functions ----
download_obis_activities <- function(){
  obis_url <- "https://raw.githubusercontent.com/MathewBiddle/ioos_code_lab/pyobis/jupyterbook/content/code_gallery/data_access_notebooks/US_MBON_bounding_boxes_20230315.geojson"
  obis_geo <- here("data/obis.geojson")

  download.file(obis_url, obis_geo)
}
# download_obis_activities()

mbon_activities_map <- function(){

  obis_url <- "https://raw.githubusercontent.com/MathewBiddle/ioos_code_lab/pyobis/jupyterbook/content/code_gallery/data_access_notebooks/US_MBON_bounding_boxes_20230315.geojson"

  obis_data <- read_sf(obis_url)
  obis_lbls <- obis_data |>
    rowwise() |>
    mutate(
      title_url = a(href = url, title) |> as.character()) |>
    pull(title_url) |>
    lapply(htmltools::HTML)

  leaflet() |>
    # * basemaps ----
    addProviderTiles(
      providers$Stamen.Toner, group = "Toner") |>
    # add base: blue bathymetry and light brown/green topography
    addProviderTiles(
      "Esri.OceanBasemap",
      options = providerTileOptions(
        variant = "Ocean/World_Ocean_Base"),
      group = "Ocean") |>
    # add reference: placename labels and borders
    addProviderTiles(
      "Esri.OceanBasemap",
      options = providerTileOptions(
        variant = "Ocean/World_Ocean_Reference"),
      group = "Ocean") |>
    # * p2p ----
    addCircleMarkers(
      data = read_sf(here("data/p2p.geojson")),
      group = "Pole to Pole",
      label = ~name, radius = 1) |>
    # * sbc ----
    addPolygons(
      data = read_sf(here("data/sbc.geojson")),
      group = "Santa Barbara Channel") |>
    # * sfl ----
    addPolygons(
      data = read_sf(here("data/sfl.geojson")),
      group = "South Florida") |>
    # * obis ----
    addPolygons(
      data = obis_data,
      group = "OBIS",
      label = obis_lbls,
      popup = obis_lbls) |>
    # * layers ----
    addLayersControl(
      baseGroups = c(
        "Ocean", "Toner"),
      overlayGroups = c(
        "Santa Barbara Channel", "South Florida", "OBIS", "Pole to Pole"),
      options = layersControlOptions(collapsed = FALSE))
}
