# api-poc
Preparation:

0. install mysql, create db 's5' and table bucket(with 3 col, id, name, uuid) - can be found in Bucket.py
1. run server by: gunicorn -b 0.0.0.0:8000 vsan:app
2. Now don't use host name, just set a header BucketName instead