#!/usr/bin/env python

import sys
import http.server
import logging
import lxml.etree as ET
import io

from ObjectManager import ObjectManager

class RequestHandler(http.server.BaseHTTPRequestHandler):

    def _getListBucketResult(self, files):
        root = ET.Element('ListBucketResult', attrib={'xmlns': 'http://s3.amazonaws.com/doc/2006-03-01/'})
        ET.SubElement(root, 'Name').text = ''
        for name, size in files:
            c = ET.SubElement(root, 'Contents')
            ET.SubElement(c, 'Key').text = name
            ET.SubElement(c, 'Size').text = str(size)
        return ET.tostring(root, encoding='utf-8', xml_declaration=True, pretty_print=True).decode('utf-8')

    def _getFilesInBucket(self):
        uuid = self.headers['x-bucket-uuid']
        if not uuid:
            responseCode = 400
            self.send_response(responseCode)
            self.end_headers()
            return

        om = ObjectManager()
        try:
            files = om.listFiles(uuid)
            rc = self._getListBucketResult(files)
            self.send_response(200)
            self.send_header('x-bucket-uuid', str(uuid))
            self.end_headers()
            self.wfile.write(rc.encode('ascii'))
        except ObjectManager.NamespaceNotFound:
            self.send_response(404)
            self.end_headers()
            self.wfile.write('namespace not found'.encode('ascii'))
        except Exception as ex:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(ex).encode('ascii'))

    def _readObject(self):
        objName = self.path[1:]
        responseCode = 200
        content = b''

        # bucket as ns uuid
        #uuid = self.headers['Host'].split('.')[0]
        uuid = self.headers['x-bucket-uuid']
        # XXX check uuid here
        if not uuid:
            responseCode = 400
            self.send_response(responseCode)
            self.end_headers()
            return

        om = ObjectManager()
        try:
            obj = om.openFile(uuid, objName)
            content = obj.read()
            obj.close()
        except ObjectManager.FileNotFound:
            responseCode = 404
            content = 'File not found'.encode('ascii')
        except ObjectManager.NamespaceNotFound:
            content = 'Namespace not found'.encode('ascii')
        except Exception as ex:
            logging.exception('failed: ' + str(ex))
            responseCode = 500
            content = str(ex).encode('ascii')

        self.send_response(responseCode)
        self.end_headers()
        self.wfile.write(content)


    def do_GET(self):
        objName = self.path[1:]
        if objName == '':
            self._getFilesInBucket()
        else:
            self._readObject()

    #def handle_expect_100(self):
    #    pass

    def _createBucket(self):
        om = ObjectManager()
        try:
            uuid = om.createNamespace()
            self.send_response(201)
            self.send_header('x-bucket-uuid', str(uuid))
            self.end_headers()
        except ObjectManager.NamespaceNotFound:
            self.send_error(404)
            self.end_headers()
            self.wfile.write('namespace not found'.encode('ascii'))
        except Exception as ex:
            self.send_error(500)
            self.end_headers()
            self.wfile.write(str(ex).encode('ascii'))

    def _writeObject(self):
        responseCode = 500

        # bucket as ns uuid
        #uuid = self.headers['Host'].split('.')[0]
        objName = self.path[1:]
        uuid = self.headers['x-bucket-uuid']
        sizeInBytes = int(self.headers['Content-Length'])

        # XXX check uuid here
        if not uuid:
            responseCode = 400
            self.send_response(responseCode)
            self.end_headers()
            return

        om = ObjectManager()
        try:
            try:
                obj = om.openFile(uuid, objName)
                obj.close()
                obj = om.createFile(uuid, objName, sizeInBytes)
                responseCode = 200
            except ObjectManager.FileNotFound:
                obj = om.createFile(uuid, objName, sizeInBytes)
                responseCode = 201

            while sizeInBytes:
                toread = 4 * 1024
                if sizeInBytes < toread:
                    toread = sizeInBytes
                string = self.rfile.read(toread)
                if len(string) == 0:
                    break
                obj.write(string)
                sizeInBytes -= toread
            obj.close()
        except Exception as ex:
            logging.exception('failed: ' + str(ex))
            responseCode = 500

        self.send_response(responseCode)
        self.end_headers()

    def do_PUT(self):
        objName = self.path[1:]
        if objName == '':
            self._createBucket()
        else:
            self._writeObject()



HandlerClass = RequestHandler
ServerClass  = http.server.HTTPServer
 
if sys.argv[1:]:
    port = int(sys.argv[1])
else:
    port = 10080
server_address = ('0.0.0.0', port)
 
httpd = ServerClass(server_address, HandlerClass)
 
sa = httpd.socket.getsockname()
print("Serving HTTP on " + str(sa[0]) + " port: " + str(sa[1]) + "...")
httpd.serve_forever()
