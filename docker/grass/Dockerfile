FROM osgeo/grass-gis:releasebranch_8_3-debian

# install requirements
COPY . /src/smoderp2d
RUN python3 -m pip install --break-system-packages /src/smoderp2d/

RUN apt-get update
# support paralelization for batch processes
RUN apt-get install --yes python3-joblib
# install also pytest to run ./tests/run_grass_gistest.sh
RUN apt-get install --yes python3-pytest