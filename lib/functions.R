if (!require("librarian")){
  install.packages("librarian") }
librarian::shelf(
  glue, here, leaflet, readr, sf)
options(readr.show_col_types = F)

dir_upload <- "/Users/bbest/My Drive/projects/mbon-cross/Map of MBON Activities - Upload Form (File responses)/File(s) (File responses)"
p2p_csv    <- glue("{dir_upload}/sites - Enrique Montes.csv")

pts_p2p <- read_csv(p2p_csv) %>%
  st_as_sf(
    coords = c("lon", "lat"), crs = 4326)

mbon_map <- function(){
  leaflet() %>%
    addProviderTiles(
      providers$Stamen.Toner, group = "Toner") %>%
    addProviderTiles(
      providers$Esri.OceanBasemap, group = "Ocean") %>%
    addCircleMarkers(
      data = pts_p2p, group = "Pole to Pole",
      label = ~name, radius = 2) %>%
    addLayersControl(
      baseGroups = c("Ocean", "Toner"),
      overlayGroups = c("Pole to Pole"),
      options = layersControlOptions(collapsed = FALSE))
}
