// DOM elements.
const roomselectioncontainer = document.getElementById('room-selection-container')
const roominput = document.getElementById('room-input')
const connectbtn = document.getElementById('connect-button')
const disconnectbtn = document.getElementById('disconnect-button')
const sharescreen = document.getElementById('share-screen')
const sharecamera = document.getElementById('share-camera')

const sharevideo = document.getElementById('share-video')
const videochatcontainer = document.getElementById('video-chat-container')
const localvideocomponent = document.getElementById('local-video')
const localscreencomponent = document.getElementById('local-screen')
const remotevideocomponent = document.getElementById('video-chat-container')
const userid = document.getElementById('userid').innerHTML
const username = document.getElementById('username').innerHTML
const socket = io({closeOnBeforeunload: false, transports: ['websocket']})
const frameragte = Number(document.getElementById('framerate').innerHTML)
const frameheight =  Number(document.getElementById('frameheight').innerHTML)
const framewidth = Number(document.getElementById('framewidth').innerHTML)

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
const videocomponentArray = [ localscreencomponent, localvideocomponent, localvideocomponent]
var chunksArray = [[], [], []];
var mediarecorderArray = [undefined, undefined, undefined];
var datestringArray = [undefined, undefined, undefined];
var localstreamArray = [undefined, undefined, undefined]
var chunks = [];
var chunks2 = [];
var mediarecorder
var mediarecorder2
// record audio or video
// var blob
var inroom = false;
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
let teacher_sid

// -------------------------set element event binding-------------------------------


// click button event binding function
connectbtn.addEventListener('click', async () => {
    mode = 3
    connectbtn.disabled = true
    mediaconstraints = {
        audio: {
            echoCancellation: true,
            noiseSuppression: true,
            sampleRate: 44100
        },
        video: {
            width: { ideal: framewidth, max: 1920 },
            height: { ideal: frameheight, max: 1080 },
            frameRate: {ideal: frameragte, max: 15}
        }
    }
    joinRoom('1');
})


// click button event binding function
disconnectbtn.addEventListener('click', () => {
    leaveRoom('1',clientid)
})


// click button event binding function
sharescreen.addEventListener('click', async () => {
    sharescreen.disabled = true
    if(sharescreen.value == "0")
    {
        var tmpconstraints = mediaconstraints
        tmpconstraints.audio = false
        if(await startShareStream(tmpconstraints, 0, '1') == false)
        {
            sharescreen.disabled = false
            return 
        }
        sharescreen.value = "1"
        sharescreen.innerHTML = "停止录制屏幕"
    }
    else if(sharescreen.value == "1")
    {
        stopShareStream(0, '1')
        sharescreen.value = "0"
        sharescreen.innerHTML = "开始录制屏幕"
    }
    sharescreen.disabled = false
})


// // click button event binding function
// hidelocalbox.addEventListener('click', () => {
//     if(hidelocalbox.value == "0")
//     {
//         localvideocomponent.srcObject = undefined;
//         hidelocalbox.value = "1"
//         hidelocalbox.innerHTML = "show localbox"
//     }
//     else if(hidelocalbox.value == "1")
//     {
//         if(sharescreen.value == "0")
//         {
//             localvideocomponent.srcObject = localstream;
//         }
//         else if(sharescreen.value == "1")
//         {
//             localvideocomponent.srcObject = sharestream;
//         }
//         hidelocalbox.value = "0"
//         hidelocalbox.innerHTML = "hide localbox"
//     }
// })

