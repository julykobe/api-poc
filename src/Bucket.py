import logging
import requests
from sqlalchemy import Column
from sqlalchemy.types import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('mysql://root:password@localhost/s5')
DBSession = sessionmaker(bind=engine)
session = DBSession()

BaseModel = declarative_base()

# self.logger = logging.getLogger()

class Bucket(BaseModel):
    __tablename__ = 'bucket'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    uuid = Column(String)

    def __repr__(self):
        return "<Bucket bucket name: %s>" % self.name

    def on_get(self, req, resp):

        # call Jeff to get objects under bucket
        url = 'https://Jeff-ESXi-IP:Port'
        headers = {'bucket-uuid': req.context['bucketUuid']}
        # r = requests.get(url, headers=headers)

        resp.set_header('FoundBucket', req.context['bucketUuid'])
        # resp.body = r.content

    def on_put(self, req, resp):
        # call Jeff to get a bucket uuid
        url = 'https://Jeff-ESXi-IP:Port'
        r = requests.get(url)
        uuid = r.content# wrong

        bucketName = getBucketName(req)
        bucket = Bucket(name=bucketName, uuid = uuid)
        session.add(bucket)
        session.commit()

        resp.set_header('CreateBucket', bucket.uuid)
        resp.body = ('%s\n') % bucket.name

def getBucketUuid(req):
    bucketName = getBucketName(req)
    # get bucket uuid from db
    bk = session.query(Bucket).filter(Bucket.name == bucketName).first()
    return bk.uuid

def getBucketName(req):
    # host = req.get_header('Host')
    # bucketName = host.split('.')[0]
    return req.get_header('BucketName')


# def init_db():
#     BaseModel.metadata.create_all(engine)

# def drop_db():
#     BaseModel.metadata.drop_all(engine)


