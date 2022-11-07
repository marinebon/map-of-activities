# packages ----
source("lib/functions.R")

# paths ----
gdir_upload <- "/Users/bbest/My Drive/projects/mbon-cross/Map of MBON Activities - Upload Form (File responses)/File(s) (File responses)"
dir_upload <- here("data/mbon_uploads")

d <- tibble(
  f = dir_ls(gdir_upload) %>% as.character()) %>%
  mutate(
    b = basename(f)) %>%
  filter(b != "Icon\r") %>%
  mutate(
    to = glue("{dir_upload}/{b}"))
file_copy(d$f, d$to)

# Pole to Pole Sites (Enrique Montes) ----

# * paths ----
p2p_csv    <- glue("{dir_upload}/sites - Enrique Montes.csv")
p2p_geo    <- here("data/p2p.geojson")

# * checks ----
stopifnot(file.exists(p2p_csv))

# * process ----
read_csv(p2p_csv) %>%
  st_as_sf(
    coords = c("lon", "lat"), crs = 4326) %>%
  write_sf(p2p_geo)
