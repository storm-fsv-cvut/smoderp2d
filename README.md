# SMODERP2D

Distributed event-based model for surface and subsurface runoff and erosion.

```
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

    git clone https://github.com/storm-fsv-cvut/smoderp2d.git

### From command line

    ./bin/start-smoderp2d.py --typecomp roff --indata tests/quicktest.ini

### From GRASS GIS

Note: GRASS GIS 7.8+ required

Create testing mapset:

    grass --text -c tests/grassdata/smoderp2d-location/test/

Run `r.smoderp2d` module:

    ./bin/grass/test_r_smoderp2d.py

### From ArcGIS 10.x or Pro

Launch SMODERP2D ArcToolbox from `bin\arcgis` directory.

![SMODERP2D ArcToolbox in action](img/arctoolbox.png?raw=true "SMODERP2D ArcToolbox in action")

### From QGIS

Quick test (on Linux):

    QGIS_PLUGINPATH=`pwd`/bin/qgis qgis tests/data/projekt.qgs

Enable SMODERP2D plugin in `Plugins -> Manage and Install Plugins...`.
