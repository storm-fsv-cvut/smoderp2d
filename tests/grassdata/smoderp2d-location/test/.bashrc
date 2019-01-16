test -r ~/.alias && . ~/.alias
PS1='GRASS 7.4.0 (smoderp2d-location):\w > '
grass_prompt() {
	LOCATION="`g.gisenv get=GISDBASE,LOCATION_NAME,MAPSET separator='/'`"
	if test -d "$LOCATION/grid3/G3D_MASK" && test -f "$LOCATION/cell/MASK" ; then
		echo [2D and 3D raster MASKs present]
	elif test -f "$LOCATION/cell/MASK" ; then
		echo [Raster MASK present]
	elif test -d "$LOCATION/grid3/G3D_MASK" ; then
		echo [3D raster MASK present]
	fi
}
PROMPT_COMMAND=grass_prompt
export PATH="/usr/lib/grass74/bin:/usr/lib/grass74/scripts:/home/michael/.grass7/addons/bin:/home/michael/.grass7/addons/scripts:/home/michael/.local/bin:/home/michael/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin:/usr/lib/jvm/java-8-oracle/bin:/usr/lib/jvm/java-8-oracle/db/bin:/usr/lib/jvm/java-8-oracle/jre/bin:/home/michael/job/GOPE/anubis/app/:/home/michael/job/GOPE/QAnubis/gui/QAnubis/"
export HOME="/home/michael"
