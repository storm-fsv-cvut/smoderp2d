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
docker build -t smoderp docker/
```

Run SMODERP command line tool from Docker container:

```sh
docker run -v `pwd`:/opt/smoderp2d -w /opt/smoderp2d/ --rm --entrypoint \
 ./bin/start-smoderp2d.py smoderp \
 --config tests/config_files/quicktest.ini
```

### From command line locally

```sh
./bin/start-smoderp2d.py --config tests/config_files/quicktest.ini
```

### From GRASS GIS

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
    rainfall_file=tests/data/rainfall.txt \
    maxdt=30 end_time=40 \
    points=points@PERMANENT \
    table_soil_vegetation=soil_veg_tab_mean@PERMANENT \
    table_soil_vegetation_fieldname=soilveg \
    streams=stream@PERMANENT \
    channel_properties_table=stream_shape@PERMANENT \
    streams_channel_type_fieldname=channel_id \
    output=tests/data/output
```

### From ArcGIS 10.x or Pro

Launch SMODERP2D ArcToolbox from `bin\arcgis` directory.

![SMODERP2D ArcToolbox in action](img/arctoolbox.png?raw=true "SMODERP2D ArcToolbox in action")

### From QGIS

Requirements: QGIS 3.28.10 and higher

Set path to the plugin from command line:

```sh
QGIS_PLUGINPATH=`pwd`/bin/qgis qgis tests/data/qgis_project.qgz
```

or define `QGIS_PLUGINPATH` in `Settings -> Options -> System` and restart QGIS:

![SMODERP2D QGIS settings](img/qgis_settings.png?raw=true "QGIS settings")


And enable SMODERP2D plugin in `Plugins -> Manage and Install Plugins...`.
