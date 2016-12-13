import json
import logging
import falcon

from Bucket import Bucket
from Object import Object

class AuthZCheck(object):

    def process_request(self, req, resp):
        authStr = req.get_header('Authorization')
        authId = self.convertAuthStrToAuthId(authStr)
        req.context['Authorization'] = authId 

    def convertAuthStrToAuthId(self, authStr):
        return authStr

app = falcon.API(middleware=[
    AuthZCheck(),
    ])

bucket = Bucket()


app.add_route('/', bucket)
