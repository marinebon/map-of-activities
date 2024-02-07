# map-of-activities
The US MBON Map of Activities aims to be the entrypoint for users interested in US MBON data.

The map-of-activities jupyter notebook provides an overview of the spatial coverage of extant US MBON data efforts.
Information is in this notebook is harvested from the [GOOS Bio-Eco portal](https://bioeco.goosocean.org/) and [OBIS](https://obis.org/) to create this view.
  * GOOS BioEco US MBON collection : https://geonode.goosocean.org/maps/1043
  * UNESCO OBIS US MBON collection : https://obis.org/institute/23070

## Run Python code in a conda environment
Install conda: <https://docs.conda.io/projects/conda/en/latest/user-guide/install/windows.html>

Create `map-of-activity` environment:
```bash
conda install conda-lock  # if you don't have conda-lock installed
conda env create --name map-of-activities --file conda-lock.yml
```

Activate environment:
```bash
conda activate map-of-activities
```

Run the code with:
```bash
python map-of-activities.py
```
