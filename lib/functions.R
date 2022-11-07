# packages ----
if (!require("librarian")){
  install.packages("librarian") }
librarian::shelf(
  dplyr, fs, geojsonsf, glue, here, httr2, leaflet,
  mapview, purrr, readr, sf, stringr, tibble, zip)
options(readr.show_col_types = F)

# functions ----
mbon_activities_map <- function(){

  # * activities with spatial ----
  # d <- read_csv(here("data/_activities.csv")) %>%
  #   mutate(
  #     geo       = glue("{dir_data}/{geojson}"),
  #     sf        = map(geo, read_sf),
  #     geom = map(sf, function(x){
  #       st_geometry(x) %>%
  #         st_union()}))

  # * leaflet map ----
  leaflet() %>%
    addProviderTiles(
      providers$Stamen.Toner, group = "Toner") %>%
    addProviderTiles(
      providers$Esri.OceanBasemap, group = "Ocean") %>%
    addCircleMarkers(
      data = read_sf(here("data/p2p.geojson")),
      group = "Pole to Pole",
      label = ~name, radius = 1) %>%
    addPolygons(
      data = read_sf(here("data/sbc.geojson")),
      group = "Santa Barbara Channel") %>%
    addPolygons(
      data = read_sf(here("data/sfl.geojson")),
      group = "South Florida") %>%
    addLayersControl(
      baseGroups = c(
        "Ocean", "Toner"),
      overlayGroups = c(
        "Pole to Pole", "Santa Barbara Channel", "South Florida"),
      options = layersControlOptions(collapsed = FALSE))
}
