# Laboratory 8: Reproducible Geoprocessing, Flask Services, and QGIS WMS/WFS Clients

## Contents
- [Required Dependencies](#required-dependencies)
- [Database Setup](#database-setup)
- [Set up the Virtual Environment](#set-up-the-virtual-environment)
    - [Create a Python Virtual Environment](#create-a-python-virtual-environment)
    - [Install dependencies](#install-dependencies)

- [Configure Environment Variables](#configure-environment-variables)
- [Executing the Python Scripts](#executing-the-python-scripts)
- [Directory Structure](#directory-structure)
- [Data Path Explanations](#data-path-explanations)
- [Author](#author)

## Required Dependencies
Before starting, make sure that you have installed the following dependencies:

- **[Python](https://www.python.org/downloads/) >= 3.14**
- **[pip](https://pip.pypa.io/en/stable/installation/) >= 26.2.1**
- **[PostgreSQL 18](https://www.postgresql.org/download/macosx/)** with **PostGIS** enabled
- `psql` (included with PostgreSQL) and [pgAdmin 4](https://www.pgadmin.org/)
- *(Optional)* **[VSCode](https://code.visualstudio.com/)**

## Database Setup
Run these as a PostgreSQL superuser (on Homebrew/macOS this is usually your OS username). Add `-U <superuser>` to each command if you connect as a different role.

```bash
createdb gisdb
psql -d gisdb -c "CREATE EXTENSION IF NOT EXISTS postgis;"
psql -d gisdb -v ON_ERROR_STOP=1 -f <YOUR_PATH_TO>/GmE205_Lab6_Database_With_Inserts.sql
```

If the application will connect as a different role, grant it access (replace `app_user`):

```bash
psql -d gisdb -c "GRANT USAGE ON SCHEMA lab6 TO app_user;"
psql -d gisdb -c "GRANT SELECT ON ALL TABLES IN SCHEMA lab6 TO app_user;"
```

Verify the load:
```bash
psql -d gisdb \
  -c "SELECT current_database();" \
  -c "SELECT PostGIS_Version();" \
  -c "SELECT parcel_id, land_use, ST_Area(geom) AS area_sqm FROM lab6.parcels ORDER BY parcel_id;"
```

## Set up the Virtual Environment

### Create a Python Virtual Environment
From the project root, create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install Dependencies
Upgrade pip, then install the required packages:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Configure Environment Variables
In your root directory, run the following command:
```bash
cp .env.example .env
```
Then open `.env` and set the values for your PostgreSQL/PostGIS database.

> **Note:** `.env` contains credentials and is listed in `.gitignore`. **Never commit it.**

## Executing the Python Scripts
Make sure PostgreSQL is running and the virtual environment is active, then run the entry-point script from the project root:

```bash
python3 src/run_lab8.py
```
The script writes the result to `output/residential_parcels.geojson`.

To run the Flask API service, run the following script from the project root:
```bash
python3 src/app.py
```


## Directory Structure
```text
├── evidences                       # Screenshots and proof of results
│   └──
├── output                          # Generated artifacts
│   └──
├── src                             # Application source code
│   ├── app.py                          # Flask routes
│   ├── database.py                     # PostgreSQL/PostGIS connection and queries
│   ├── exchange.py                     # Converts database rows/objects to GeoJSON
│   ├── map_renderer.py                 # Provided: map rendering
│   ├── ogc_services.py                 # Provided: OGC service helpers
│   ├── pipeline.py                     # Orchestrates the processing steps
│   ├── run_lab8.py                     # Entry point: wires everything together and writes output/
│   └── spatial.py                      # Domain entities (e.g. Parcel, geometry primitives)
├── .env                            # Local database credentials (not included in commit)
├── .env.example                    # Template for .env
├── .gitignore                      # Files excluded from version control
├── README.md                       # Project overview, setup, and usage instructions
└── requirements.txt                # Pinned/declared third-party dependencies
```

## Data Path Explanations

### *1. What parts of the pipeline were reused from Laboratory 7–8 rather than rewritten?*

The `database.py`, `spatial.py`, and `exchange.py` modules from Laboratory 7 were reused in Laboratory 8. The database module handles the connection to PostgreSQL/PostGIS and retrieves parcel records using a parameterized query. The spatial module converts database rows into `Parcel` objects, while the exchange module converts these objects into a GeoJSON `FeatureCollection` and validates its structure.

Instead of rewriting these functions, Laboratory 8 introduced the `ParcelPipeline` class in `pipeline.py` to coordinate the existing components. The same pipeline is also used by `run_lab8.py` and `app.py`, while the provided `map_renderer.py` and `ogc_services.py` handle the WMS and WFS services.

### *2. Why is ParcelPipeline a useful coordinating object? What should it NOT do?*

`ParcelPipeline` is useful because it organizes the data-processing steps into a single reusable workflow. Its `run()` method retrieves parcel records based on the specified land use, converts them into `Parcel` objects, builds the GeoJSON FeatureCollection, and validates the resulting output. This avoids repeating the same sequence of operations in different scripts or Flask routes.

However, `ParcelPipeline` should not handle database connection configurations, Flask routing, HTTP requests, file saving, or map rendering. These responsibilities belong to their respective modules. Keeping these responsibilities separate makes the system easier to maintain, modify, and reuse.

### *3. Why must we specify stable query ordering when comparing outputs?*

Stable query ordering is necessary to ensure that the records are returned in a predictable sequence. Without an explicit ordering, the database may return the same records in a different order between executions, even when the underlying data has not changed.

In this laboratory, the query uses `ORDER BY parcel_id` to ensure that the parcels are consistently arranged. This allows the two pipeline outputs to be compared reliably. If the same input data and parameters produce the same ordered FeatureCollection, the comparison can confirm that the pipeline is repeatable.

### *4. What is the difference between a saved .geojson file and the Flask endpoint?*

A saved `.geojson` file is a static output that contains the parcel data at the time the pipeline was executed. It can be stored locally, shared, or opened in another GIS application without requiring the Flask server to be running.

On the other hand, the Flask endpoint provides the GeoJSON data through an HTTP request. When a client requests the endpoint, Flask executes the pipeline and returns the resulting data as a response. This allows clients such as QGIS or a browser to retrieve the data directly from the service without manually opening or transferring a file.

The file represents a stored snapshot of the data, while the Flask endpoint provides a way to retrieve the generated data dynamically.

### *5. How do the temporary prints and HTTP responses help locate a failed boundary?*

The temporary print statements and HTTP responses help identify which stage of the workflow is failing. The connection check verifies whether Python can communicate with PostgreSQL/PostGIS. The feature count and first parcel ID help verify whether the database query returned the expected records. The equality check confirms whether repeated pipeline executions produce the same result, while the output path check verifies that the GeoJSON file was successfully saved.

Similarly, HTTP responses help identify problems at the service boundary. The `/health` endpoint checks whether Flask is running, while `/api/parcels` verifies whether the pipeline can produce and return the GeoJSON output. HTTP status codes can also indicate problems, such as unsupported parameters, database connection failures, or errors during data preparation.

These checks make it easier to isolate a problem instead of assuming that the entire workflow failed.

### *6. Compare WMS and WFS in QGIS: What can you inspect in the vector attribute table that you cannot inspect in the rendered WMS image?*

WMS (Web Map Service) delivers a rendered map image of the spatial data. In QGIS, the WMS layer can be viewed and visually interpreted, but its output is primarily an image rather than the original vector features.

WFS (Web Feature Service), on the other hand, delivers actual vector features with their associated geometries and attributes. In QGIS, the WFS layer allows the user to open the attribute table, inspect individual parcel records, view their parcel IDs and land-use classifications, and select or identify individual features.

WMS is primarily used for visual map presentation, while WFS is more suitable for feature inspection and attribute-based analysis. The two services provide different ways of accessing and using the same underlying spatial data.


## 👤 Author
**ALLAN FRITZGERALD N. AMISTOSO** <br>
*2014-73618* <br>
MS Geomatics Engineering - Geoinformatics <br>
University of the Philippines Diliman
