# api-poc
Preparation:

On VM:

0. install mysql, create db 's5' and table bucket(with 3 col, id, name, uuid) - can be found in Bucket.py
1. run server by: gunicorn -b 0.0.0.0:8000 vsan:app
2. Now don't use host name, just set a header BucketName instead
*. you can refer to src/curl.cmd for how to call rest API by curl

On ESXi host:

0. upload code in src_on_host/
1. open firewall for incoming port 10080
2. run OSServer.py

