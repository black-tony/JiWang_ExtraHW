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
const socket = io()
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
let roomid
let clientid
let lastconnect

// -------------------------set element event binding-------------------------------


// click button event binding function
connectbtn.addEventListener('click', async () => {
    mode = 3
    
    mediaconstraints = {
        audio: {
            echoCancellation: true,
            noiseSuppression: true,
            sampleRate: 44100
        },
        video: {
            width: { max: 1280 },
            height: { max: 720 },
            frameRate: {max: 30}
        }
    }
    joinRoom('1');
})


// click button event binding function
disconnectbtn.addEventListener('click', () => {
    leaveRoom('1',clientid)
})


// click button event binding function
sharescreen.addEventListener('click', () => {
    if(sharescreen.value == "0"){
        startShareScreen(mediaconstraints)
        sharescreen.value = "1"
        sharescreen.innerHTML = "stop share"
    }else if(sharescreen.value == "1"){
        stopShareScreen(mediaconstraints)
        sharescreen.value = "0"
        sharescreen.innerHTML = "share screen"
  }
})


// click button event binding function
hidelocalbox.addEventListener('click', () => {
    if(hidelocalbox.value == "0")
    {
        localvideocomponent.srcObject = undefined;
        hidelocalbox.value = "1"
        hidelocalbox.innerHTML = "show localbox"
    }
    else if(hidelocalbox.value == "1")
    {
        if(sharescreen.value == "0")
        {
            localvideocomponent.srcObject = localstream;
        }
        else if(sharescreen.value == "1")
        {
            localvideocomponent.srcObject = sharestream;
        }
        hidelocalbox.value = "0"
        hidelocalbox.innerHTML = "hide localbox"
    }
})


// before close window or reload page warning
window.addEventListener("beforeunload", function(event) {
    event.returnValue = ''
})


