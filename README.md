# SMODERP2D

Distributed event-based model for surface and subsurface runoff and erosion

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

    ./bin/start-smoderp2d.py --typecomp roff --indata tests/test.ini

### From GRASS GIS

Note: GRASS GIS 7.8+ required

Create testing mapset:

    grass --text -c tests/grassdata/smoderp2d-location/test/

Run `r.smoderp2d` module:

    ./bin/grass/r.smoderp2d/r.smoderp2d.py \
        elevation=w001001 soil=puda soil_type=Novak vegetation=puda \
        vegetation_type=vegetace rainfall_file=tests/data/srazka.txt \
        points=points2 table_soil_vegetation=tabulkytab \
        table_soil_vegetation_code=soilveg stream=tok \
        table_stream_shape=tab_stream_tvar table_stream_shape_code=smoderp \
        maxdt=10 end_time=120

### From ArcGIS 10.x or Pro

Launch SMODERP2D ArcToolbox from `bin\arcgis` directory.

![SMODERP2D ArcToolbox in action](img/arctoolbox.png?raw=true "SMODERP2D ArcToolbox in action")
