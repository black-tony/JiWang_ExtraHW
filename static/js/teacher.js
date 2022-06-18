// DOM elements.
const roomselectioncontainer = document.getElementById('room-selection-container')
const roominput = document.getElementById('room-input')
const connectbtn = document.getElementById('connect-button')
const disconnectbtn = document.getElementById('disconnect-button')
const sharescreen = document.getElementById('share-screen')
const hidelocalbox = document.getElementById('hide-localbox')
const videochatcontainer = document.getElementById('video-chat-container')
const localvideocomponent = document.getElementById('local-video')
const remotevideocomponent = document.getElementById('video-chat-container')
const userid = document.getElementById('userid').innerHTML
const username = document.getElementById('username').innerHTML
const socket = io({closeOnBeforeunload: false})
//  stun/turn servers.
const iceservers = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' },
    { urls: 'stun:stun2.l.google.com:19302' }
  //  { urls: 'stun:stun3.l.google.com:19302' }
  ],
}
// { url: 'stun:mysite.com:3478' },
// 	{
// 		url: 'turn:mysite.com,
// 		credential: 'turnpwd',
// 		username: 'turnadmin'
// 	}

// initial recoder global variable
var chunks = [];
var mediarecorder
// record audio or video
var blob
// control webcam and audio
var mediaconstraints
// var for mode video or audio 
var mode = 0
// var audioURL
var recoder


let senders = []
let localstream
let remotestream
let sharestream
let isconnectcreator
// Connection between the local device and the remote peer.
var rtcpeerconnection = {}
var videocontainers = {}
var disconnect_detector = {}
let roomid
let clientid
let lastconnect

// -------------------------set element event binding-------------------------------

window.onload = function()
{
    mode = 3;
    joinRoom('1');
}
// close window or reload page will disconnect room
window.addEventListener("unload", function(event) {
    leaveRoom('1', clientid)
})
// before close window or reload page warning
window.addEventListener("beforeunload", function(event) {
    event.returnValue = ''
})

// -------------------------set socket event -------------------------------

// set client id
socket.on('connect', () => {
    if (clientid == undefined)
    {
        clientid = socket.id;
        console.log('your client id :',socket.id)
    }
});
socket.on('room_joined', async () => {
    console.log('Socket event callback: room_joined')
    // start connect
    socket.emit('start_call', roomid)
})


// 2
socket.on('webrtc_offer', async (event) => {
    console.log('Socket event callback: webrtc_offer from',event.From,'to',event.To)
    if (!isconnectcreator) 
    {
        var peerid = event['peerid']
        // creat new peerconnect ,and use ice server information(stun or turn server)
        rtcpeerconnection[peerid] = new RTCPeerConnection(iceservers)
        //老师不需要录屏
        //对面发来track的时候可以call下一个
        videocontainers[peerid] = await createNewContainer(peerid)

        rtcpeerconnection[peerid].ontrack = function(event){
            event.peerid = peerid
            setRemoteStream(event)
            socket.emit('start_call', roomid)
        }
        rtcpeerconnection[peerid].oniceconnectionstatechange = function(){
            console.log(rtcpeerconnection[peerid].iceConnectionState)
            switch(rtcpeerconnection[peerid].iceConnectionState)
            {
                case 'disconnected':
                    console.error('detect peer disconnect!')
                    disconnect_detector[peerid] = setTimeout(disconnect_peer, 10 * 1000, peerid, event['userid']) // TODO : 时间暂定15s
                    break;
                case 'failed':
                    console.error('detect peer fail!')
                    break;
                case 'closed':
                    console.error('detect connection close!')
                    break;
                case 'connected':
                    if(disconnect_detector[peerid] != undefined)
                    {
                        clearTimeout(disconnect_detector[peerid])
                        delete disconnect_detector[peerid]
                    }
                    break;
                case 'connecting':
                    console.error('detect connection connecting!')
                default:
                    break;

            }
        }
        rtcpeerconnection[peerid].onicecandidate = function(event){
            event.peerid = peerid
            sendIceCandidate2answer(event)
        }
        // RTCSessionDescription : return our info to remote computer
        rtcpeerconnection[peerid].setRemoteDescription(new RTCSessionDescription(event['sdp']))
        await createAnswer(peerid, userid)
    }
    else
    {
        console.log('webrtc_offer Error!')
    }
})