//两个是冲突的
sharecamera.addEventListener('click', async() => {

    sharecamera.disabled = true
    if(sharecamera.value == "0")
    {
        var tmpconstraints = mediaconstraints
        tmpconstraints.audio = false
        sharevideo.disabled = true
        if(await startShareStream(mediaconstraints, 1, '1') == false)
        {
            sharecamera.disabled = false;
            sharevideo.disabled = false;
            return;
        }
        
        sharecamera.value = "1"
        sharecamera.innerHTML = "停止录制摄像头"

    }
    else if(sharecamera.value == "1")
    {
        stopShareStream(1, '1')
        sharecamera.value = "0"
        sharecamera.innerHTML = "开始录制摄像头"
        sharevideo.disabled = false;
    }
    sharecamera.disabled = false;
})
sharevideo.addEventListener('click', async() => {
    sharevideo.disabled = true
    if(sharevideo.value == "0")
    {
        sharecamera.disabled = true
        if(await startShareStream(mediaconstraints, 2, '1') == false)
        {
            sharevideo.disabled = false;
            sharecamera.disabled = false;
            return;
        }
        
        sharevideo.value = "1"
        sharevideo.innerHTML = "停止录制视频+音频"
    }
    else if(sharevideo.value == "1")
    {
        stopShareStream(2, '1')
        sharevideo.value = "0"
        sharevideo.innerHTML = "开始录制视频+音频"
        sharecamera.disabled = false
    }
    sharevideo.disabled = false
})



// before close window or reload page warning
window.onbeforeunload =  function(event) {
    // socket.emit("actuall_exit")
    // event.returnValue = ""
}


// close window or reload page will disconnect room
window.addEventListener("unload", async function(event) {
    // socket.emit("actuall_exit")
    await leaveRoom('1', clientid)
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


socket.on('disconnect', ()=>{
    console.log("disconnect!")
})

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
        // for(var i = 0; i < 3; i++)
        // {
        //     if(datestringArray[i] != undefined)
        //     {
        //         console.error("add this")
        //         addLocalTracks(peerid, localstreamArray[i])
        //         await createOffer()
        //     }
        // }
        rtcpeerconnection[peerid].oniceconnectionstatechange = function(){
            console.log(rtcpeerconnection[peerid].iceConnectionState)
            switch(rtcpeerconnection[peerid].iceConnectionState)
            {
                case 'disconnected':
                    console.error('detect peer disconnect!')
                    break;
                case 'failed':
                    console.error('detect peer fail!')
                    break;
                case 'closed':
                    console.error('detect connection close!')
                    break;
                case 'connected':
                    break;
                case 'connecting':
                    console.error('detect connection connecting!')
                default:
                    break;

            }
        }
        if(localstreamArray[0] != undefined)
            addLocalTracks(peerid, localstreamArray[0])
        if(localstreamArray[1] != undefined)
            addLocalTracks(peerid, localstreamArray[1])
        if(localstreamArray[2] != undefined)
            addLocalTracks(peerid, localstreamArray[2])


        // addLocalTracks(peerid)
        // if(mediarecorder == undefined)
        // {
        //     startRecord(roomid)
        //     openBtn()
        // }
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
        await createOffer(peerid, userid)
    }
})

