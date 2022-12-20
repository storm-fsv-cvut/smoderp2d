# Deploy SMODERP2D Demo WPS server using Docker

## Build image

```
docker-compose build
```

## Run container

```
docker-compose up
```

## Call WPS

GetCapabilities:

http://localhost:8080/services/wps?service=wps&request=getcapabilities

### profile1d

DescribeProcess:

http://localhost:8080/services/wps?service=wps&request=describeprocess&version=1.0.0&identifier=profile1d

Execute:

```
python3 request-template.py --template request-profile1d.xml > /tmp/request.xml && \
wget --post-file /tmp/request.xml 'http://localhost:8080/services/wps?' -O -
```

### smoderp2d

DescribeProcess:

http://localhost:8080/services/wps?service=wps&request=describeprocess&version=1.0.0&identifier=smoderp2d

Execute:

```
python3 request-template.py --template request-smoderp2d.xml > /tmp/request.xml && \
wget --post-file /tmp/request.xml 'http://localhost:8080/services/wps?' -O -
```

## Restart service on rain1 server

```
cd /opt/smoderp2d/bin/wps
docker-compose down
git pull
docker-compose -f docker-compose-letsencrypt.yml up -d
```
