# coding=GB18030
import imp
import random
import sys
import flask
from server_src.read_config import read_from_config_file, config_info
from flask import request, render_template, redirect, session, url_for
from flask_socketio import SocketIO, emit, disconnect
from server_src.MyConstants import DB_URL
from server_src.DatabaseIO import db, Student
app = flask.Flask(__name__)
app.config['SECRET_KEY'] = "r`9[M-AtuO"
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


if len(sys.argv) > 1:
    read_from_config_file(sys.argv[1])
else:
    read_from_config_file("./webrtc-Tony.conf")
    
    
ssl_certificate = config_info['ssl']['crt']
ssl_certificate_key = config_info['ssl']['key']
# print(ssl_certificate, ssl_certificate_key)
DEBUG = 1


def __output(*message):
    if DEBUG:
        print(message)


@app.route('/', methods=['GET', 'POST'])
def website():
    if request.method == 'GET':
        return render_template("index.html")
    else:
        user_id = request.form['ID']
        user_password = request.form['passwd']
        if user_id == "123456" and user_password == 'root':
            return redirect('/success')
        else:
            __output("login fail")
            return render_template("index.html", user_id=user_id)


@app.route('/success', methods=['GET'])
def tmp_page():
    return render_template("YangTest/index.html")


# TODO : 这个是用于测试数据库的, 最后需要删掉
@app.route('/testdb', methods=['GET'])
def test_db():
    with app.app_context():
        users = Student.query.all()
        # print(users)
        # print("---------")
        users = Student.query.filter_by(stu_no="1234567").all()
        # print(users)
        # print("---------")
        users = Student.query.filter_by(stu_no="1234567", stu_grade="0000").all()
        # print("None" if not users else users)
        # print("---------")
    
    return "Hello!"

if __name__ == "__main__":
    socketio = SocketIO(app, async_mode=None)
    socketio.run(app, host='0.0.0.0', port=8080, debug=DEBUG, ssl_context=(ssl_certificate, ssl_certificate_key))
