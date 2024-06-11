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

User documentation: <https://storm-fsv-cvut.github.io/smoderp2d-manual/>

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

Run SMODERP2D command line tool from Docker container:

```sh
docker run \
 -v `pwd`:/opt/smoderp2d -w /opt/smoderp2d/ --rm --entrypoint \
 ./bin/start-smoderp2d.py smoderp2d \
 --config tests/config_files/quicktest_stream_rill.ini
```

#### GRASS GIS

Build an image with GRASS GIS support:

```sh
docker build \
 --tag smoderp2d-grass:latest --file docker/grass/Dockerfile .
```

Run SMODERP2D with GRASS GIS provider from Docker container:

```sh
docker run \
 -v `pwd`:/opt/smoderp2d -w /opt/smoderp2d/ --rm --entrypoint \
 ./tests/run_grass_gistest.sh smoderp2d-grass \
 nucice
```

### Run locally

#### Command line

```sh
PYTHONPATH=$PYTHONPATH:`pwd` ./bin/start-smoderp2d.py --config tests/config_files/quicktest_stream_rill.ini
```

#### QGIS

Requirements: QGIS 3.28.10 and higher

Define `QGIS_PLUGINPATH` and `PYTHONPATH` environmental variables in
`Settings -> Options -> System` and restart QGIS.

Than enable SMODERP2D plugin in `Plugins -> Manage and Install Plugins...`.

Alternatively set up environment variables in command line before starting QGIS:

```sh
PYTHONPATH=$PYTHONPATH:`pwd` QGIS_PLUGINPATH=`pwd`/bin/qgis qgis tests/data/nucice/qgis_project.qgz
```
