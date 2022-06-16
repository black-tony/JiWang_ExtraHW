# coding=GB18030
DB_PASSWD = 'A6080o--a__TtVFR'
DB_HOST = "localhost"
DB_USER = "root"
DB_PORT = 3306
DB_DATABASE = "user"
DB_URL = "mariadb://{username}:{password}@{host}:{port}/{db}?charset=gbk".format(username=DB_USER, password=DB_PASSWD, host=DB_HOST, port=DB_PORT, db=DB_DATABASE)
