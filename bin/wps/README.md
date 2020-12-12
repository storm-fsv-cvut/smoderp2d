# SMODERP2D Web Processing Service

## Deploy SMODERP2D Demo WPS server using Docker

### Build image

```
docker-compose build
```

### Run container

```
docker-compose up
```

### Call WPS

GetCapabilities:

http://localhost:8080/services/wps?service=wps&request=getcapabilities
    
DescribeProcess:

http://localhost:8080/services/wps?service=wps&request=describeprocess&version=1.0.0&identifier=smoderp1d

http://localhost:8080/services/wps?service=wps&request=describeprocess&version=1.0.0&identifier=smoderp2d
    
Execute (POST):

```
python3 request-template.py --template request-smoderp1d.xml > /tmp/request.xml && \
wget --post-file /tmp/request.xml 'http://localhost:8080/services/wps?' -O -
```
