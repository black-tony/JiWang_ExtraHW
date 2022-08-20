# coding=GB18030
# import configparser
from configparser import ConfigParser
from .MyConstants import *


config_info = {}
config_info['root_dir'] = DEFAULT_DIR
config_info['frame'] = {}
config_info['frame']['width'] = DEFAULT_FRAME_WIDTH
config_info['frame']['height'] = DEFAULT_FRAME_HEIGHT
config_info['frame']['rate'] = DEFAULT_FRAME_RATE
config_info['disconnect'] = DEFAULT_DISCONNECT
config_info['ssl'] = {}
config_info['ssl']['crt'] = DEFAULT_SSL_CRT
config_info['ssl']['key'] = DEFAULT_SSL_KEY
config_info['log'] = DEFAULT_LOG_DIR
config_info['database'] = {}
config_info['database']['password'] = DB_PASSWD
config_info['database']['host'] = DB_HOST
config_info['database']['port'] = DB_PORT
config_info['database']['user'] = DB_USER
config_info['turnserver'] = {}
config_info['turnserver']['ip'] = TURNSERVER_IP
config_info['turnserver']['port'] = TURNSERVER_PORT


__config = ConfigParser(comment_prefixes=(';', '#'), inline_comment_prefixes=(';', '#'), delimiters=('='), empty_lines_in_values=False)

def read_from_config_file(filename, encoding='GB18030'):
    fin = open(filename, 'r', encoding=encoding)
    buf = fin.read()
    buf = buf.replace("\n", "\n\n")
    
    __config.read_string(buf)
    # print(__config.sections())
    # getchar()
    # print(__config.options('frame'))
    config_info['root_dir'] = __config.get(section='root_dir', option='dir', fallback=DEFAULT_DIR)
    config_info['frame']['width'] = __config.getint(section='frame', option='width', fallback=DEFAULT_FRAME_WIDTH)
    config_info['frame']['height'] = __config.getint(section='frame', option='high', fallback=DEFAULT_FRAME_HEIGHT)
    config_info['frame']['rate'] = __config.getint(section='frame', option='rate', fallback=DEFAULT_FRAME_RATE)
    config_info['disconnect'] = __config.getint(section='断联时间', option='disconnect', fallback=DEFAULT_DISCONNECT)
    config_info['ssl']['crt'] = __config.get(section='ssl', option='crt', fallback=DEFAULT_SSL_CRT)
    config_info['ssl']['key'] = __config.get(section='ssl', option='key', fallback=DEFAULT_SSL_KEY)
    config_info['log'] = __config.get(section='log', option='log', fallback=DEFAULT_LOG_DIR)
    config_info['database']['password'] = __config.get(section='database', option='password', fallback=DB_PASSWD)
    config_info['database']['host'] = __config.get(section='database', option='host', fallback=DB_HOST)
    config_info['database']['port'] = __config.get(section='database', option='port', fallback=DB_PORT)
    config_info['database']['user'] = __config.get(section='database', option='user', fallback=DB_USER)
    config_info['turnserver']['ip'] = __config.get(section='turnserver', option='ip', fallback=TURNSERVER_IP)
    config_info['turnserver']['port'] = __config.get(section='turnserver', option='port', fallback=TURNSERVER_PORT)
    
if __name__ == '__main__':
    read_from_config_file('../webrtc-Tony.conf')
    
    print(config_info)