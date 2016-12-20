def getBucketUuid(req):
    bucketName = getBucketName(req)
    # get bucket uuid from db
    bk = session.query(Bucket).filter(Bucket.name == bucketName).first()
    return bk.uuid

def getBucketName(req):
    host = req.get_header('Host')
    bucketName = host.split('.')[0]
    return bucketName