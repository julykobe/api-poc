#!/usr/bin/env python

import subprocess
import re
import os
import threading
import logging
import json
import struct

class SingletonClass(object):

    __singleton_lock = threading.Lock()
    __singleton_instance = None

    def __init__(self):
        assert(self.__singleton_instance is None)
        if hasattr(self, '_init'):
            self._init()

    @classmethod
    def instance(cls):
        if not cls.__singleton_instance:
            with cls.__singleton_lock:
                if not cls.__singleton_instance:
                    cls.__singleton_instance = cls()
        return cls.__singleton_instance


class Objtool(SingletonClass):

    objtoolBin = '/usr/lib/vmware/osfs/bin/objtool'

    def _runCmd(self, cmd, checkResult=True):
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                             universal_newlines=True)
        out, err = p.communicate()
        if checkResult and p.returncode:
            raise Exception('objtool cmd: %s failed with return code: %d\nstderr:%s'
                            % (' '.join(cmd), p.returncode, err))

        return p.returncode, out, err

    def create(self, sizeInBytes, type_):
        cmd = [self.objtoolBin,
               'create',
               '-s', str(sizeInBytes),
               '-t', type_]
        _, out, _ = self._runCmd(cmd)

        result = re.search(r'^UUID:([-0-9a-f]{36})$', out, re.MULTILINE)
        return result.group(1)

    def delete(self, uuid):
        cmd = [self.objtoolBin, 'delete', '-u', uuid]
        self._runCmd(cmd)

    def open(self, uuid):
        cmd = [self.objtoolBin, 'getAttr', '-u', uuid]
        rc, _, _ = self._runCmd(cmd, checkResult=False)
        if rc != 0:
            raise FileNotFoundError()
        cmd = [self.objtoolBin, 'open', '-u', uuid]
        self._runCmd(cmd)

    def resize(self, uuid, sizeInBytes):
        cmd = [self.objtoolBin, 'resize', '-u', uuid, '-s', str(sizeInBytes)]
        self._runCmd(cmd)


class VsanObject(object):

    vsanDevFsPath = '/vmfs/devices/vsan/'
    blockSize = 4 * 1024

    TYPE_VDISK      = '0'
    TYPE_NAMESPACE  = '2'

    def __init__(self, uuid):
        self._fd = None
        self._uuid = uuid

        self.reopen()

    @staticmethod
    def create(sizeInBytes, type_):
        mod = sizeInBytes % VsanObject.blockSize
        if mod is not 0:
            sizeInBytes += VsanObject.blockSize - mod

        return Objtool.instance().create(sizeInBytes, type_)

    @staticmethod
    def delete(uuid):
        return Objtool.instance().delete(uuid)

    @staticmethod
    def resize(uuid, sizeInBytes):
        mod = sizeInBytes % VsanObject.blockSize
        if mod is not 0:
            sizeInBytes += VsanObject.blockSize - mod

        Objtool.instance().resize(uuid, sizeInBytes)

    def reopen(self):
        assert(self._fd is None)

        fdpath = self.vsanDevFsPath + self._uuid
        if not os.path.isfile(fdpath):
            Objtool.instance().open(self._uuid)

        flags = os.O_RDWR | os.O_SYNC | os.O_DIRECT
        self._fd = os.open(fdpath, flags)

    def close(self):
        if self._fd:
            os.fsync(self._fd)
            os.close(self._fd)
            self._fd = None

    def __del__(self):
        self.close()

    def lseek(self, pos, how):
        return os.lseek(self._fd, pos, how)

    def read(self, length):
        left = os.lseek(self._fd, 0, os.SEEK_CUR) % self.blockSize
        right = (left + length) % self.blockSize
        if right is not 0:
            right = self.blockSize - right
        os.lseek(self._fd, -left, os.SEEK_CUR)
        ret = os.read(self._fd,
                      left + length + right)[left:left+length]
        os.lseek(self._fd, -right, os.SEEK_CUR)
        return ret

    def write(self, content):
        left = os.lseek(self._fd, 0, os.SEEK_CUR) % self.blockSize
        if left:
            os.lseek(self._fd, -left, os.SEEK_CUR)
            block = os.read(self._fd, self.blockSize)
            os.lseek(self._fd, -self.blockSize, os.SEEK_CUR)
            content = block[:left] + content

        right = len(content) % self.blockSize
        if right == 0:
            os.write(self._fd, content)
        else:
            os.write(self._fd, content[:-right])
            block = os.read(self._fd, self.blockSize)
            os.lseek(self._fd, -self.blockSize, os.SEEK_CUR)
            os.write(self._fd, content[-right:] + block[right:])
            os.lseek(self._fd, right-self.blockSize, os.SEEK_CUR)
        cur = os.lseek(self._fd, 0, os.SEEK_CUR)


