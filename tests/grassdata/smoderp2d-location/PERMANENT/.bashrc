test -r ~/.alias && . ~/.alias
PS1='GRASS 7.8.3 (smoderp2d-location):\w > '
grass_prompt() {
    MAPSET_PATH="`g.gisenv get=GISDBASE,LOCATION_NAME,MAPSET separator='/'`"
    LOCATION="$MAPSET_PATH"
    if test -f "$MAPSET_PATH/cell/MASK" && test -d "$MAPSET_PATH/grid3/RASTER3D_MASK" ; then
        echo [2D and 3D raster MASKs present]
    elif test -f "$MAPSET_PATH/cell/MASK" ; then
        echo [Raster MASK present]
    elif test -d "$MAPSET_PATH/grid3/RASTER3D_MASK" ; then
        echo [3D raster MASK present]
    fi
}
PROMPT_COMMAND=grass_prompt
export HOME="/home/martin"
export PATH="/usr/lib/grass78/bin:/usr/lib/grass78/scripts:/home/martin/.grass7/addons/bin:/home/martin/.grass7/addons/scripts:/home/martin/git/gismentors/grass-gis-pokrocily/_static/skripty:/home/martin/.local/bin:/home/martin/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin"
