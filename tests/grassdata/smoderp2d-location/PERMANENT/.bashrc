test -r ~/.alias && . ~/.alias
PS1='GRASS 7.7.dev (smoderp2d-location):\W > '
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
export PATH="/home/martin/src/grass-p3/grass/dist.x86_64-pc-linux-gnu/bin:/home/martin/src/grass-p3/grass/dist.x86_64-pc-linux-gnu/scripts:/home/martin/.grass7/addons/bin:/home/martin/.grass7/addons/scripts:/home/martin/src/grass-p2/venv/bin:/home/martin/.local/bin:/home/martin/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin"
export HOME="/home/martin"
