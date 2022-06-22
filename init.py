# coding=GB18030
from datetime import datetime
from distutils.log import debug
from hashlib import md5
import shutil
from socket import socket
import threading
import ffmpeg
import random
import os
import threading
import sys
import time
import flask
from matplotlib.pyplot import get
from server_src.read_config import read_from_config_file, config_info
from flask import make_response, request, render_template, redirect, send_from_directory, session, url_for
from flask_socketio import SocketIO, emit, disconnect,join_room, leave_room, close_room
from server_src.MyConstants import DB_URL, DEBUG
from server_src.DatabaseIO import db, Student
import jinja2
app = flask.Flask(__name__)
app.config['SECRET_KEY'] = "r`9[M-AtuO"
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
socketio = SocketIO(app, async_mode = None)# , ping_interval=3, ping_timeout=3
room_with_teacher = False
teacher_sid = []
callingList = {}
sid_to_clientid = {}
userid_to_sid = {}
# userid_to_logtime = {}
teacher_killed = []
ROOM_NAME = '1'
if len(sys.argv) > 1:
    read_from_config_file(sys.argv[1])
else:
    read_from_config_file("./webrtc-Tony.conf")
record_dir = config_info['root_dir']
    
def RemoveDir(filepath):
    if not os.path.exists(filepath):
        os.mkdir(filepath)
    else:
        shutil.rmtree(filepath)
        os.mkdir(filepath)
# print(ssl_certificate, ssl_certificate_key)

RemoveDir(record_dir)
# 功能性函数

def debug_output(*message):
    if DEBUG:
        print(message)
    else:
        with open(config_info['log'], 'a') as f:
            f.write(message)

def check_password_strength(password):
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
        os.remove(self.fin)
        debug_output(f"{self.fin} decode finish!")
        # print_time(self.name, self.delay, 5)
        # print ("退出线程：" + self.name)


    
def get_new_sid(clientsid : str):
    new_sid = None
    new_sid : str
    for (i,j) in sid_to_clientid.items():
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
        resp = make_response(render_template("index.html"))
        resp.delete_cookie('userid')
        resp.delete_cookie('username')
        resp.delete_cookie('userlevel')
        return resp
    else:
        user_id = request.form['ID']
        user_password = request.form['passwd']
        user_name = "NULL"
        login_status = -1
        user_userlevel = '0'
        #-1: 用户名/密码错误, 0 : 正常, 1 : 需要更改密码 
        with app.app_context():
            satisfy_user = Student.query.filter_by(stu_no=user_id, stu_password=md5(user_password.encode("GB18030")).hexdigest()).first()#
            satisfy_user : Student
            # print(f"passwd = {satisfy_user.stu_password}, hashcode = {calcans}")
            if not satisfy_user:
                login_status = -1
            elif user_password == user_id:
                login_status = 1 
                user_userlevel = satisfy_user.stu_userlevel
                user_name = satisfy_user.stu_name
            else :
                login_status = 0
                user_userlevel = satisfy_user.stu_userlevel
                user_name = satisfy_user.stu_name
        
        if login_status == 1:
            resp = make_response(redirect(url_for('change_password')))
            resp.set_cookie('userid', user_id)
            return resp
        elif login_status == -1:
            # __output("login fail")
            return render_template("index.html", user_id=user_id)
        else :
            if user_userlevel == '0':
                resp = make_response(redirect(url_for('student_record', user_id = user_id)))
                resp.set_cookie('userid', user_id)
                resp.set_cookie('username', user_name.encode('utf8').decode('utf8'))
                resp.set_cookie('userlevel', user_userlevel)
                return resp
            else :
                resp = make_response(redirect(url_for('teacher_monitor', user_id = user_id)))
                resp.set_cookie('username', user_name.encode('utf8').decode('utf8'))
                resp.set_cookie('userid', user_id)
                resp.set_cookie('userlevel', user_userlevel)
                return resp


