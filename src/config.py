import ConfigParser

config = ConfigParser.RawConfigParser()
config.read('config.cfg')

def getEsxHosts():
    return config.get('config', 'esx_hosts').split(',')

def getMysqlConnectionString():
    server = config.get('mysql', 'server')
    db = config.get('mysql', 'db')
    user = config.get('mysql', 'user')
    password = config.get('mysql', 'password')
    return "mysql://{}:{}@{}/{}".format(user, password, server, db)
