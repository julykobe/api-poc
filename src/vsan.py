import json
import logging
import falcon

class AuthMiddleware(object):

    def process_request(self, req, resp):
        token = req.get_header('X-Auth-Token')

        if 'curl' in req.user_agent:
            return

        if token is None:
            description = ('Please provice an auth token')
            
            raise falcon.HTTPUnauthorized('Auth token required',
                                          description,
                                          href='https://google.com')

        if not self._token_is_valid(token):
            description = ('Token is not valid.')

            raise falcon.HTTPUnauthorized('Authentication required',
                                          description,
                                          href='https://google.com',
                                          scheme='Token; UUID')

    def _token_is_valid(self, token):
        return token == 'cam'

class RequireJSON(object):

    def process_request(self, req, resp):
        if not req.client_accepts_json:
            raise falcon.HTTPNotAcceptable(
                'This API only supports responses encoded as JSON.')

        if req.method in ('POST', 'PUT') and ('application/json' not in req.content_type):
            raise falcon.HTTPUnsupportedMediaType('This API only supports requests encoded as JSON.')

class JSONTranslator(object):
    def process_request(self, req, resp):
        if req.content_length in (None, 0):
            #warning
            return

        body = req.stream.read()
        if not body:
            raise falcon.HTTPBadRequest('Empty request body.')

        try:
            req.context['doc'] = json.loads(body.decode('utf-8'))
        except (ValueError, UnicodeDecodeError):
            raise falcon.HTTPError(falcon.HTTP_753,
                                   'Malformed JSON.')


    def process_response(self, req, resp, resource):
        if 'result' not in req.context:
            return

        resp.body = json.dumps(req.context['result'])


class VsanClusterResource:
    
    def __init__(self):
        self.logger = logging.getLogger('vsan.' + __name__)

    def on_get(self, req, resp):
        req.context['result'] = 'list api'

        # here should run some vmodl api to complete function

        resp.set_header('X-Powered-By', 'Photon')
        resp.status = falcon.HTTP_200
        resp.body = ('\nlist api\n\n')


    def on_post():
        # vmodl api
        pass

class VsanClusterAddHostResource:

    def __init__(self):
        self.logger = logging.getLogger('vsan.' + __name__)

    def on_get(self, req, resp):
        req.context['result'] = 'add host'

        # here should run some vmodl api to complete function

        resp.set_header('X-Powered-By', 'Photon')
        resp.status = falcon.HTTP_200
        resp.body = ('\nadd host to vsan\n\n')

app = falcon.API(middleware=[
    AuthMiddleware(),
    RequireJSON(),
    JSONTranslator(),
    ])

vsanCluster = VsanClusterResource()
vsanClusterAddHost = VsanClusterAddHostResource()

app.add_route('/vsan/cluster', vsanCluster)
app.add_route('/vsan/cluster/addhost', vsanClusterAddHost)
