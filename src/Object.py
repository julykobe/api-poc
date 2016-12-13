import requests

class Object:

    def on_get(self, req, resp, name):

        url = 'https://Jeff-ESXi-IP:Port/%s' % name
        headers = {'bucket-uuid': req.context['bucketUuid']}
        # r = requests.get(url, headers=headers)
        # r.content
        resp.body = (name)

    def on_put(self, req, resp):
        url = 'https://Jeff-ESXi-IP:Port/%s' % name
        headers = {'bucket-uuid': req.context['bucketUuid']}
        # r = requests.put(url, headers=headers)

        resp.status = r.headers['Status']