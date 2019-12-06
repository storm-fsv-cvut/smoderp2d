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

    ./bin/start-smoderp2d.py --typecomp roff --indata tests/test.ini

### From GRASS GIS

Note: GRASS GIS 7.8+ required

Create testing mapset:

    grass --text -c tests/grassdata/smoderp2d-location/test/

Run `r.smoderp2d` module:

    ./bin/grass/r.smoderp2d/r.smoderp2d.py \
        elevation=dem10m \
        soil=soil_LU soil_type=soil_id \
        vegetation=soil_LU vegetation_type=lu_id \
        rainfall_file=tests/data/rainfall.txt \
        points=points \
        table_soil_vegetation=soil_LU_property table_soil_vegetation_code=soilveg \
        stream=stream \
        table_stream_shape=stream_shape table_stream_shape_code=smoderp \
        maxdt=10 end_time=120 output_dir=/tmp/smoderp2d

### From ArcGIS 10.x or Pro

Launch SMODERP2D ArcToolbox from `bin\arcgis` directory.

![SMODERP2D ArcToolbox in action](img/arctoolbox.png?raw=true "SMODERP2D ArcToolbox in action")
