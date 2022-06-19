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
const disconnect_time = Number(document.getElementById("disconnect-time").innerHTML)
const socket = io({closeOnBeforeunload: false, transports: ['websocket']})
//  stun/turn servers.
const iceservers = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' },
    { urls: 'stun:stun2.l.google.com:19302' }
    // ,
    // {
	// 	url: "turn:8.130.97.48:3478",
	// 	credential: 'Tony020731',
	// 	username: 'BlackTony'
	// }
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
    console.log('now client id :',socket.id)
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
socket.on('disconnect', ()=>{
    console.log("disconnect!")
})

// 2
socket.on('webrtc_offer', async (event) => {
    console.log('Socket event callback: webrtc_offer from',event.From,'to',event.To)
    isconnectcreator = false
    if (!isconnectcreator) 
    {
        var peerid = event['peerid']
        var target_userid = event['userid']
        // creat new peerconnect ,and use ice server information(stun or turn server)
        if(videocontainers[target_userid] == undefined)
            videocontainers[target_userid] = await createNewContainer(target_userid)
        if(rtcpeerconnection[target_userid] == undefined)
        {
            rtcpeerconnection[target_userid] = new RTCPeerConnection(iceservers)
            rtcpeerconnection[target_userid].ontrack = function(event){
                event.peerid = peerid
                event.userid = target_userid
                setRemoteStream(event)
                // socket.emit('start_call', roomid)
            }
            rtcpeerconnection[target_userid].oniceconnectionstatechange = function(){
                console.log(rtcpeerconnection[target_userid].iceConnectionState)
                switch(rtcpeerconnection[target_userid].iceConnectionState)
                {
                    case 'disconnected':
                        console.error('detect peer disconnect!')
                        var d3 = document.getElementById(target_userid + "_monitor")
                        d3.innerHTML = target_userid + event['username'] + "检测到掉线, 正在重连"
                        disconnect_detector[target_userid] = setTimeout(disconnect_peer, disconnect_time * 1000, peerid, event['userid']) 
                        break;
                    case 'failed':
                        console.error('detect peer fail!')
                        break;
                    case 'closed':
                        console.error('detect connection close!')
                        break;
                    case 'connected':
                        var d3 = document.getElementById(target_userid + "_monitor")
                        d3.innerHTML = target_userid + event['username'] + "已连接"
                        if(disconnect_detector[target_userid] != undefined)
                        {
                            clearTimeout(disconnect_detector[target_userid])
                            delete disconnect_detector[target_userid]
                        }
                        break;
                    case 'connecting':
                        console.error('detect connection connecting!')
                    default:
                        break;
    
                }
            }
            rtcpeerconnection[target_userid].onicecandidate = function(event){
                event.peerid = peerid
                event.userid = userid
                sendIceCandidate2answer(event)
            }
        }
        


        
        // RTCSessionDescription : return our info to remote computer
        rtcpeerconnection[target_userid].setRemoteDescription(event['sdp'])
        await createAnswer(peerid, userid, target_userid)
        socket.emit('start_call', roomid)
    }
    else
    {
        console.log('webrtc_offer Error!')
    }
})






