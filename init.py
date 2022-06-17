# coding=GB18030
from collections import UserDict
from hashlib import md5
from http.client import REQUESTED_RANGE_NOT_SATISFIABLE
import ffmpeg
import imp
import os
import random
import sys
import time
import flask
from server_src.read_config import read_from_config_file, config_info
from flask import request, render_template, redirect, session, url_for
from flask_socketio import SocketIO, emit, disconnect,join_room, leave_room, close_room
from server_src.MyConstants import DB_URL, DEBUG
from server_src.DatabaseIO import db, Student
app = flask.Flask(__name__)
app.config['SECRET_KEY'] = "r`9[M-AtuO"
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
socketio = SocketIO(app, async_mode=None)
room_with_teacher = False
teacher_sid = None
callingList = {}

# TODO : 学生的参数设置

if len(sys.argv) > 1:
    read_from_config_file(sys.argv[1])
else:
    read_from_config_file("./webrtc-Tony.conf")
    
    
ssl_certificate = config_info['ssl']['crt']
ssl_certificate_key = config_info['ssl']['key']
# print(ssl_certificate, ssl_certificate_key)



def __output(*message):
    if DEBUG:
        print(message)


def decode_record(filename : str):
    basename = filename[0:filename.rfind('.')]
    stream = ffmpeg.input(basename + '.webm')
    stream = ffmpeg.output(stream, basename + '.mp4')
    ffmpeg.run(stream)
    

@app.route('/', methods=['GET', 'POST'])
def website():
    # print("visited!")
    if request.method == 'GET':
        return render_template("index.html")
    else:
        user_id = request.form['ID']
        user_password = request.form['passwd']
        login_status = -1
        user_userlevel = 0
        #-1: 用户名/密码错误, 0 : 正常, 1 : 需要更改密码 
        with app.app_context():
            satisfy_user = Student.query.filter_by(stu_no=user_id, stu_password=user_password).first()
            satisfy_user : Student
            if not satisfy_user:
                login_status = -1
            elif user_password == md5(user_id):
                login_status = 0 # TODO : 添加更改密码界面
                user_userlevel = satisfy_user.stu_userlevel
            else :
                login_status = 0
                user_userlevel = satisfy_user.stu_userlevel
        
        if login_status == 1:
            return redirect(url_for('change_password', user_id = user_id))
        elif login_status == -1:
            # __output("login fail")
            return render_template("index.html", user_id=user_id)
        else :
            if user_userlevel <= 5 and user_userlevel >= 0:
                return redirect(url_for('student_record', user_id = user_id))
            else :
                return redirect(url_for('teacher_monitor', user_id = user_id))


@app.route('/change_password/<user_id>', methods=['GET', 'POST'])
def change_psasword(user_id):
    if(request.method == 'GET'):
        return render_template("change_password.html", user_id = user_id)
    else :
        __output("change password")
        return "NULL"


@app.route('/student/?<string:user_id>', methods=['GET', 'POST'])
def student_record(user_id):
    return render_template("./student.html")

@app.route('/teacher/?<string:user_id>', methods=['GET', 'POST'])
def teacher_monitor(user_id):
    return "NULL"

@app.route('/teststudent', methods=['GET', 'POST'])
def test_student_record():
    return render_template("./student.html")

@app.route('/testteacher', methods=['GET', 'POST'])
def test_teacher_monitor():
    return render_template("./teacher.html")



@socketio.on('join')
def creatOrJoin(roomid, userLevel):
    global room_with_teacher
    global teacher_sid
    __output(f"receive join event, roomid = {roomid}, sessionId = {request.sid}, userLevel = {userLevel}")
    join_room(room=roomid)
    # student
    if userLevel >= 0 and userLevel <= 5:
        if not room_with_teacher:
            __output(f"room joined, sid = {request.sid}")
        else :
            if len(callingList) == 0 or len(callingList[roomid]) == 0:
                callingList[roomid] = []
            callingList[roomid].append({'From': teacher_sid, 'To': request.sid, 'room': request.sid})
            emit('room_joined', room=teacher_sid)
            
    else :
        # teacher
        room_with_teacher = True
        teacher_sid = request.sid
        try:
        # catch people num in the room ,if  room not be created ,set num = 0
            how_many_people = len(socketio.sockio_mw.engineio_app.manager.rooms['/'][str(roomid)])
        except:
            how_many_people = 0
        if how_many_people > 0:
            callingList[roomid] = []
            for i in socketio.sockio_mw.engineio_app.manager.rooms['/'][str(roomid)]:
                if i != request.sid:
                    callingList[roomid].append({'From': teacher_sid, 'To': i, 'room': i})
            emit('room_joined', room=teacher_sid)