@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    
    if(request.method == 'GET'):
        if 'userid' not in request.cookies:
            return redirect("website")
        user_id = request.cookies['userid']
        return render_template("change_password.html", user_id = user_id, test_result = 1)
    else:
        passwd1 = request.form['passwd1']
        passwd2 = request.form['passwd2']
        userid = request.cookies['userid']
        # debug_output("accept!")
        if(passwd1 == passwd2) :
            if not check_password_strength(passwd1):
                return render_template("change_password.html", user_id = userid, test_result = 2)
            with app.app_context():
                debug_output(userid)
                satisfy_user = Student.query.filter_by(stu_no=userid).first()
                satisfy_user : Student
                satisfy_user.stu_password = md5(passwd1.encode("GB18030")).hexdigest()
                db.session.commit()
            return redirect(url_for('website'))
        else :
            return render_template("change_password.html", user_id = userid, test_result = 0)


@app.route('/student/?<string:user_id>', methods=['GET', 'POST'])
def student_record(user_id):
    if 'userid' not in request.cookies or 'username' not in request.cookies or 'userlevel' not in request.cookies:
        return redirect('website') 
    user_id = request.cookies['userid']
    now_userlevel = request.cookies['userlevel']
    
    if(now_userlevel == None or now_userlevel != '0'):
        return "权限错误!"
    
    if user_id in userid_to_sid.keys():
        return "You already in the room!"
    return render_template("./student.html", 
                           userid=user_id, 
                           username=request.cookies['username'], 
                           framerate=config_info['frame']['rate'],
                           frameheight=config_info['frame']['height'],
                           framewidth=config_info['frame']['width']
                           )

@app.route('/teacher/?<string:user_id>', methods=['GET', 'POST'])
def teacher_monitor(user_id):
    if 'userid' not in request.cookies or 'username' not in request.cookies or 'userlevel' not in request.cookies:
        return redirect('website')
    user_id = request.cookies['userid']
    now_userlevel = request.cookies['userlevel']
    
    if(now_userlevel == None or now_userlevel != '1'):
        return "权限错误!"
    
    if user_id in userid_to_sid.keys():
        return "You already in the room!"
    satisfy_user = []
    with app.app_context():
        satisfy_user = Student.query.filter_by(stu_userlevel='0', stu_enable='1').all()#
        satisfy_user : list[Student]
    satisfy_user_dict = []
    for i in satisfy_user:
        satisfy_user_dict.append(i.get_dict())
    for index in range(len(satisfy_user_dict)):
        for key, value in satisfy_user_dict[index].items():
            value:str
            satisfy_user_dict[index][key] = value
            # print(value)
    return render_template("./teacher.html", satisfy_user=satisfy_user_dict, 
                           userid=user_id, 
                           username=request.cookies['username'], 
                           disconnect_time = config_info['disconnect'])


@app.route("/timeout", methods=['GET', 'POST'])
def tle():
    resp = redirect(url_for('website'))
    resp.delete_cookie('userid')
    resp.delete_cookie('username')
    resp.delete_cookie('userlevel')
    return resp    

@app.route('/static/js/<path:path>', methods=['GET'])
def send_js(path):
    # debug_output(f"get this!{path}")
    resp = make_response(send_from_directory('./static/js/', path))
    resp.headers['Content-Type'] = 'application/javascript; charset=gb18030'
    return resp

# 用于测试
@app.route('/teststudent', methods=['GET', 'POST'])
def test_student_record():
    user_id = None
    if 'userid' not in request.cookies:
        global userid_to_sid
        user_id = random.randint(1000000, 9999999)
        while str(user_id) in userid_to_sid.keys():
            user_id = random.randint(1000000, 9999999)
    else :
        user_id = request.cookies['userid']
    now_userlevel = None
    if 'userlevel' not in request.cookies:
        now_userlevel = '0'
    else :
        now_userlevel = request.cookies['userlevel']
    
    if(now_userlevel == None or now_userlevel != '0'):
        return "权限错误!"
    
    if user_id in userid_to_sid.keys():
        return "You already in the room!"

    resp = make_response(render_template("./student.html",
                                            userid=user_id, 
                                            username="NULL", 
                                            framerate=config_info['frame']['rate'],
                                            frameheight=config_info['frame']['height'],
                                            framewidth=config_info['frame']['width']))
    resp.set_cookie('userid', str(user_id))
    resp.set_cookie('userlevel', str(0))
    return resp