socket.on('webrtc_ice_candidate', (event) => {
    console.log('Socket event callback: webrtc_ice_candidate from',event.From,'to',event.To)
    // ICE candidate configuration.
    var candidates = new RTCIceCandidate({
        sdpMLineIndex: event.label,
        candidate: event.candidate,
    })
    rtcpeerconnection[event.peerid].addIceCandidate(candidates)
})


socket.on('leave_room', (event) => {
    removeRemoteStream(event)
    console.log('clinet:'+event['From']+' leave room')
})



socket.on('transfer_complete', async () => {
    mode = 0
    roomid,clientid,recoder,mediarecorder = undefined,undefined,undefined,undefined
    chunks = [];
    alert('transfer record complete!');
})


// -------------------------set logic function-------------------------------


function disconnect_peer(peerid, user_id)
{
    let teacher_sid = peerid.split(':')[0]
    let student_sid = peerid.split(':')[1]
    if(teacher_sid != clientid)
        console.error("disconnect_peer error!")
    socket.emit('detect_disconnect', student_sid, user_id)
    delete disconnect_detector[peerid]
}


// this function into room and send room id
async function joinRoom(room) 
{
    // get user local camera streams
    // await setLocalStream(mediaconstraints)
    roomid = room
    console.log("roomURL: ",location.href.split('?')[0]+'?mode='+mode+"&room="+roomid)
    socket.emit('join', room, 9, userid, username)
    showVideoConference()
}


// this function to leave room 
function leaveRoom(room,client){
    // stopRecord(room)
    
    socket.emit('leave', {room:room, client:client,userid:userid,username:username,teacher_killed: 0})
    leaveVideoConference({'From':client,'To':'all'})
    alert('video coference closed, if you need new coversation, plz enter new room number');
        // alert('WARNING :plz wait for the transfer to complete before closing this page!!');
}


// this function cancle video display none if into room and get local camera stream
function showVideoConference() {
    roomselectioncontainer.style = 'display: none'
    videochatcontainer.style = 'display: block'
    disconnectbtn.disabled = false;
    disconnectbtn.innerHTML = 'leave Room';
}


// leave video conference
function leaveVideoConference(event) {
  // hide video div and show choose page
  roomselectioncontainer.style = 'display: block'
  videochatcontainer.style = 'display: none'
  // if share screem not stop ,clear variable and stop it.
//   if(sharestream != undefined){
//     stopShareScreen()
//   }
  // stop localstream 
  trclen = Object.keys(rtcpeerconnection).length
  if(trclen != 0)
  {
        for (var i = 0; i < trclen; i++) {
            rtcpeerconnection[Object.keys(rtcpeerconnection)[0]].getSenders().forEach(function(sender) {
                sender.track.stop();
            });
            rtcpeerconnection[Object.keys(rtcpeerconnection)[0]].close();
        }
  }
  // stop track
  a = localstream.getTracks().length
  if(localstream.getTracks().length != 0)
  {
        for(i=0;i<a;i++)
        {
            localstream.getTracks()[0].stop()
        }
  }
  // close button
  closeBtn()
  // reset const
  senders = [];
  // reset variable
  localstream,remotestream,isconnectcreator,mediaconstraints,isconnectcreator,roomid = undefined,undefined,undefined,undefined,undefined,undefined
  c = 0
}


