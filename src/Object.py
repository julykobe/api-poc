import requests
from config import getEsxHosts

class Object:

    def on_get(self, req, resp, name):
        esx_host = getEsxHosts()[0]

        url = 'http://%s/%s' % (esx_host, name)
        headers = {'x-bucket-uuid': req.context['bucketUuid']}
        r = requests.get(url, headers=headers)

        resp.data = r.content

    def on_put(self, req, resp, name):
        esx_host = getEsxHosts()[0]

        url = 'http://%s/%s' % (esx_host, name)
        headers = {'x-bucket-uuid': req.context['bucketUuid']}
        r = requests.put(url, headers=headers, data=req.stream.read())

        resp.status_code = r.status_code
