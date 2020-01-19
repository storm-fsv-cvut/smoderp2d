# Experiment SMODERP2D WPS demo server

## Requirements

    pip3 install pywps flask

## How to test

Run demo WPS server

    python3 demo.py

Open http://127.0.0.1:5000

### Execute

Copy test input data to demo server

    (cd ../..;
    zip test.zip tests/test.ini tests/data/rainfall.txt tests/data/nucice.save
    mv test.zip bin/wps/static/data)

Run execute request

    http://127.0.0.1:5000/wps?service=wps&version=1.0.0&request=execute&identifier=smoderp2d&datainputs=input=http://127.0.0.1:5000/static/data/test.zip
