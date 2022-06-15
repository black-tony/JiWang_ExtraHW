# ExtraHW
 JiWang ExtraHW


#### TODO_服务端
1. 将ssl的证书文件整合到本目录下



# 客户端与服务端通信方法:
使用socketIO

C接受S的信息:(C端写法)

在客户端的js文件里添加如下内容
```javascript
socket = io() //声明变量

//data和callback是两个变量名
//创建的这个function会在客户端收到Server发的事件的时候执行
socket.on('事件名', function(data, callback){
    ...
    //data的格式是{name:value}的格式
    //可以通过data['name']或者data.name的格式访问传送的内容
    //callback可以不写, 是回调函数, 大概率用不上
    //客户端收到信息后调用callback(参数), 服务端如果定义了对应的函数的话, 服务端会有对应的处理
    //callback的例子: 客户端执行callback("event received!");
    //如果服务端的对该callback的定义是print(arg), 那服务端就会输出上面的字符串



});

```

S接受C的信息:(C端写法)

在客户端的js文件里添加如下内容
```javascript
socket = io() //同上, 一个变量只需要一次这个
//格式为socket.emit('事件名', data, callback);
//例子:
socket.emit('client_event', {num1 : 114514, str1: "1919810"}, function(data){
    console.log("server received data", data);
}
//server会收到名为'client_event'的事件
//server会收到{num1 : 114514, str1: "1919810"}数据包, 
//server如果执行了callback函数, 则客户端会受到反馈, 在控制台上输出内容
```

# 部署方式
如果没有`python`和`pip`命令, 可以试一试有没有`python3`, `pip3`
```shell
pip install Flask
pip install configparser
pip install Flask-SocketIO
pip install Flask-SQLAlchemy
pip install pyOpenSSL
python init.py 
```
安装完python的库就可以直接运行`init.py`了

需要先自己生成https的签名, 用http协议webrtc好像不好使

ssl生成的两个文件位置和文件名需要固定~~(因为路径写死了)~~, 否则需要在init.py文件中改`ssl_certificate`和`ssl_certificate_key`的值

生成的.crt文件必须是`/etc/pki/tls/certs/cert.crt`

生成的.key文件必须是`/etc/pki/tls/private/cert.key`

写的html文件需要放在templates文件夹下, 可以有子文件夹, 支持由服务端在打开一个html的时候提供一些信息, 如下
```html
学号: <input type="number" name="ID" value="{{user_id}}"> <br>
```
`{{变量名}}`这种格式的变量会在flask显示html的时候填充提供的信息, 服务端使用的python函数为``render_template("index.html", user_id=user_id)

上面一行在显示的时候会将value的 `{{user_id}}`替换为python传入的`user_id`变量的值, 可以是空, 具体样式为

![这样](./photo_readme/render.png)


