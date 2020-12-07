# FROM nginx:1.19
FROM ubuntu:18.04

# install requirements
COPY requirements.txt /tmp/requirements.txt
RUN apt-get update && apt-get install --yes software-properties-common gettext-base
RUN add-apt-repository --yes ppa:ubuntugis/ubuntugis-unstable
RUN apt-get update && apt-get install --yes python3-pip python3-pyproj gunicorn3 nginx
RUN python3 -m pip install -r /tmp/requirements.txt

# set up pyWPS
RUN mkdir -p /var/www/wps/outputs
RUN mkdir -p /var/log/pywps
RUN rm /etc/nginx/sites-enabled/default

# run pyWPS Gunicorn
COPY startup.sh /opt/startup.sh
CMD /opt/startup.sh
