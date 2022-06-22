# coding=GB18030
DEBUG = 0
DEFAULT_DIR = "/home/webrtc/video"
DEFAULT_FRAME_WIDTH = 1920
DEFAULT_FRAME_HEIGHT = 1080
DEFAULT_FRAME_RATE = 15
DEFAULT_DISCONNECT = 15
DEFAULT_SSL_CRT = "/etc/pki/tls/certs/cert.crt"
DEFAULT_SSL_KEY = "/etc/pki/tls/private/cert.key"
DEFAULT_LOG_DIR = "./server.log"
DB_PASSWD = 'A6080o--a__TtVFR'
DB_HOST = "localhost"
DB_USER = "root"
DB_PORT = 3306
DB_DATABASE = "user"
DB_URL = "mariadb://{username}:{password}@{host}:{port}/{db}?charset=gbk".format(username=DB_USER, password=DB_PASSWD, host=DB_HOST, port=DB_PORT, db=DB_DATABASE)
