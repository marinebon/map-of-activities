# packages ----
source("lib/functions.R")

# paths ----
goos_api <- "https://geonode.goosocean.org/api/v2"
goos_ows <- "https://geonode.goosocean.org/geoserver/ows"
goos_dl  <- "https://geonode.goosocean.org/download"

dir_dl    <- here("data/goosocean_downloads")
d_csv     <- glue("{dir_dl}/_datasets.csv")
d_key_csv <- glue("{dir_dl}/_datasets_key.csv") # manually fill in ds_key

# functions ----
dl_goos <- function(pk, alternate, ...){

  key <- str_remove(alternate, "^geonode:")

  message(glue("{pk} -> {key}"))

  dl_url <- glue("{goos_dl}/{pk}")
  dl_zip <- glue("{dir_dl}/{key}.zip")
  dl_dir <- path_ext_remove(dl_zip)
  r <- try(
    download.file(
      url      = dl_url,
      destfile = dl_zip))
  if (inherits(r, "try-error"))
    return(F)
  unzip(dl_zip, exdir = dl_dir)
  file_delete(dl_zip)
  return(T)
}

goos_sf <- function(alternate, ...){
  # alternate = d$alternate[[4]]

  req_geo <- request(goos_ows) %>%
    req_url_query(
      service      = "WFS",
      version      = "1.0.0",
      request      = "GetFeature",
      typename     = alternate,
      outputFormat = "json",
      srs          = "EPSG:4326",
      srsName      = "EPSG:4326")

  message(glue("alternate:\n\t{alternate}\nreq_geo$url:\n\t{req_geo$url}"))
  r <- try(suppressWarnings(geojson_sf(req_geo$url)))
  if (inherits(r, "try-error"))
    return(NA)
  return(r)
}

# fetch datasets ----
#   programmatic version of [Search "MBON" at GOOS BioEco GeoNode](https://geonode.goosocean.org/search/?title__icontains=MBON&abstract__icontains=MBON&purpose__icontains=MBON&f_method=or&limit=5&offset=0)
d_json <- request(goos_api) %>%
  req_url_path_append("resources") %>%
  req_url_query(
    search        = "MBON",
    search_fields = "title",
    search_fields = "abstract") %>%
  req_perform() %>%
  resp_body_json()

# extract relevant fields from nested list,
#   including URL `detail_url` and package id `pk`
d <- tibble(
  r          = d_json$resources,
  title      = map_chr(r, "title"),
  abstract   = map_chr(r, "abstract"),
  detail_url = map_chr(r, "detail_url"),
  alternate  = map_chr(r, "alternate"),
  pk         = map_chr(r, "pk") %>% as.integer()) %>%
  select(-r)
write_csv(d, d_csv)
#  d <- read_csv(d_csv)

# match dataset key `ds_key` ----
stopifnot(file.exists(d_key_csv))
# manually assigned ds_key column from copy of _datasets.csv

d_key <- read_csv(d_key_csv) %>%
  filter(
    !is.na(ds_key))
# e.g., pk=662 has ds_key=NA since duplicative with
#   process_uploads.R: Pole to Pole Sites (Enrique Montes)

d <- d %>%
  inner_join(
    d_key %>%
      select(pk, ds_key),
    by = "pk")

# get spatial for datasets ----

# initially try to download and read as spatial features
d <- d %>%
  mutate(
    dl = map2_lgl(pk, alternate, dl_goos),
    sf = map(alternate, goos_sf))

# for those datasets in which the first method dl_goos() failed,
#   use alternative method of forming the url to the geojson file
d %>%
  filter(!is.na(sf)) %>%
  pwalk(function(sf, ds_key, ...){
    ds_geo <- here(glue("data/{ds_key}.geojson"))
    write_sf(sf, ds_geo, delete_dsn = T)
  })
d %>%
  filter(is.na(sf)) %>%
  pwalk(function(alternate, ds_key, ...){

    key    <- str_remove(alternate, "^geonode:")
    dl_dir <- glue("{dir_dl}/{key}")
    ds_geo <- here(glue("data/{ds_key}.geojson"))

    shp <- dir_ls(dl_dir, glob = "*.shp")[1]

    read_sf(shp) %>%
      write_sf(ds_geo, delete_dsn = T)
  })
