# map-of-activities
The US MBON Map of Activities aims to be the entrypoint for users interested in US MBON data.

The map-of-activities jupyter notebook provides an overview of the spatial coverage of extant US MBON data efforts.
Information is in this notebook is harvested from the [GOOS Bio-Eco portal](https://bioeco.goosocean.org/) and [OBIS](https://obis.org/) to create this view.
  * GOOS BioEco US MBON collection : https://geonode.goosocean.org/maps/1043
  * UNESCO OBIS US MBON collection : https://obis.org/institute/23070

## Run Jupyter Notebook
Install conda: <https://docs.conda.io/projects/conda/en/latest/user-guide/install/windows.html>

Create `map-of-activity` environment:
```bash
conda create --file environment.yml
```

Activate environment:
```bash
conda activate map-of-activities
```

Run Jupyter and open notebook to run:
```bash
jupyter nbclassic
```
