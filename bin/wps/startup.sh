#!/bin/bash

envsubst '$NGINX_HOST $NGINX_PORT' < /opt/pywps/pywps.cfg.template > \
         /opt/pywps/pywps.cfg

envsubst '$NGINX_HOST' < /etc/nginx/conf.d/default.conf.template > \
         /etc/nginx/conf.d/default.conf
if test -f /etc/nginx/conf.d/conf.letsencrypt.template; then
    envsubst '$NGINX_HOST' < /etc/nginx/conf.d/conf.letsencrypt.template > \
             /etc/nginx/conf.d/conf.letsencrypt
    envsubst '$NGINX_HOST' < /etc/nginx/conf.d/ssl-parameters.template > \
             /etc/nginx/conf.d/ssl-parameters
    sed -i 's/http/https/g' /opt/pywps/pywps.cfg
fi
nginx -g 'daemon off;' &

gunicorn3 -b 127.0.0.1:8081 --workers $((2*`nproc --all`)) \
          --log-syslog  --pythonpath /opt/pywps pywps_app:application

exit 0