@app.route('/testteacher', methods=['GET', 'POST'])
def test_teacher_monitor():
    global userid_to_sid
    user_id = None
    if 'userid' not in request.cookies:
        global userid_to_sid
        user_id = random.randint(1000000, 9999999)
        while str(user_id) in userid_to_sid.keys():
            user_id = random.randint(1000000, 9999999)
    else :
        user_id = request.cookies['userid']
    now_userlevel = None
    if 'userlevel' not in request.cookies:
        now_userlevel = '1'
    else :
        now_userlevel = request.cookies['userlevel']
    
    if(now_userlevel == None or now_userlevel != '1'):
        return redirect(url_for("website"))
    
    if user_id in userid_to_sid.keys():
        return "You already in the room!"
    
    satisfy_user = []
    with app.app_context():
        satisfy_user = Student.query.filter_by(stu_userlevel='0', stu_enable='1').all()#
        satisfy_user : list[Student]
    satisfy_user_dict = []
    for i in satisfy_user:
        satisfy_user_dict.append(i.get_dict())
    for index in range(len(satisfy_user_dict)):
        for key, value in satisfy_user_dict[index].items():
            value:str
            satisfy_user_dict[index][key] = value
            # print(value)
    resp = make_response(render_template("./teacher.html", satisfy_user=satisfy_user_dict, userid=user_id, username="NULL",
                           disconnect_time = config_info['disconnect']))
    resp.set_cookie('userid', str(user_id))
    resp.set_cookie('userlevel', str(1))
    return resp


# 监听的事件

@socketio.on('join')
def creatOrJoin(roomid, userLevel, userid, username):
    # 这里的sid一定是第一个sid
    global room_with_teacher
    global teacher_sid
    global userid_to_sid
    global sid_to_clientid
    # global userid_to_logtime
    userlevel = request.cookies['userlevel']
    debug_output(f"receive join event, roomid = {roomid}, sessionId = {request.sid}, userlevel = {userlevel}")
    join_room(room=roomid)
    
    
    if request.sid in userid_to_sid.values():
        debug_output("impossible event! join with a previous sid!")
        return
    userid_to_sid[userid] = request.sid
    sid_to_clientid[request.sid] = request.sid
    nowtime = datetime.now()
    
    # timeformated ="-{:0>4}-{:0>2}-{:0>2}-{:0>2}-{:0>2}-{:0>2}".format(
    #     nowtime.year, nowtime.month, nowtime.day, nowtime.hour, nowtime.minute, nowtime.second)
    # userid_to_logtime[userid] = timeformated
    
    # student
    if userlevel == '0':
        if not room_with_teacher:
            debug_output(f"room joined, sid = {request.sid}")
        else :
            if len(callingList) == 0 or len(callingList[roomid]) == 0:
                callingList[roomid] = []
            for single_teachersid in teacher_sid:
                callingList[roomid].append({'From': sid_to_clientid[single_teachersid], 'To': request.sid, 'room': request.sid})
            emit('room_joined', room=get_new_sid(teacher_sid[0]))
            
            
    else :
        # teacher
        room_with_teacher = True
        teacher_sid.append(request.sid)
        single_teachersid = request.sid
        try:
        # catch people num in the room ,if  room not be created ,set num = 0
            how_many_people = len(socketio.sockio_mw.engineio_app.manager.rooms['/'][str(roomid)])
        except:
            how_many_people = 0
        if how_many_people > 0:
            callingList[roomid] = []
            for i in socketio.sockio_mw.engineio_app.manager.rooms['/'][str(roomid)]:
                if i != request.sid and teacher_sid.count(i) == 0:
                    callingList[roomid].append({'From': single_teachersid, 'To': sid_to_clientid[i], 'room': sid_to_clientid[i]})
            emit('room_joined', room=single_teachersid)



@socketio.on('start_call')
def startCall(roomid):
    userid = request.cookies['userid']
    debug_output(f"receive start_call event, roomid = {roomid}, sessionId = {userid_to_sid[userid]}")
    
    try:
        result = callingList[roomid].pop(0)
        if len(callingList) == 0:
            debug_output(f"impossible event: callingList empty")
        if len(callingList) == 0 or len(callingList[roomid]) == 0:
            emit('start_call', {'From': result['From'], 'To': result['To'], 'lastconnect': True}, room=get_new_sid(result['room']))
        else:
            emit('start_call', {'From': result['From'], 'To': result['To'], 'lastconnect': False}, room=get_new_sid(result['room']))
    except:
        pass

