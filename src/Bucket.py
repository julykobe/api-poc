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

    def __repr__(self):
        return "<Bucket bucket name: %s>" % self.name

    def on_get(self, req, resp):
        # host = req.get_header('Host')
        # bucketName = host.split('.')[0]
        bucketName = getBucketName(req)

        # get bucket from db
        bk = session.query(Bucket).filter(Bucket.name == bucketName).first()

        resp.set_header('FoundBucket', bk.id)
        resp.body = ('\n%s\n\n') % bk.name

    def on_put(self, req, resp):
        # create bucket from db and backend
        # bucketName = host.split('.')[0]

        bucketName = getBucketName(req)

        bucket = Bucket(name=bucketName)
        session.add(bucket)
        session.commit()

        resp.set_header('FoundBucket', bucket.id)
        resp.body = ('\n%s\nThen call backend') % bucket.name
        # callBackend()
        print('call backend')


def getBucketName(req):
    return req.get_header('BucketName')

def init_db():
    BaseModel.metadata.create_all(engine)

def drop_db():
    BaseModel.metadata.drop_all(engine)



        