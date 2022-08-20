import os
import sys
import server_src.MyConstants as MyConstants

user = MyConstants.DB_USER
password = MyConstants.DB_PASSWD
database_file = "./user.sql"
if len(sys.argv) > 1:
    database_file = sys.argv[1]
os.system(f"mysql -u{user} -p{password} < {database_file}")