socket.on('webrtc_ice_candidate', async(event) => {
    console.log('Socket event callback: webrtc_ice_candidate from',event.From,'to',event.To)
    // ICE candidate configuration.
    var candidates = new RTCIceCandidate({
        sdpMLineIndex: event.label,
        candidate: event.candidate,
    })
    rtcpeerconnection[event.userid].addIceCandidate(candidates)
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

socket.on("track_delete", (event)=>{
    removeRemoteStreamByTrackID(event.userid, event.streamid)
})



// -------------------------set logic function-------------------------------


function disconnect_peer(peerid, user_id)
{
    let teacher_sid = peerid.split(':')[0]
    let student_sid = peerid.split(':')[1]
    if(teacher_sid != clientid)
        console.error("disconnect_peer error!")
    socket.emit('detect_disconnect', student_sid, user_id)
    delete disconnect_detector[user_id]
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
    var d3 = document.getElementById(event['userid'] + "_monitor")
    if(d3 == null)
        return
    d3.innerHTML = event['userid'] +" " + event['username'] + " " + "已掉线"
    

    if(rtcpeerconnection[event['userid']])
    {
        rtcpeerconnection[event['userid']].close();
        delete rtcpeerconnection[event['userid']]
    }
    else
    {
        try
        {
            rtcpeerconnection[event['userid']].close();
            delete rtcpeerconnection[event['userid']]
        }
        catch(error)
        {
            
        }
    }
    
}
function removeRemoteStreamByTrackID(target_userid, streamid)
{
    if(videocontainers[target_userid] == undefined)
        return
    let firststream = document.getElementById(target_userid + "_1")
    let secondstream = document.getElementById(target_userid + "_2")
    if(firststream != null)
    {
        if(firststream.srcObject != undefined )
        {
            if(firststream.srcObject.id == streamid)
            {
                firststream.srcObject = undefined
                return
            }

        }
    }
    if(secondstream != null)
    {
        if(secondstream.srcObject != undefined )
        {
            if(secondstream.srcObject.id == streamid)
            {
                secondstream.srcObject = undefined
                return
            }

        }
    }
}
// 2
async function createAnswer(peerid, user_id, target_userid) {
    // var sessionDescription
    try 
    {
        var sessionDescription = await rtcpeerconnection[target_userid].createAnswer()
        rtcpeerconnection[target_userid].setLocalDescription(sessionDescription)
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
        userid:user_id,
        username:username
    })
}

async function createNewContainer(peerid){
    let firststream = document.getElementById(peerid)
    if( firststream != null)
    {
        // console.error("this session id is already used!")
        return firststream
    }
    var div = document.createElement("div");
    // div.setAttribute("class", "video-position");
    div.setAttribute("id", peerid);
    // div.setAttribute("autoplay", "autoplay");
    // div.setAttribute("playsInline", "playsInline");
    remotevideocomponent.insertBefore(div, null);
    var desc = document.createElement('div')
    desc.innerHTML = peerid + "已连接"
    desc.setAttribute('id', peerid + "_monitor")
    div.insertBefore(desc, null)
    // var br = document.createElement("br")
    // div.insertBefore(br, null)



    var video1 = document.createElement("video");
    video1.setAttribute("class", "remote-video");
    video1.setAttribute("id", peerid + "_1");
    video1.setAttribute("autoplay", "autoplay");
    video1.setAttribute("playsInline", "playsInline");
    div.insertBefore(video1, null);

    var video2 = document.createElement("video");
    video2.setAttribute("class", "remote-video");
    video2.setAttribute("id", peerid + "_2");
    video2.setAttribute("autoplay", "autoplay");
    video2.setAttribute("playsInline", "playsInline");
    // div.srcObject = event.streams[0]
    // console.log(event.track)//TODO
    // console.log(event.streams)
    div.insertBefore(video2, null);
    // videocontainers[peerid] = div
    return div
}

// set remote stream 
function setRemoteStream(event) {
    if(event.track.kind == 'audio')
        return
    
    console.log("set remote stream event!!")
    let firststream = document.getElementById(event.userid + "_1")
    let secondstream = document.getElementById(event.userid + "_2")
    if( firststream.srcObject != null && secondstream.srcObject != null)
    {
        console.error("a third line!")
        return
    }
    if(firststream.srcObject == undefined)
    {
        firststream.srcObject = null
        firststream.srcObject = event.streams[0]
    }
    else if(secondstream.srcObject == undefined)
    {
        secondstream.srcObject = null
        secondstream.srcObject = event.streams[0]
    }
    console.log(event.streams)
    console.log(event.track)
    
    // div.srcObject = event.streams[0]
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
            To:peerid.split(':')[1],
            userid:event.userid,
            username:username
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
