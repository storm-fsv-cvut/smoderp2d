FROM nginx:1.19

# install requirements
COPY requirements.txt /tmp/requirements.txt
RUN apt-get update && apt-get install --yes python3 python3-pip gunicorn3
RUN python3 -m pip install -r /tmp/requirements.txt

# set up pyWPS
RUN mkdir -p /opt/pywps/processes
RUN mkdir -p /var/www/wps/outputs
WORKDIR /opt/pywps
COPY processes/ processes/
COPY pywps.cfg.template .
COPY pywps_app.py .

# run pyWPS Gunicorn
COPY startup.sh /opt/startup.sh
CMD /opt/startup.sh
