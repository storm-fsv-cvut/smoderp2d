# SMODERP2D

[![cmd_provider_consistency_test](https://github.com/storm-fsv-cvut/smoderp2d/actions/workflows/cmd_provider.yml/badge.svg?branch=release_1_0)](https://github.com/storm-fsv-cvut/smoderp2d/actions/workflows/cmd_provider.yml)
[![grass_provider_consistency_test](https://github.com/storm-fsv-cvut/smoderp2d/actions/workflows/grass_provider.yml/badge.svg?branch=release_1_0)](https://github.com/storm-fsv-cvut/smoderp2d/actions/workflows/grass_provider.yml)

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
 --config tests/quicktest.ini
```

### From command line locally

```sh
./bin/start-smoderp2d.py --config tests/quicktest.ini
```

### From GRASS GIS

Note: GRASS GIS 8.3+ required

Create testing mapset:

```sh
grass --text -c tests/grassdata/smoderp2d-location/test/
```

Run `r.smoderp2d` module:

```sh
./bin/grass/test_r_smoderp2d.py
```

### From ArcGIS 10.x or Pro

Launch SMODERP2D ArcToolbox from `bin\arcgis` directory.

![SMODERP2D ArcToolbox in action](img/arctoolbox.png?raw=true "SMODERP2D ArcToolbox in action")

### From QGIS

Quick test (on Linux):

```sh
QGIS_PLUGINPATH=`pwd`/bin/qgis qgis tests/data/projekt.qgs
```

Enable SMODERP2D plugin in `Plugins -> Manage and Install Plugins...`.
