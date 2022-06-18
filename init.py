# coding=GB18030
from crypt import methods
from datetime import datetime
from distutils.log import debug
from email.mime import audio
from hashlib import md5
import shutil
import threading
import ffmpeg
import random
import os
import sys
import time
import flask
from server_src.read_config import read_from_config_file, config_info
from flask import make_response, request, render_template, redirect, session, url_for
from flask_socketio import SocketIO, emit, disconnect,join_room, leave_room, close_room
from server_src.MyConstants import DB_URL, DEBUG
from server_src.DatabaseIO import db, Student
app = flask.Flask(__name__)
app.config['SECRET_KEY'] = "r`9[M-AtuO"
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
socketio = SocketIO(app)# , ping_interval=3, ping_timeout=3
room_with_teacher = False
teacher_sid = None
callingList = {}
sid_to_clientid = {}
userid_to_sid = {}
userid_to_logtime = {}
teacher_killed = []
ROOM_NAME = '1'

# TODO : 学生的参数设置

if len(sys.argv) > 1:
    read_from_config_file(sys.argv[1])
else:
    read_from_config_file("./webrtc-Tony.conf")
    
    
def RemoveDir(filepath):
    if not os.path.exists(filepath):
        os.mkdir(filepath)
    else:
        shutil.rmtree(filepath)
        os.mkdir(filepath)
# print(ssl_certificate, ssl_certificate_key)

RemoveDir("./record/") # TODO : 更改
# 功能性函数

def debug_output(*message):
    if DEBUG:
        print(message)

def check_password_strength(password):
    return True # TODO 限制
    if len(password) < 8 or len(password) > 16:
        return False

    digit = False
    other = False
    alpha = False
    for i in password:
        if i.isdigit():
            digit = True
        elif i.isalpha():
            alpha = True
        else:
            other = True
    
    if digit and other and alpha:
        return True
    else:
        return False

def decode_record(fin : str, fout : str):
    probe = ffmpeg.probe(fin)
    have_audio = False
    have_video = False
    for i in probe['streams']:
        if(i['codec_type'] == 'audio'):
            have_audio = True
        elif(i['codec_type'] == 'video'):
            have_video = True
    stream = ffmpeg.input(fin)
    streamaudio = stream.audio
    streamvideo = stream.video
    # stream = ffmpeg.filter(stream, "scale", config_info['frame']['width'], config_info['frame']['height'])
    streamvideo = ffmpeg.filter(streamvideo, "fps", config_info['frame']['rate'])
    # stream = ffmpeg.filter(stream, 'loglevel', 'quiet')
    if have_audio and have_video:
        stream = ffmpeg.output(streamaudio, streamvideo, fout,  **{'loglevel':'quiet'})
    elif have_audio:
        stream = ffmpeg.output(streamaudio, fout,  **{'loglevel':'quiet'})
    else:
        stream = ffmpeg.output(streamvideo, fout,  **{'loglevel':'quiet'})
    stream = ffmpeg.overwrite_output(stream)
    pip = ffmpeg.run_async(stream)
    pip.communicate()

class DecodeThread (threading.Thread):
    def __init__(self, fin, fout):
        threading.Thread.__init__(self)
        self.fin = fin
        self.fout = fout
    def run(self):
        decode_record(self.fin, self.fout)
        # os.remove(self.fin)
        debug_output(f"{self.fin} decode finish!")
        # print_time(self.name, self.delay, 5)
        # print ("退出线程：" + self.name)


    
def get_new_sid(clientsid : str):
    new_sid = None
    new_sid : str
    for i,j in sid_to_clientid.items():
        if j == clientsid:
            new_sid = i
            break
    if(new_sid == None):
        debug_output("Target not find!")
        return clientsid
    else:
        return new_sid


# 部署的域名

@app.route('/', methods=['GET', 'POST'])
def website():
    # print("visited!")
    if request.method == 'GET':
        return render_template("index.html")
    else:
        user_id = request.form['ID']
        user_password = request.form['passwd']
        login_status = -1
        user_userlevel = '0'
        #-1: 用户名/密码错误, 0 : 正常, 1 : 需要更改密码 
        with app.app_context():
            satisfy_user = Student.query.filter_by(stu_no=user_id, stu_password=user_password).first()#
            satisfy_user : Student
            # print(f"passwd = {satisfy_user.stu_password}, hashcode = {calcans}")
            if not satisfy_user:
                login_status = -1
            elif user_password == md5(satisfy_user.stu_no.encode("GB18030")).hexdigest():
                login_status = 1 
                user_userlevel = satisfy_user.stu_userlevel
            else :
                login_status = 0
                user_userlevel = satisfy_user.stu_userlevel
        
        if login_status == 1:
            resp = make_response(redirect(url_for('change_password', user_id = user_id)))
            resp.set_cookie('userid', user_id)
            return resp
        elif login_status == -1:
            # __output("login fail")
            return render_template("index.html", user_id=user_id)
        else :
            if user_userlevel == '0':
                resp = make_response(redirect(url_for('student_record', user_id = user_id)))
                resp.set_cookie('userid', user_id)
                resp.set_cookie('userlevel', user_userlevel)
                return resp
            else :
                resp = make_response(redirect(url_for('teacher_monitor', user_id = user_id)))
                resp.set_cookie('userid', user_id)
                resp.set_cookie('userlevel', user_userlevel)
                return resp


