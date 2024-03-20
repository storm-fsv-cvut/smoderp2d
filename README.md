# SMODERP2D

[![cmd_provider_consistency_test](https://github.com/storm-fsv-cvut/smoderp2d/actions/workflows/cmd_provider.yml/badge.svg?branch=master)](https://github.com/storm-fsv-cvut/smoderp2d/actions/workflows/cmd_provider.yml)
[![grass_provider_consistency_test](https://github.com/storm-fsv-cvut/smoderp2d/actions/workflows/grass_provider.yml/badge.svg?branch=master)](https://github.com/storm-fsv-cvut/smoderp2d/actions/workflows/grass_provider.yml)

Distributed event-based model for surface and subsurface runoff and erosion.

```sh
    @ @ @   @       @     @ @     @ @ @     @ @ @ @  @ @ @    @ @ @
   @        @ @   @ @   @     @   @     @   @        @     @  @     @
   @        @   @   @  @       @  @      @  @        @     @  @     @
     @ @    @       @  @       @  @      @  @ @ @    @ @ @    @ @ @
         @  @       @  @       @  @      @  @        @   @    @
         @  @       @   @     @   @     @   @        @    @   @
    @ @ @   @       @     @ @     @ @ @     @ @ @ @  @     @  @
    \  \  /   / /    \   \  /   \  /    /     /       @ @ @   @ @ @
     \ _\/   /_/      \   \/     \/    /_____/       @     @  @     @
         \__/          \  /      _\___/                    @  @      @
             \____      \/      /                         @   @      @
                  \_____/______/                        @     @      @
                               \                      @       @     @
                                \___________________ @ @ @ @  @ @ @
```

## How to test

Download SMODERP2D source code to your computer.

```sh
git clone https://github.com/storm-fsv-cvut/smoderp2d.git
```

### From Docker container

Build an image:

```sh
docker build \
 --tag smoderp2d:latest --file docker/Dockerfile .
```

Run SMODERP command line tool from Docker container:

```sh
docker run \
 -v `pwd`:/opt/smoderp2d -w /opt/smoderp2d/ --rm --entrypoint \
 ./bin/start-smoderp2d.py smoderp2d \
 --config tests/config_files/quicktest_stream_rill.ini
```

### Run locally

Build and install SMODERP2D Python package:

```sh
pip install .
```

#### Command line

```sh
./bin/start-smoderp2d.py --config tests/config_files/quicktest_stream_rill.ini
```

#### GRASS GIS

Note: GRASS GIS 8.3+ required

Create testing mapset:

```sh
grass --text -c tests/grassdata/smoderp2d-location/test/
```

Run `r.smoderp2d` module:

```sh
./bin/grass/r.smoderp2d/r.smoderp2d.py \
    elevation=dem10m@PERMANENT \
    soil=soils@PERMANENT \
    soil_type_fieldname=SID \
    vegetation=landuse@PERMANENT \
    vegetation_type_fieldname=LandUse \
    rainfall_file=tests/data/rainfall_nucice.txt \
    maxdt=5 end_time=5 \
    points=points@PERMANENT points_fieldname='point_id' \
    table_soil_vegetation=soil_veg_tab_mean@PERMANENT \
    table_soil_vegetation_fieldname=soilveg \
    streams=stream@PERMANENT \
    channel_properties_table=stream_shape@PERMANENT \
    streams_channel_type_fieldname=channel_id \
    output=tests/data/output
```

#### ArcGIS Pro

Launch SMODERP2D ArcToolbox from `bin\arcgis` directory.

![SMODERP2D ArcToolbox in action](img/arctoolbox.png?raw=true "SMODERP2D ArcToolbox in action")

#### QGIS

Requirements: QGIS 3.28.10 and higher

Define `QGIS_PLUGINPATH` and `PYTHONPATH` environmental variables in
`Settings -> Options -> System` and restart QGIS:

![SMODERP2D QGIS settings](img/qgis_settings.png?raw=true "QGIS settings")

Than enable SMODERP2D plugin in `Plugins -> Manage and Install Plugins...`.

Alternatively set up environment variables in command line before starting QGIS:

```sh
PYTHONPATH=`pwd` QGIS_PLUGINPATH=`pwd`/bin/qgis qgis tests/data/nucice/qgis_project.qgz
```

#### Known issue

On MS Windows QGIS plugin suffers by poping-up windows when starting computation.
This can be solved by copying ``core.py`` file located in ``smoderp2d\bin\qgis\grass_patch``
to a GRASS target directory.

GRASS target directory is typically located in:

- ``C:\Program Files\QGIS 3.**.*\apps\grass\grass83\etc\python\grass\script`` in the case that QGIS has been installed by standalone installer, or
- ``C:\OSGeo4W\apps\grass\grass83\etc\python\grass\script`` in the case that QGIS has been installed by OSGeo4W network installer.

Update: This bug has been fixed in GRASS GIS 8.4.
