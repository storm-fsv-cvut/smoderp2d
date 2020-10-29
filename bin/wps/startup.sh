#!/bin/bash

envsubst '$NGINX_HOST' < /etc/nginx/conf.d/smoderp.template > \
         /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;' &
gunicorn3 -b 127.0.0.1:8081 --workers $((2*`nproc --all`)) \
          --log-syslog  --pythonpath /opt/pywps pywps_app:application

exit 0