class Object(object):

    def __init__(self, uuid, offset=0, length=None):
        self._offset = offset
        self._length = length
        self._vsanObj = VsanObject(uuid)
        if not self._length:
            self._length = self._vsanObj.lseek(0, os.SEEK_END)
        self._vsanObj.lseek(offset, os.SEEK_SET)

    def read(self, length=None):
        cur = self._vsanObj.lseek(0, os.SEEK_CUR)
        assert(cur >= self._offset and cur < self._offset + self._length)
        left = self._offset + self._length - cur
        if length is None:
            length = left
        elif length > left:
            raise ValueError('try to read too much')
        return self._vsanObj.read(length)

    def write(self, content):
        cur = self._vsanObj.lseek(0, os.SEEK_CUR)
        assert(cur >= self._offset and cur < self._offset + self._length)
        left = self._offset + self._length - cur
        if len(content) > left:
            raise ValueError('try to write too much')
        self._vsanObj.write(content)

    def close(self):
        self._vsanObj.close()


class NamespaceManager(object):

    def __init__(self, uuid):
        self._nsObj = VsanObject(uuid)
        self._loadDb()

    def _saveDb(self):
        buf = json.dumps(self.db).encode('ascii')
        dbSize = struct.pack('=L', len(buf))
        self._nsObj.lseek(0, os.SEEK_SET)
        self._nsObj.write(dbSize + buf)

    def _loadDb(self):
        self._nsObj.lseek(0, os.SEEK_SET)
        buf = self._nsObj.read(struct.calcsize('=L'))
        dbSize = struct.unpack('=L', buf)[0]
        buf = self._nsObj.read(dbSize)
        if not buf:
            self.db = {'container': [], 'files': {}}
        else:
            self.db = json.loads(buf.decode('ascii'))

    def addFile(self, name, offset, size):
        if not self.db['container']:
            uuid = VsanObject.create(1 * 1024 ** 3, VsanObject.TYPE_VDISK)
            self.db['container'].append(uuid)
        cIndex = 0

        files = self.db['files']
        if name in files:
            raise KeyError(name)
        files[name] = (cIndex, offset, size)
        self._saveDb()
        return self.db['container'][cIndex]

    def setFile(self, name, offset, size):
        cIndex = 0

        files = self.db['files']
        files[name] = (cIndex, offset, size)
        self._saveDb()
        return self.db['container'][cIndex]

    def getFile(self, name):
        files = self.db['files']
        cIndex, offset, size = files[name]
        return self.db['container'][cIndex], offset, size

    def getFiles(self):
        ret = {}
        for k, v in self.db['files'].items():
            ret[k] = (self.db['container'][v[0]], v[1], v[2])
        return ret

    @staticmethod
    def create():
        uuid = VsanObject.create(256 * 1024 ** 2, VsanObject.TYPE_NAMESPACE)
        nsObj = VsanObject(uuid)
        nsObj.write(struct.pack('=L', 0))
        nsObj.close()
        return uuid


class ObjectManager(object):

    class NamespaceNotFound(Exception):
        pass

    class FileNotFound(Exception):
        pass

    def __init__(self):
        self._dsName = 'vsanDatastore'

    def createNamespace(self):
        return NamespaceManager.create()

    def listFiles(self, ns):
        try:
            nsMgr = NamespaceManager(ns)
        except FileNotFoundError:
            raise self.NamespaceNotFound()

        files = nsMgr.getFiles()
        return zip(files.keys(), map(lambda v: v[2], files.values()))

    def createFile(self, ns, name, sizeInBytes):
        try:
            nsMgr = NamespaceManager(ns)
        except FileNotFoundError:
            raise self.NamespaceNotFound()

        files = nsMgr.getFiles()
        if name not in files or files[name][2] < sizeInBytes:
            # sort by offset
            offsets = sorted(files.values(), key=lambda f: f[1])
            lastPos = 0
            for _, offset, length in offsets:
                hole = offset - lastPos
                if sizeInBytes <= hole:
                    break
                else:
                    lastPos = offset + length
        else:
            lastPos = files[name][1]

        try:
            uuid = nsMgr.addFile(name, lastPos, sizeInBytes)
        except KeyError:
            uuid = nsMgr.setFile(name, lastPos, sizeInBytes)

        return Object(uuid, lastPos, sizeInBytes)

    def openFile(self, ns, name):
        try:
            nsMgr = NamespaceManager(ns)
        except FileNotFoundError:
            raise self.NamespaceNotFound()

        try:
            uuid, offset, length = nsMgr.getFile(name)
            return Object(uuid, offset, length)
        except KeyError:
            raise self.FileNotFound()

