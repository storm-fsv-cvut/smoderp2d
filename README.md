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
## Quick test

    ./bin/start-smoderp2d.py --typecomp roff --indata tests/test.ini

## GRASS GIS test

    grass --text tests/grassdata/smoderp2d-location/test/
   
    ./bin/grass/r.smoderp2d/r.smoderp2d.py \
        elevation=w001001 soil=puda soil_type=Novak vegetation=puda \
        vegetation_type=vegetace rainfall_file=tests/data/srazka.txt \
        points=points2 table_soil_vegetation=tabulkytab \
        table_soil_vegetation_code=soilveg streams=tok \
        table_stream_shape=tab_stream_tvar table_stream_shape_code=smoderp
