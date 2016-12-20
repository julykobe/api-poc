#!/bin/bash
sudo kill `sudo lsof -t -i:8000` > /dev/null 2>&1
source s5_env/bin/activate
cd src && gunicorn -b 0.0.0.0:8000 vsan:app