@app.route('/change_password/<user_id>', methods=['GET'])
def change_password(user_id):
    if(request.method == 'GET'):
        if 'userid' not in request.cookies:
            return redirect("website")
        return render_template("change_password.html", user_id = user_id, test_result = 1)
        

@app.route("/change_password", methods=['POST'])
def check_passwd():
    passwd1 = request.form['passwd1']
    passwd2 = request.form['passwd2']
    userid = request.cookies['userid']
    # debug_output("accept!")
    if(passwd1 == passwd2) :
        with app.app_context():
            debug_output(userid)
            satisfy_user = Student.query.filter_by(stu_no=userid).first()
            satisfy_user : Student
            satisfy_user.stu_password = passwd1
            db.session.commit()
        return redirect(url_for('website'))
    else :
        return render_template("change_password.html", user_id = userid, test_result = 0)



@app.route('/student/?<string:user_id>', methods=['GET', 'POST'])
def student_record(user_id):
    if 'userid' not in request.cookies or 'username' not in request.cookies:
        return redirect('website') 
    return render_template("./student.html")

@app.route('/teacher/?<string:user_id>', methods=['GET', 'POST'])
def teacher_monitor(user_id):
    if 'userid' not in request.cookies or 'username' not in request.cookies:
        return redirect('website') 
    return "NULL"


@app.route("/timeout", methods=['GET', 'POST'])
def tle():
    resp = redirect(url_for('website'))
    resp.delete_cookie('userid')
    resp.delete_cookie('username')
    resp.delete_cookie('userlevel')
    return resp    



# TODO : 测试学生和老师使用
@app.route('/teststudent', methods=['GET', 'POST'])
def test_student_record():
    global userid_to_sid
    user_id = random.randint(1000000, 9999999)
    while str(user_id) in userid_to_sid:
        user_id = random.randint(1000000, 9999999)
    resp = make_response(render_template("./student.html", userid=user_id, username="NULL"))
    resp.set_cookie('userid', str(user_id))
    resp.set_cookie('userlevel', str(0))
    return resp

@app.route('/testteacher', methods=['GET', 'POST'])
def test_teacher_monitor():
    global userid_to_sid
    user_id = random.randint(1000000, 9999999)
    while str(user_id) in userid_to_sid:
        user_id = random.randint(1000000, 9999999)
    # userid_to_sid[str(user_id)] = request.sid
    resp = make_response(render_template("./teacher.html", userid=user_id, username="NULL"))
    resp.set_cookie('userid', str(user_id))
    resp.set_cookie('userlevel', str(9))
    return resp



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
        # print(users)
        # print("---------")
        users = Student.query.filter_by(stu_no="1234567").first()
        print(users.stu_grade)
        # print("---------")
        users = Student.query.filter_by(stu_no="1234567", stu_grade="0000").all()
        print("None" if not users else users)
        # print("---------")
    
    return "Hello!"



# 监听的事件

@socketio.on('join')
def creatOrJoin(roomid, userLevel, userid, username):
    # 这里的sid一定是第一个sid
    
    global room_with_teacher
    global teacher_sid
    global userid_to_sid
    global sid_to_clientid
    global userid_to_logtime
    
    debug_output(f"receive join event, roomid = {roomid}, sessionId = {request.sid}, userLevel = {userLevel}")
    join_room(room=roomid)
    
    
    if userid in userid_to_sid:
        debug_output("impossible event! join with a previous sid!")
        return
    userid_to_sid[userid] = request.sid
    sid_to_clientid[request.sid] = request.sid
    nowtime = datetime.now()
    
    timeformated ="-{:0>4}-{:0>2}-{:0>2}-{:0>2}-{:0>2}-{:0>2}".format(
        nowtime.year, nowtime.month, nowtime.day, nowtime.hour, nowtime.minute, nowtime.second)
    userid_to_logtime[userid] = timeformated
    
    # student
    if userLevel >= 0 and userLevel <= 5:
        if not room_with_teacher:
            debug_output(f"room joined, sid = {request.sid}")
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
                    callingList[roomid].append({'From': teacher_sid, 'To': sid_to_clientid[i], 'room': sid_to_clientid[i]})
            emit('room_joined', room=teacher_sid)