// 1
socket.on('webrtc_answer', (event) => {
    if(isconnectcreator)
    {
        var peerid = event['peerid']
        console.log('Socket event callback: webrtc_answer from',event.From,'to',event.To)
        rtcpeerconnection[peerid].setRemoteDescription(event['sdp'])
    }
    if(lastconnect == true)
    {
        isconnectcreator = false
        lastconnect = undefined
    }
    else if(lastconnect == false)
    {
        console.log("still remained")
    }
    
})
socket.on("upload_accept", ()=>{
    console.log("data updated!")
})
socket.on('webrtc_ice_candidate', async (event) => {
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


socket.on('transfer_complete', async (event) => {
    // mode = 0
    oper = event.oper
    localstreamArray[oper] = undefined;
    chunksArray[oper] = []
    videocomponentArray[oper].srcObject = undefined
    datestringArray[oper] = undefined
    mediarecorderArray[oper] = undefined
    console.log('transfer record complete!');
})

socket.io.on('reconnect_attempt', () =>{
    console.log("reconnecting")
})

socket.on('get_killed', ()=>{
    socket.close()
    alert("您已经掉线, 请重新连接!")
    window.location.href = "/timeout"//location.protocol +"://" + location.host + 

})

// -------------------------set logic function-------------------------------

// this function into room and send room id
async function joinRoom(room) {
    // get user local camera streams
    inroom = true;
    // await setLocalStream(mediaconstraints)
    roomid = room
    console.log("roomURL: ",location.href.split('?')[0]+'?mode='+mode+"&room="+roomid)
    socket.emit('join', room, 0, userid, username)
    showVideoConference()
}


// this function to leave room 
async function leaveRoom(room,client){
    if(inroom == false)
        return
    for(var i = 0; i < 3; i++)
        if(localstreamArray[i] != undefined)
        {
            await stopShareStream(i, '1')
        }
    // await stopRecord(room)
    await socket.emit('leave', {room:room,client:client,userid:userid,username:username,teacher_killed: 0})
    leaveVideoConference({'From':client,'To':'all'})
    return true
    // alert('video coference closed, if you need new coversation, plz enter new room number');
    // alert('WARNING :plz wait for the transfer to complete before closing this page!!');
}


// // this function to start record, 不再使用
// function startRecord(room){
//     // recoder stream
//     mediarecorder = new MediaRecorder(localstream)
//     mediarecorder2 = new MediaRecorder(sharestream)
//     // set stream mode (video or audio) 
//     if(mode == 3)
//     {
//         mediarecorder.mimeType = 'video/webm; codecs=h264';
//         mediarecorder2.mimeType = 'video/webm; codecs=h264';
//         // mediarecorder.audioChannels = 2;
//         console.log("recorder started");
//     }
//     else
//     {
//         console.log('can\'t recorde, plz check your mode')
//     }
//     socket.emit('record_time',{roomid:room,clientid:clientid,mode:'start',userid:userid,username:username})

//     //单位是ms
//     mediarecorder.start(3 * 1000);
//     // event function
//     mediarecorder.ondataavailable = function(e) {
//         chunks.push(e.data);
//         socket.emit('upload_blob',{data:chunks.shift(),roomid:room,clientid:clientid,mode:1,userid:userid,username:username});
//         console.log('upload record !!');
//     }

//     mediarecorder2.start(3 * 1000);
//     // event function
//     mediarecorder2.ondataavailable = function(e) {
//         chunks2.push(e.data);
//         socket.emit('upload_blob',{data:chunks2.shift(),roomid:room,clientid:clientid,mode:1 + 2,userid:userid,username:username});
//         console.log('upload record_screen !!');
//     }
// }


// // this function to stop record
// async function stopRecord(room)
// {
//     if(mediarecorder != undefined)
//     {
//         mediarecorder.stop()
//         await socket.emit('record_time',{roomid:room,clientid:clientid,mode:'stop',userid:userid,username:username})
//         console.log("recorder stopped");
//         var atlast = chunks.length
//         console.log("there are",atlast,"data need upload")
//         if(atlast != 0)
//         {
//             for (let i = 0; i < atlast; i++) {
//                 if(i == atlast-1)
//                 {
//                     await socket.emit('upload_blob',{data:chunks[i],roomid:room,clientid:clientid,mode:0,userid:userid,username:username})
//                 }
//                 else
//                 {
//                     await socket.emit('upload_blob',{data:chunks[i],roomid:room,clientid:clientid,mode:1,userid:userid,username:username})
//                 }
//             }
//         }
//         else
//         {
//             await socket.emit('upload_blob',{data:[0],roomid:room,clientid:clientid,mode:0,userid:userid,username:username})
//         }
//     }
//     if(mediarecorder2 != undefined)
//     {
//         mediarecorder2.stop()
//         await socket.emit('record_time',{roomid:room,clientid:clientid,mode:'stop',userid:userid,username:username})
//         console.log("recorder stopped");
//         var atlast = chunks2.length
//         console.log("there are",atlast,"data need upload")
//         if(atlast != 0)
//         {
//             for (let i = 0; i < atlast; i++) {
//                 if(i == atlast-1)
//                 {
//                     await socket.emit('upload_blob',{data:chunks2[i],roomid:room,clientid:clientid,mode:0 + 2,userid:userid,username:username})
//                 }
//                 else
//                 {
//                     await socket.emit('upload_blob',{data:chunks2[i],roomid:room,clientid:clientid,mode:1 + 2,userid:userid,username:username})
//                 }
//             }
//         }
//         else
//         {
//             await socket.emit('upload_blob',{data:[0],roomid:room,clientid:clientid,mode:0 + 2,userid:userid,username:username})
//         }
//     }
//     return true
// }

function getCurrentDate() 
{
    var now = new Date();
    var year = now.getFullYear();
    var month = now.getMonth();
    var date = now.getDate();
    var day = now.getDay();
    var hour = now.getHours();
    var minu = now.getMinutes();
    var sec = now.getSeconds();
    month = month + 1;
    if (month < 10) month = "0" + month;
    if (date < 10) date = "0" + date;
    if (hour < 10) hour = "0" + hour;
    if (minu < 10) minu = "0" + minu;
    if (sec < 10) sec = "0" + sec;
    var time = "";
    time = year + "-" + month + "-" + date + "-" + hour + "-" + minu + "-" + sec;
    return time;
}

//TOTAL start----------------------------------------
async function startShareStream(mediaconstraints, oper, room){
    if(localstreamArray[oper] != undefined)
        return false;
    var displayconstraints =  mediaconstraints
    try 
    {
        if(oper == 0)
            localstreamArray[oper] = await navigator.mediaDevices.getDisplayMedia(displayconstraints)
        else 
            localstreamArray[oper] = await navigator.mediaDevices.getUserMedia(displayconstraints)
        videocomponentArray[oper].srcObject = localstreamArray[oper]
        console.log(localstreamArray[oper])
        trclen = Object.keys(rtcpeerconnection).length
        if(trclen != 0)
        {
            for (var i = 0; i < trclen; i++) 
            {
                addLocalTracks(Object.keys(rtcpeerconnection)[i], localstreamArray[oper])
                await createOffer(Object.keys(rtcpeerconnection)[i], userid)
            }
        }
    } 
    catch (error) 
    {
        console.error('Could not get user device!', error)
        return false
    }
    mediarecorderArray[oper] = new MediaRecorder(localstreamArray[oper])
    mediarecorderArray[oper].mimeType = 'video/webm; codecs=h264';
    mediarecorderArray[oper].start(3 * 1000);
    chunksArray[oper] = []
    datestringArray[oper] = getCurrentDate()
    // event function
    mediarecorderArray[oper].ondataavailable = function(e) {
        chunksArray[oper].push(e.data);
        socket.emit('upload_blob',{data:chunksArray[oper].shift(),roomid:room,clientid:clientid,mode:1,userid:userid,username:username,oper:oper, date:datestringArray[oper]});
        console.log('upload record !!');
    }
    return true
}


// stop sharescreen function
async function stopShareStream(oper, room){
    if(localstreamArray[oper] == undefined)
        return;

    mediarecorderArray[oper].stop()
    // await socket.emit('record_time',{roomid:room,clientid:clientid,mode:'stop',userid:userid,username:username})
    console.log("recorder stopped");
    var atlast = chunksArray[oper].length
    console.log("there are",atlast,"data need upload")
    if(atlast != 0)
    {
        for (let i = 0; i < atlast; i++) {
            if(i == atlast-1)
            {
                await socket.emit('upload_blob',{data:chunksArray[oper][i],roomid:room,clientid:clientid,mode:0,userid:userid,username:username,oper:oper, date:datestringArray[oper]})
            }
            else
            {
                await socket.emit('upload_blob',{data:chunksArray[oper][i],roomid:room,clientid:clientid,mode:1,userid:userid,username:username,oper:oper, date:datestringArray[oper]})
            }
        }
    }
    else
    {
        await socket.emit('upload_blob',{data:[0],roomid:room,clientid:clientid,mode:0,userid:userid,username:username,oper:oper, date:datestringArray[oper]})
    }
    trclen = Object.keys(rtcpeerconnection).length
    
    if(trclen != 0)
    {
        for (var i = 0; i < trclen; i++) 
        {
            var peerid = Object.keys(rtcpeerconnection)[i]
            var senderlen = rtcpeerconnection[Object.keys(rtcpeerconnection)[i]].getSenders().length
            for(var j = 0; j < senderlen; j++)
            {
                // var changed = false;
                var tmpsender = rtcpeerconnection[peerid].getSenders()[j]
                if (tmpsender.track == localstreamArray[oper].getTracks()[0])
                {
                    console.log("find to delete")
                    rtcpeerconnection[peerid].removeTrack(tmpsender)
                    socket.emit("track_delete", {
                        peerid:peerid,
                        From:peerid.split(':')[1],
                        To:peerid.split(':')[0],
                        userid:userid,
                        username:username,
                        streamid:localstreamArray[oper].id
                    })
                }
                // if(changed)
                    // await createOffer(Object.keys(rtcpeerconnection)[i], userid)
            }
            
        }
    }
    localstreamArray[oper].getTracks().forEach(function(screentrack){
        // if(sender.track.id == screentrack.id)
            screentrack.stop();
    })
    
}



//TOTAL end-------------------------------------------






// this function cancle video display none if into room and get local camera stream
function showVideoConference() {
    roomselectioncontainer.style = 'display: none'
    videochatcontainer.style = 'display: block'
    disconnectbtn.disabled = false;
    disconnectbtn.innerHTML = '断开连接';
    openBtn()
}


// leave video conference
function leaveVideoConference(event) {
    // hide video div and show choose page
    roomselectioncontainer.style = 'display: block'
    videochatcontainer.style = 'display: none'
    // if share screem not stop ,clear variable and stop it.
    // for(var i = 0; i < 3; i++)
    //     stopShareStream(i, '1')
    // stop localstream 
    // trclen = Object.keys(rtcpeerconnection).length
    // if(trclen != 0)
    // {
    //     for (var i = 0; i < trclen; i++) 
    //     {
    //         rtcpeerconnection[Object.keys(rtcpeerconnection)[0]].getSenders().forEach(function(sender) {
    //             sender.track.stop();
    //         });
    //         rtcpeerconnection[Object.keys(rtcpeerconnection)[0]].close();
    //     }
    // }
    // // stop track
    // a = localstream.getTracks().length
    // if(localstream.getTracks().length != 0)
    // {
    //     for(i=0;i<a;i++)
    //     {
    //         localstream.getTracks()[0].stop()
    //     }
    // }
    // close button
    closeBtn()
    // reset const
    senders = [];
    // reset variable
    isconnectcreator = undefined
    mediaconstraints = undefined
    // localstream,remotestream,isconnectcreator,mediaconstraints,isconnectcreator,roomid = undefined,undefined,undefined,undefined,undefined,undefined
    c = 0
    return true
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




// add local stream to webrtc track
function addLocalTracks(peerid, streamobject)
{
    var tmpstream = streamobject
    tmpstream.getTracks().forEach(
        track => {
            console.log(track)
            senders.push(rtcpeerconnection[peerid].addTrack(track, tmpstream))
        }
    )
    // sharestream.getTracks().forEach(
    //     track => {
    //         console.log(track)
    //         senders.push(rtcpeerconnection[peerid].addTrack(track, sharestream))
    //     }
    // )
}



// 1
async function createOffer(peerid, user_id) {
    // var sessionDescription
    isconnectcreator = true
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
        To:peerid.split(':')[0],
        userid:user_id,
        username:username
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
            To:peerid.split(':')[0],
            userid:userid,
            username:username
        })
    }
}

// open button
function openBtn(){
    sharecamera.disabled = false;
    sharecamera.innerHTML = '开始录制镜头';
    sharescreen.disabled = false;
    sharescreen.innerHTML = '开始录制屏幕'
    sharevideo.disabled = false;
    sharevideo.innerHTML = '开始录制视频+音频'
}


// close button
function closeBtn(){
    connectbtn.disabled = false;
    sharecamera.disabled = true;
    sharecamera.innerHTML = '开始录制镜头';
    sharescreen.disabled = true;
    sharescreen.innerHTML = '开始录制屏幕'
    sharevideo.disabled = true;
    sharevideo.innerHTML = '开始录制视频+音频'
    var bt = document.getElementsByClassName('remote-video');
    slen = Object.keys(bt).length
    for (i = 0; i < slen-1; i++) 
  for (i = 0; i < slen-1; i++) 
    for (i = 0; i < slen-1; i++) 
    {
        bt[1].remove()
    }
};