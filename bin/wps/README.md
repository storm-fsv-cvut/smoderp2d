# SMODERP2D Web Processing Service

## Experimental Rain WPS Process

#### DescribeProcess

https://rain1.fsv.cvut.cz/services/wps?service=wps&version=1.0.0&request=describeprocess&identifier=smoderp2d

#### Execute

https://rain1.fsv.cvut.cz/services/wps?service=wps&version=1.0.0&request=execute&identifier=smoderp2d&datainputs=input=http://rain.fsv.cvut.cz/geodata/smoderp2d.zip

## Development SMODERP2D WPS demo server

### Requirements

    pip3 install pywps flask

### How to test

Run demo WPS server

    python3 demo.py

Open http://127.0.0.1:5000

#### DescribeProcess

http://127.0.0.1:5000/wps?service=wps&version=1.0.0&request=describeprocess&identifier=smoderp2d

#### Execute

Copy testing input data to demo server

    (cd ../..;
    zip test.zip tests/quicktest.ini tests/data/rainfall.txt tests/data/destak.save
    mv test.zip bin/wps/static/data)

Run execute request

http://127.0.0.1:5000/wps?service=wps&version=1.0.0&request=execute&identifier=smoderp2d&datainputs=input=http://127.0.0.1:5000/static/data/test.zip
