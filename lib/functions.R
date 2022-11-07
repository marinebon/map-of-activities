# packages ----
if (!require("librarian")){
  install.packages("librarian") }
librarian::shelf(
  dplyr, fs, geojsonsf, glue, here, httr2, leaflet,
  mapview, purrr, readr, sf, stringr, tibble, zip,
  cran_repo = "https://cloud.r-project.org")
options(readr.show_col_types = F)

# functions ----
mbon_activities_map <- function(){

  leaflet() %>%
    # * basemaps ----
    addProviderTiles(
      providers$Stamen.Toner, group = "Toner") %>%
    addProviderTiles(
      providers$Esri.OceanBasemap, group = "Ocean") %>%
    # * p2p ----
    addCircleMarkers(
      data = read_sf(here("data/p2p.geojson")),
      group = "Pole to Pole",
      label = ~name, radius = 1) %>%
    # * sbc ----
    addPolygons(
      data = read_sf(here("data/sbc.geojson")),
      group = "Santa Barbara Channel") %>%
    # * sfl ----
    addPolygons(
      data = read_sf(here("data/sfl.geojson")),
      group = "South Florida") %>%
    # * layers ----
    addLayersControl(
      baseGroups = c(
        "Ocean", "Toner"),
      overlayGroups = c(
        "Pole to Pole", "Santa Barbara Channel", "South Florida"),
      options = layersControlOptions(collapsed = FALSE))
}
