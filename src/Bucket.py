import falcon
import logging
import requests
from sqlalchemy import Column
from sqlalchemy.types import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import getEsxHosts, getMysqlConnectionString

engine = create_engine(getMysqlConnectionString())
DBSession = sessionmaker(bind=engine)
session = DBSession()

BaseModel = declarative_base()

# self.logger = logging.getLogger()

def validateBucketName(req, resp, resource, params):
    bucketName = getBucketName(req)

    if session.query(Bucket).filter(Bucket.name == bucketName).count() != 0:
            raise falcon.HTTPInvalidParam("Bucket %s already exists." % bucketName,
                                          "BucketName")

def getBucketUuid(req):
    bucketName = getBucketName(req)
    # get bucket uuid from db
    bk = session.query(Bucket).filter(Bucket.name == bucketName).first()
    if bk is None:
        raise falcon.HTTPBadRequest("Bucket %s doesn't exist" % bucketName,)
    return bk.uuid

def getBucketName(req):
    host = req.get_header('Host')
    bucketName = host.split('.')[0]
    return bucketName


class Bucket(BaseModel):
    __tablename__ = 'bucket'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    uuid = Column(String)

    def __repr__(self):
        return "<Bucket bucket name: %s>" % self.name

    def on_get(self, req, resp):
        esx_host = getEsxHosts()[0]

        url = 'http://%s' % esx_host
        headers = {'x-bucket-uuid': req.context['bucketUuid']}
        r = requests.get(url, headers=headers)

        resp.set_header('x-bucket-uuid', req.context['bucketUuid'])
        resp.status_code = r.status_code

    @falcon.before(validateBucketName)
    def on_put(self, req, resp):
        esx_host = getEsxHosts()[0]

        # header "BucketName: test"
        url = 'http://%s' % esx_host
        r = requests.put(url)
        uuid = r.headers['x-bucket-uuid']
        
        bucket = Bucket(name=getBucketName(req), uuid=uuid)
        session.add(bucket)
        session.commit()

        resp.set_header('CreateBucket', bucket.uuid)
        resp.status_code = r.status_code




# def init_db():
#     BaseModel.metadata.create_all(engine)

# def drop_db():
#     BaseModel.metadata.drop_all(engine)