// close window or reload page will disconnect room
window.addEventListener("unload", function(event) {
    leaveRoom('1', clientid)
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

// 1
socket.on('start_call', async (event) => {
    isconnectcreator = true
    console.log('Socket event callback: start_call from',event.From,'to',event.To)
    if (event.lastconnect == true)
    {
        console.log('this connect is last connect')
        lastconnect = true
    }
    if (isconnectcreator) 
    {
        var peerid = event.From +':'+ event.To
        rtcpeerconnection[peerid] = new RTCPeerConnection(iceservers)

        addLocalTracks(peerid)
        if(mediarecorder == undefined)
        {
            startRecord(roomid)
            openBtn()
        }
        //当对面发送音视频来时执行
        rtcpeerconnection[peerid].ontrack = function(event){
            event.peerid = peerid
            console.log("enter some impossible function: student::ontrack")
        }
        // icecandidate(ICE) event : find shortest path
        rtcpeerconnection[peerid].onicecandidate = function(event){
            event.peerid = peerid
            sendIceCandidate2offer(event)
        }
        await createOffer(peerid)
    }
})

// 1
socket.on('webrtc_answer', (event) => {
    if(isconnectcreator)
    {
        var peerid = event['peerid']
        console.log('Socket event callback: webrtc_answer from',event.From,'to',event.To)
        rtcpeerconnection[peerid].setRemoteDescription(new RTCSessionDescription(event['sdp']))
    }
    if(lastconnect == true)
    {
        isconnectcreator = false
        lastconnect = undefined
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

// this function into room and send room id
async function joinRoom(room) {
    // get user local camera streams
    await setLocalStream(mediaconstraints)
    roomid = room
    console.log("roomURL: ",location.href.split('?')[0]+'?mode='+mode+"&room="+roomid)
    socket.emit('join', room, 0)
    showVideoConference()
}


// this function to leave room 
function leaveRoom(room,client){
    stopRecord(room)
    socket.emit('leave', {room:room,client:client})
    leaveVideoConference({'From':client,'To':'all'})
    alert('video coference closed, if you need new coversation, plz enter new room number');
    // alert('WARNING :plz wait for the transfer to complete before closing this page!!');
}


// this function to start record
function startRecord(room){
    // recoder stream
    mediarecorder = new MediaRecorder(localstream)
    // set stream mode (video or audio) 
    if(mode === 1){
        mediarecorder.mimeType = 'audio/webm; codecs=opus';
        console.log("recorder started");

    }else if(mode === 2 || mode === 3){
        mediarecorder.mimeType = 'video/webm; codecs=h264';
        // mediarecorder.audioChannels = 2;
        console.log("recorder started");
    }else{
        console.log('can\'t recorde, plz check your mode')
    }
    socket.emit('record_time',{roomid:room,clientid:clientid,mode:'start'})
    // set 10 sec trigger dataavailable and cut blob
    mediarecorder.start(10000);
    // event function
    mediarecorder.ondataavailable = function(e) {
        chunks.push(e.data);
        socket.emit('upload_blob',{data:chunks.shift(),roomid:room,clientid:clientid,mode:1});
        console.log('upload record !!');
    }
}


// this function to stop record
function stopRecord(room){
  if(mediarecorder != undefined){
    mediarecorder.stop()
    socket.emit('record_time',{roomid:room,clientid:clientid,mode:'stop'})
    console.log("recorder stopped");
    var atlast = chunks.length
    console.log("there are",atlast,"data need upload")
    if(atlast != 0){
      for (let i = 0; i < atlast; i++) {
        if(i == atlast-1){
          socket.emit('upload_blob',{data:chunks[i],roomid:room,clientid:clientid,mode:0})
        }else{
          socket.emit('upload_blob',{data:chunks[i],roomid:room,clientid:clientid,mode:1})
        }
      }
    }else{
      socket.emit('upload_blob',{data:[0],roomid:room,clientid:clientid,mode:0})
    }
  }
}


// start sharescreen function
// TODO : 把共享屏幕的replace改成同时
async function startShareScreen(mediaconstraints){
    var displayconstraints =  mediaconstraints
    displayconstraints.video = {width: { max: 1920 },height: { max: 1080 },frameRate: {max: 30},cursor: "always"}
    displayconstraints.audio = false
    try 
    {
        sharestream = await navigator.mediaDevices.getDisplayMedia(displayconstraints)
        localvideocomponent.srcObject = sharestream
        // senders.find(sender => sender.track.kind === 'video').replaceTrack(sharestream.getTracks()[0])
        for(i=0;i<senders.length;i++)
        {
            if(senders[i].track.kind === 'video')
            {
                senders[i].replaceTrack(sharestream.getTracks()[0]);
            }
        }
    } 
    catch (error) 
    {
        console.error('Could not get user screen', error)
        sharescreen.value = "0"
        sharescreen.innerHTML = "share screen"
    }
}


// stop sharescreen function
function stopShareScreen(){
    // senders.find(sender => sender.track.kind === 'video').replaceTrack(localstream.getTracks().find(track => track.kind === 'video'));
    for(i=0;i<senders.length;i++)
    {
        if(senders[i].track.kind === 'video')
        {
            senders[i].replaceTrack(localstream.getTracks().find(track => track.kind === 'video'));
        }
    }
    sharestream.getTracks()[0].stop()
    sharestream = undefined;
    localvideocomponent.srcObject = localstream
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
    if(sharestream != undefined)
    {
        stopShareScreen()
    }
    // stop localstream 
    trclen = Object.keys(rtcpeerconnection).length
    if(trclen != 0)
    {
        for (var i = 0; i < trclen; i++) 
        {
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
    var d = document.getElementById(event['From']+':'+event['To']) || document.getElementById(event['To']+':'+event['From'])
    try
    {
        d.remove()
    }
    catch(error)
    {
        console.log(d)
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



// this function get user camera stream(local)
async function setLocalStream(mediaconstraints) {
    let stream
    try 
    {
        // if calback ,show stream and audio
        stream = await navigator.mediaDevices.getUserMedia(mediaconstraints)
    }
    catch(error)
    {
        console.error('Could not get user media', error)
        alert('error,check your microphone and webcame')
        leaveVideoConference({'From':'all','To':'all'})
    }
    localstream = stream
    localvideocomponent.srcObject = stream
}


// add local stream to webrtc track
function addLocalTracks(peerid)
{
    localstream.getTracks().forEach(
        track => senders.push(rtcpeerconnection[peerid].addTrack(track, localstream))
    )
}


// 1
async function createOffer(peerid) {
    // var sessionDescription
    try 
    {
        var sessionDescription = await rtcpeerconnection[peerid].createOffer()
        rtcpeerconnection[peerid].setLocalDescription(sessionDescription)
        console.log("set local description finish!")
    } catch (error) 
    {
        console.error("error happen in function createOffer")
        console.error(error)
    }
    console.log('creat offer from',peerid.split(':')[1],'to',peerid.split(':')[0])
    socket.emit('webrtc_offer', {
        type: 'webrtc_offer',
        sdp: sessionDescription,
        roomid,
        peerid:peerid,
        From:peerid.split(':')[1],
        To:peerid.split(':')[0]
    })
}


// send candidate event to server 
async function sendIceCandidate2offer(event) {
    var peerid = event.peerid
    if (event.candidate) 
    {
        await socket.emit('webrtc_ice_candidate', {
            roomid,
            label: event.candidate.sdpMLineIndex,
            candidate: event.candidate.candidate,
            peerid:peerid,
            From:peerid.split(':')[1],
            To:peerid.split(':')[0]
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
  for (i = 0; i < slen-1; i++) 
  {
    bt[1].remove()
  }
};