@socketio.on('start_call')
def startCall(roomid):
    __output(f"receive start_call event, roomid = {roomid}, sessionId = {request.sid}")
    
    try:
        result = callingList[roomid].pop(0)
        if len(callingList) == 0:
            __output(f"impossible event: callingList empty")
        if len(callingList) == 0 or len(callingList[roomid]) == 0:
            emit('start_call', {'From': result['From'], 'To': result['To'], 'lastconnect': True}, room=result['room'])
        else:
            emit('start_call', {'From': result['From'], 'To': result['To'], 'lastconnect': False}, room=result['room'])
    except:
        pass

@socketio.on('webrtc_offer')
def webrtcOffer(event):
    __output(f"receive webrtc_offer event, from = {event['From']}, to = {event['To']}, room = {event['To']}")
    emit('webrtc_offer', {'sdp': event['sdp'], 'peerid': event['peerid'], 'From': event['From'], 'To': event['To']},
         room=event['To'])


@socketio.on('webrtc_answer')
def webrtcAnswer(event):
    __output(f"receive webrtc_answer event, from = {event['From']}, to = {event['To']}, room = {event['To']}")
    
    # print('webrtc_answer event to peers in room {}'.format(event['roomid']))
    emit('webrtc_answer', {'sdp': event['sdp'], 'peerid': event['peerid'], 'From': event['From'], 'To': event['To']},
         room=event['To'])


@socketio.on('webrtc_ice_candidate')
def webrtcIceCandidate(event):
    # print(event)
    __output(f"receive webrtc_ice_candidate event\n event = {event}")
    # print('webrtc_ice_candidate event to peers in room {}'.format(event['roomid']))
    emit('webrtc_ice_candidate', event, room=event['To'])


@socketio.on('upload_blob')
def webrtcuploadblob(event):
    roomid = event['roomid']
    clientid = event['clientid']
    __output(f"receive upload_blob event\n, clientid = {clientid}, mode = {event['mode']}")
    
    if roomid not in os.listdir('./record/'):
        os.mkdir('./record/{}'.format(roomid))

    with open('./record/{}/{}.webm'.format(roomid, clientid), 'ab') as f:
        if event['data'] != [0]:
            f.write(event['data'])

    if event['mode'] == 0:
        emit('transfer_complete')


@socketio.on('record_time')
def recordTime(event):
    if event['roomid'] not in os.listdir('./record/'):
        os.mkdir('./record/{}'.format(event['roomid']))

    file = './record/{}/{}.txt'.format(event['roomid'], event['clientid'])
    with open(file, 'a', encoding='utf-8') as file:
        file.writelines(str({'roomid':event['roomid'],'clientid':event['clientid'],'mode':event['mode'],'time':int(time.time())}))
        # file.writelines(str(int(time.time())) + '\n')


@socketio.on('leave')
def leaveRoom(event):
    __output(f"receive leave event, clientid = {event['client']}")
    try:
        how_many_people = len(socketio.sockio_mw.engineio_app.manager.rooms['/'][str(event['room'])])
    except:
        how_many_people = 1
    if 1 < how_many_people <= 6:
        for i in socketio.sockio_mw.engineio_app.manager.rooms['/'][str(event['room'])]:
            if i != event['client']:
                emit('leave_room', {'From': event['client'], 'To': i}, room=i)
        leave_room(event['room'])
    else:
        # emit('close_room', {'F': event['client'], 'T': 'all'}, room=event['client'])
        leave_room(event['room'])
        close_room(event['room'])


# TODO : 记得删掉
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
    # print("INS")
    socketio.run(app, host='0.0.0.0', port=8080, debug=DEBUG, keyfile=ssl_certificate_key, certfile=ssl_certificate )# ssl_context=(ssl_certificate, ssl_certificate_key)
