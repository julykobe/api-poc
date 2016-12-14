import json
import logging
import falcon

from Bucket import Bucket
from Object import Object

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import getMysqlConnectionString

engine = create_engine(getMysqlConnectionString())
DBSession = sessionmaker(bind=engine)
session = DBSession()

class AuthZCheck(object):

    def process_request(self, req, resp):
        authStr = req.get_header('Authorization')
        authId = self.convertAuthStrToAuthId(authStr)
        req.context['Authorization'] = authId 

    def convertAuthStrToAuthId(self, authStr):
        return authStr

class SetBucketUuid(object):
    def process_request(self, req, resp):
        if not (req.method == 'PUT' and req.path == '/'):
            uuid = self.getBucketUuid(req)
            req.context['bucketUuid'] = uuid

    def getBucketUuid(self, req):
        bucketName = self.getBucketName(req)
        # get bucket uuid from db
        bk = session.query(Bucket).filter(Bucket.name == bucketName).first()
        return bk.uuid

    def getBucketName(self, req):
        # host = req.get_header('Host')
        # bucketName = host.split('.')[0]
        return req.get_header('BucketName')

app = falcon.API(middleware=[
    AuthZCheck(),
    SetBucketUuid(),
    ])

bucket = Bucket()
obj = Object()

app.add_route('/', bucket)
app.add_route('/{name}', obj)
