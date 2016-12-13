class Object:

    def __init__(self):
        self.logger = logging.getLogger()

    def on_get(self, req, resp):
        host = req.get_header('Host')
        bucketName = host.split('.')[0]
        print bucketName
        resp.body = (bucketName)

    def on_put(self, req, resp):
        pass