function removeRemoteStream(event) {
    // try
    // {
    //     d1.remove()
    // }
    // catch(error)
    // {
    //     console.log(d1)
    // }
    // try
    // {
    //     d2.remove()
    // }
    // catch(error)
    // {
    //     console.log(d2)
    // }
    var d3 = document.getElementById(event['From']+':'+event['To']) || document.getElementById(event['To']+':'+event['From'])
    try
    {
        d3.remove()
    }
    catch(error)
    {
        console.log(d3)
    }
    if(rtcpeerconnection[event['From']+':'+event['To']])
    {
        rtcpeerconnection[event['From']+':'+event['To']].close();
        delete rtcpeerconnection[event['From']+':'+event['To']]
    }
    else
    {
        try
        {
            rtcpeerconnection[event['To']+':'+event['From']].close();
            delete rtcpeerconnection[event['To']+':'+event['From']]
        }
        catch(error)
        {
            
        }
    }
    
}

// 2
async function createAnswer(peerid, user_id) {
    // var sessionDescription
    try 
    {
        var sessionDescription = await rtcpeerconnection[peerid].createAnswer()
        rtcpeerconnection[peerid].setLocalDescription(sessionDescription)
    } 
    catch (error) 
    {
        console.error("error happen in function createAnswer")

        console.error(error)
    }
    console.log('creat answer from',peerid.split(':')[0],'to',peerid.split(':')[1])
    
    socket.emit('webrtc_answer', {
        type: 'webrtc_answer',
        sdp: sessionDescription,
        roomid,
        peerid:peerid,
        From:peerid.split(':')[0],
        To:peerid.split(':')[1],
        userid:user_id
    })
}

async function createNewContainer(peerid){
    let firststream = document.getElementById(peerid)
    if( firststream != null)
    {
        console.error("this session id is already used!")
        return
    }
    var div = document.createElement("div");
    // div.setAttribute("class", "video-position");
    div.setAttribute("id", peerid);
    div.setAttribute("autoplay", "autoplay");
    div.setAttribute("playsInline", "playsInline");
    remotevideocomponent.insertBefore(div, null);
    var desc = document.createTextNode(peerid)
    div.insertBefore(desc, null)
    var br = document.createElement("br")
    div.insertBefore(br, null)

    // videocontainers[peerid] = div
    return div
}

// set remote stream 
function setRemoteStream(event) {
    if(event.track.kind == 'audio')
        return
    
    console.log("set remote stream event!!")
    let firststream = document.getElementById(event.peerid)
    let secondstream = document.getElementById(event.peerid + "2")
    if( firststream != null && secondstream != null)
    {
        console.error("a third line!")
        return
    }
    var div = document.createElement("video");
    div.setAttribute("class", "remote-video");
    div.setAttribute("id", event.peerid + (firststream == null ? "_1" : "_2"));
    div.setAttribute("autoplay", "autoplay");
    div.setAttribute("playsInline", "playsInline");
    div.srcObject = event.streams[0]
    console.log(event.track)//TODO
    videocontainers[event.peerid].insertBefore(div, null);
    remotestream = event.stream
}



// send candidate event to server 
async function sendIceCandidate2answer(event) {
    var peerid = event.peerid
    if (event.candidate) {
        await socket.emit('webrtc_ice_candidate', {
            roomid,
            label: event.candidate.sdpMLineIndex,
            candidate: event.candidate.candidate,
            peerid:peerid,
            From:peerid.split(':')[0],
            To:peerid.split(':')[1]
        })
    }
}



// open button
function openBtn(){
    sharescreen.disabled = false;
    hidelocalbox.disabled = false
}


// close button
function closeBtn(){
    sharescreen.disabled = true;
    sharescreen.value = "0"
    sharescreen.innerHTML = "share screen"
    hidelocalbox.disabled = true
    hidelocalbox.value = "0"
    hidelocalbox.innerHTML = "hide localbox"
    disconnectbtn.disabled = true;
    disconnectbtn.innerHTML = 'wait for connect....';
    var bt = document.getElementsByClassName('remote-video');
    slen = Object.keys(bt).length
    for (i = 0; i < slen-1; i++) {
        bt[1].remove()
    }
};