@socketio.on('webrtc_offer')
def webrtcOffer(event):
    debug_output(f"receive webrtc_offer event, from = {event['From']}, to = {event['To']}, room = {get_new_sid(event['To'])}")
    emit('webrtc_offer', event,
         room=get_new_sid(event['To']))


@socketio.on('webrtc_answer')
def webrtcAnswer(event):
    debug_output(f"receive webrtc_answer event, from = {event['From']}, to = {event['To']}, room = {get_new_sid(event['To'])}")
    
    # print('webrtc_answer event to peers in room {}'.format(event['roomid']))
    emit('webrtc_answer', event,
         room=get_new_sid(event['To']))


@socketio.on('webrtc_ice_candidate')
def webrtcIceCandidate(event):
    # print(event)
    debug_output(f"receive webrtc_ice_candidate event", "\n", f" peerid = {event['peerid']},room = {get_new_sid(event['To'])}")
    # print('webrtc_ice_candidate event to peers in room {}'.format(event['roomid']))
    
    
    emit('webrtc_ice_candidate', event, room=get_new_sid(event['To']))


@socketio.on('upload_blob')
def webrtcuploadblob(event):
    
    if event['userid'] not in userid_to_sid.keys():
        return
    
    if event['mode'] == 0:
        emit('transfer_complete', {'oper':event['oper']})
    else :
        emit("upload_accept")
    
    # global sid_to_userid
    # roomid = event['roomid']
    # clientid = event['clientid']
    debug_output(f"receive upload_blob event, userid = {event['userid']}, mode = {event['mode']}")
    oper = event['oper']
    datestring = event['date']
    # if roomid not in os.listdir('./record/'):
    #     os.mkdir('./record/{}'.format(roomid))
    recordType =  'screen' if oper == 0 else 'video' 
    # try:
    #     userid = sid_to_userid[clientid]
    # except:
    #     __output("How to get here?")
        
        
    with open('{}/u{}-{}-{}-{}.webm'.format(record_dir, event['userid'], event['username'], recordType, datestring), 'ab') as f:
        if event['data'] != [0]:
            f.write(event['data'])

    
    #     users = None
    #     users : Student
    #     with app.app_context():
    #         users = Student.query.filter_by(stu_no=event['userid']).first()
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
    pass
    # global sid_to_userid
    # if event['roomid'] not in os.listdir('./record/'):
    #     os.mkdir('./record/{}'.format(event['roomid']))
    # try:
    #     userid = sid_to_userid[event['clientid']]
    # except:
    # #     __output("How to get here?")
    # file = './{}.txt'.format(event['userid'])
    # with open(file, 'a', encoding='utf-8') as file:
    #     file.writelines(str({'roomid':event['roomid'],'userid':event['userid'],'mode':event['mode'],'time':int(time.time())}))
        # file.writelines(str(int(time.time())) + '\n')