@socketio.on('start_call')
def startCall(roomid):
    userid = request.cookies['userid']
    debug_output(f"receive start_call event, roomid = {roomid}, sessionId = {userid_to_sid[userid]}")
    
    try:
        result = callingList[roomid].pop(0)
        if len(callingList) == 0:
            debug_output(f"impossible event: callingList empty")
        if len(callingList) == 0 or len(callingList[roomid]) == 0:
            emit('start_call', {'From': result['From'], 'To': result['To'], 'lastconnect': True}, room=result['room'])
        else:
            emit('start_call', {'From': result['From'], 'To': result['To'], 'lastconnect': False}, room=result['room'])
    except:
        pass

@socketio.on('webrtc_offer')
def webrtcOffer(event):
    debug_output(f"receive webrtc_offer event, from = {event['From']}, to = {event['To']}, room = {get_new_sid(event['To'])}")
    emit('webrtc_offer', {'sdp': event['sdp'], 'peerid': event['peerid'], 'From': event['From'], 'To': event['To'], 'userid' : event['userid']},
         room=get_new_sid(event['To']))


@socketio.on('webrtc_answer')
def webrtcAnswer(event):
    debug_output(f"receive webrtc_answer event, from = {event['From']}, to = {event['To']}, room = {get_new_sid(event['To'])}")
    
    # print('webrtc_answer event to peers in room {}'.format(event['roomid']))
    emit('webrtc_answer', {'sdp': event['sdp'], 'peerid': event['peerid'], 'From': event['From'], 'To': event['To'], 'userid' : event['userid']},
         room=get_new_sid(event['To']))


@socketio.on('webrtc_ice_candidate')
def webrtcIceCandidate(event):
    # print(event)
    debug_output(f"receive webrtc_ice_candidate event", "\n", f" peerid = {event['peerid']},room = {get_new_sid(event['To'])}")
    # print('webrtc_ice_candidate event to peers in room {}'.format(event['roomid']))
    
    
    emit('webrtc_ice_candidate', event, room=get_new_sid(event['To']))


@socketio.on('upload_blob')
def webrtcuploadblob(event):
    # global sid_to_userid
    # roomid = event['roomid']
    # clientid = event['clientid']
    debug_output(f"receive upload_blob event, userid = {event['userid']}, mode = {event['mode']}")
    
    # if roomid not in os.listdir('./record/'):
    #     os.mkdir('./record/{}'.format(roomid))
    recordType =  "video" if event['mode'] < 2 else "screen"
    # try:
    #     userid = sid_to_userid[clientid]
    # except:
    #     __output("How to get here?")
        
    # TODO 更改路径
    time_str = None
    try:
        time_str = userid_to_logtime[event['userid']]
    except:
        return
        
    with open('./record/u{}-{}-{}{}.webm'.format(event['userid'], event['username'], recordType, time_str), 'ab') as f:
        if event['data'] != [0]:
            f.write(event['data'])

    # if event['mode'] == 0 or event['mode'] == 2:
    #     emit('transfer_complete')
    #     users = None
    #     users : Student
    #     with app.app_context():
    #         users = Student.query.filter_by(stu_no=event['userid']).first()
    #     #TODO : 正式版之前要注释
    #     users = Student(0, event['userid'], "NULL", "123","0","0","0","0","0","0",'0','0')
    #     if users == None:
    #         return
    #     nowtime = datetime.now()
    
    #     timeformated ="-{:0>4}-{:0>2}-{:0>2}-{:0>2}-{:0>2}-{:0>2}".format(
    #         nowtime.year, nowtime.month, nowtime.day, nowtime.hour, nowtime.minute, nowtime.second)
        
    #     videobasename = "./record/" + "u{}-{}-video".format(
    #         users.stu_no, users.stu_name)
    #     screenbasename = "./record/" + "u{}-{}-screen".format(
    #         users.stu_no, users.stu_name)
    #     videosrcname = videobasename+".webm"
    #     videotargetname = videobasename + timeformated + ".mp4"
    #     screensrcname = screenbasename+".webm"
    #     screentargetname = screenbasename + timeformated + ".mp4"
    #     if os.path.isfile(videosrcname) and event['mode'] == 0:
    #         newthread1 = DecodeThread(videosrcname, videotargetname)
    #         newthread1.start()
    #     if os.path.isfile(screensrcname) and event['mode'] == 2:
    #         newthread2 = DecodeThread(screensrcname, screentargetname)
    #         newthread2.start()


@socketio.on('record_time')
def recordTime(event):
    # global sid_to_userid
    # if event['roomid'] not in os.listdir('./record/'):
    #     os.mkdir('./record/{}'.format(event['roomid']))
    # try:
    #     userid = sid_to_userid[event['clientid']]
    # except:
    #     __output("How to get here?")
    file = './{}.txt'.format(event['userid'])
    with open(file, 'a', encoding='utf-8') as file:
        file.writelines(str({'roomid':event['roomid'],'userid':event['userid'],'mode':event['mode'],'time':int(time.time())}))
        # file.writelines(str(int(time.time())) + '\n')


