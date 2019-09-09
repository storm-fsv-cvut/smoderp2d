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

    (GRASS GIS 7.8+ required)

    grass --text -c tests/grassdata/smoderp2d-location/test/

    (data preparation only)

    ./bin/grass/r.smoderp2d/r.smoderp2d.py \
        elevation=w001001 soil=puda soil_type=Novak vegetation=puda \
        vegetation_type=vegetace rainfall_file=tests/data/srazka.txt \
        points=points2 table_soil_vegetation=tabulkytab \
        table_soil_vegetation_code=soilveg stream=tok \
        table_stream_shape=tab_stream_tvar table_stream_shape_code=smoderp \
        maxdt=10 end_time=120 \
        -d pickle_file=/tmp/save.pickle