@socketio.on('leave')
def leaveRoom(event):
    global room_with_teacher
    global teacher_sid
    # now_sid = request.sid
    userid = event['userid']
    clientid = event['client']
    now_sid = userid_to_sid[userid]
    
    
    # assert(now_sid == clientid)
    # assert(now_sid == userid_to_sid[userid])
    # assert(userid == event['userid'])
    # assert(event['client'] == clientid)
    
    try:
        # del sid_to_clientid[now_sid]
        sid_to_clientid.pop(now_sid)
        userid_to_sid.pop(userid)
        # del userid_to_sid[userid]
        # del userid_to_logtime[userid]
    except:
        pass
    
    debug_output(sid_to_clientid)
    debug_output(userid_to_sid)
    debug_output(f"receive leave event, clientid = {clientid}, userid = {userid}")
    try :
        if now_sid not in socketio.sockio_mw.engineio_app.manager.rooms['/'][str(event['room'])]:
            debug_output("notin!")
            # return 
    except KeyError:
        debug_output("keyError")
        return
    
    # if 1 < how_many_people <= 6:
    if teacher_sid.count(clientid) == 0:
        for i in teacher_sid:
            emit('leave_room', {'From': clientid, 'To': i, 'userid': userid, 'username' : event['username']}, room=get_new_sid(i))
    else :
        teacher_sid.remove(clientid)
        if len(teacher_sid) == 0:
            room_with_teacher = False
        for i in userid_to_sid.values():
            if sid_to_clientid[i] not in teacher_sid:
                emit('leave_room', {'From': clientid, 'To': i, 'userid': userid, 'username' : event['username']}, room=get_new_sid(i))
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
    ok_to_decode = True
    for i in sid_to_clientid.keys():
        if i in teacher_sid:
            ok_to_decode = False
            break
        
    
    if how_many_people == 0 or ok_to_decode:
        print("----------------------------------------")
        print("开始视频转码")

        record_list = os.listdir(f"{record_dir}")
        for i in record_list:
            a = i.split('.')
            if len(a) < 2:
                continue
            if a[1] == 'webm':
                videosrcname = f"{record_dir}/" + i
                videotargetname = f"{record_dir}/" + a[0] + ".mp4"
                newthread1 = DecodeThread(videosrcname, videotargetname)
                newthread1.start()
        print("视频转码结束")
        print("----------------------------------------")
        

    


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
    pass
    # print(session.get("test"))
    # session['test'] = request.sid
    # print(request.sid)
    # disconnect(request.sid)
    # 检查是否存在, 要设置双向内容
    # 检查是否被老师断开
    
    # sid_to_userid[sid] = request.cookies['userid']
    
@socketio.on("start_record")
def start_record_order():
    emit("start_record", room=ROOM_NAME)
            
            
    
    
@socketio.on("stop_record")
def stop_record_order():
    emit("stop_record", room=ROOM_NAME)

@socketio.on("detect_disconnect")
def detect_disconnect(sid, userid):
    debug_output(f"teacher detect user {userid}disconnect!")
    sid_to_kill = get_new_sid(sid)
    username = "NULL"
    with app.app_context():
        satisfy_user = Student.query.filter_by(stu_no=userid).first()#
        satisfy_user : Student
        if satisfy_user:
            username = satisfy_user.stu_name
    event = {'client' : sid, 'userid' : userid, 'room' : ROOM_NAME, 'teacher_killed' : 1, 'username' : username}
    teacher_killed.append(userid)
    leaveRoom(event)
    
    disconnect(sid=sid_to_kill)
    # 
    # leave_room(event)
    # try:
    #     del sid_to_userid[sid]
    # except:
    #     pass


@socketio.on("track_delete")
def delete_tracks(event):
    debug_output(f"receive track_delete event", "\n", f" peerid = {event['peerid']},room = {get_new_sid(event['To'])}")
    emit('track_delete', event, room=get_new_sid(event['To']))
    

@socketio.on("update_clientid")
def update_clientid(userid):
    if teacher_killed.count(userid) != 0:
        teacher_killed.remove(userid)
        emit("get_killed", room=request.sid)
        return
        
        
    
    global sid_to_clientid
    global userid_to_sid
    debug_output("connect event!")
    # session
    # userid = request.cookies['userid'] 
    now_sid = request.sid
    debug_output(f"connect event from {now_sid}")
    if userid in userid_to_sid.keys():
        leave_room(ROOM_NAME, sid=userid_to_sid[userid])
        debug_output(f'history_sid = {userid_to_sid[userid]}, nowsid = {now_sid}')
        old_sid = userid_to_sid[userid]

        clientid = sid_to_clientid[old_sid]
        
        sid_to_clientid.pop(old_sid)
        # del sid_to_clientid[]
        
        sid_to_clientid[now_sid] = clientid
        userid_to_sid[userid] = now_sid
        
        join_room(ROOM_NAME, sid = now_sid)
        
    




if __name__ == "__main__":
    # print("INS")
    ssl_certificate = config_info['ssl']['crt']
    ssl_certificate_key = config_info['ssl']['key']
    socketio.run(app, host='0.0.0.0', port=8080, debug=DEBUG, keyfile=ssl_certificate_key, certfile=ssl_certificate)
    # ssl_context=(ssl_certificate, ssl_certificate_key)