@socketio.on('leave')
def leaveRoom(event):
    # now_sid = request.sid
    userid = event['userid']
    clientid = event['client']
    now_sid = userid_to_sid[userid]
    
    
    # assert(now_sid == clientid)
    # assert(now_sid == userid_to_sid[userid])
    # assert(userid == event['userid'])
    # assert(event['client'] == clientid)
    
    try:
        del sid_to_clientid[now_sid]
        del userid_to_sid[userid]
        del userid_to_logtime[userid]
    except:
        pass
    
    debug_output(f"receive leave event, clientid = {clientid}, userid = {userid}")
    try :
        if now_sid not in socketio.sockio_mw.engineio_app.manager.rooms['/'][str(event['room'])]:
            debug_output("notin!")
            # return 
    except KeyError:
        debug_output("keyError")
        return
    
    # if 1 < how_many_people <= 6:
    if clientid != teacher_sid:
        emit('leave_room', {'From': clientid, 'To': teacher_sid}, room=get_new_sid(teacher_sid))
        # for i in socketio.sockio_mw.engineio_app.manager.rooms['/'][str(event['room'])]:
            # if i != event['client']:
                
        # leave_room(event['room'])
    # else:
        # emit('close_room', {'F': event['client'], 'T': 'all'}, room=event['client'])
    leave_room(event['room'])
        # close_room(event['room'])
    # 开始视频转码
    try:
        how_many_people = len(socketio.sockio_mw.engineio_app.manager.rooms['/'][str(event['room'])])
    except:
        how_many_people = 0
    if how_many_people == 0:
        print("----------------------------------------")
        print("开始视频转码")

        record_list = os.listdir("./record/")
        for i in record_list:
            a = i.split('.')
            if len(a) < 2:
                continue
            if a[1] == 'webm':
                videosrcname = "./record/" + i
                videotargetname = "./record/" + a[0] + ".mp4"
                newthread1 = DecodeThread(videosrcname, videotargetname)
                newthread1.start()
    


@socketio.on('disconnect')
def disconnect_event():
    # for i,j in session.items():
    #     print(i,j)
    # socketio.manage_session
    sid = request.sid
    # print(sid)
    debug_output(f"detect {sid} disconnect!")
    # event = {'client' : sid, 'room' : '1'}
    # leaveRoom(event)
    
@socketio.on("connect")
def connect_event():
    
    # disconnect(request.sid)
    # 检查是否存在, 要设置双向内容
    # 检查是否被老师断开
    if teacher_killed.count(request.cookies['userid']) != 0:
        teacher_killed.remove(request.cookies['userid'])
        emit("get_killed", room=request.sid)
        return
        
        
    
    global sid_to_clientid
    global userid_to_sid
    debug_output("connect event!")
    userid = request.cookies['userid'] 
    now_sid = request.sid
    debug_output(f"connect event from {now_sid}")
    if userid in userid_to_sid:
        leave_room(ROOM_NAME, sid=userid_to_sid[userid])
        debug_output(f'history_sid = {userid_to_sid[userid]}, nowsid = {now_sid}')
        old_sid = userid_to_sid[userid]

        clientid = sid_to_clientid[old_sid]
        
        del sid_to_clientid[old_sid]
        
        sid_to_clientid[now_sid] = clientid
        userid_to_sid[userid] = now_sid
        
        join_room(ROOM_NAME, sid = now_sid)
        
    
    # sid_to_userid[sid] = request.cookies['userid']
    
    

@socketio.on("detect_disconnect")
def detect_disconnect(sid, userid):
    debug_output(f"teacher detect user {userid}disconnect!")
    sid_to_kill = get_new_sid(sid)
    event = {'client' : sid, 'userid' : userid, 'room' : ROOM_NAME, 'teacher_killed' : 1}
    teacher_killed.append(userid)
    leaveRoom(event)
    
    disconnect(sid=sid_to_kill)
    # 
    # leave_room(event)
    # try:
    #     del sid_to_userid[sid]
    # except:
    #     pass


# TODO 删除这个事件
@socketio.on("reconnect")
def reconnect_success(clientid):
    pass

# TODO 删除这个事件
@socketio.on("actuall_exit")
def actuall_exit():
    debug_output("TRUELY_EXITING")



if __name__ == "__main__":
    # print("INS")
    ssl_certificate = config_info['ssl']['crt']
    ssl_certificate_key = config_info['ssl']['key']
    socketio.run(app, host='0.0.0.0', port=8080, debug=DEBUG, keyfile=ssl_certificate_key, certfile=ssl_certificate )
    # ssl_context=(ssl_certificate, ssl_certificate_key)
