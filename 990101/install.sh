#!/bin/bash
set -e

echo "安装repo: epel"
rpm -Uvh --force ./source/epel-release*rpm

echo "安装python3和coturn"
dnf -y -q install python3 coturn 

echo "通过pip安装需要的包"
pip3 install -q -r ./source/requirements.txt

echo "覆盖flask的scaffold.py源码, 来满足GB18030编码的要求"
\cp ./source/scaffold.py $(pip3 show flask | grep Location | awk -F "Location: " '{printf "%s/flask/",$2}')

echo "将源码复制到/usr/bin/webrtc_Tony目录下"
if [ ! -d "/usr/bin/webrtc_Tony/" ]; then
    mkdir /usr/bin/webrtc_Tony/
fi
\cp -r ./source/code/* /usr/bin/webrtc_Tony/

echo "将config文件都复制到/etc目录下"
\cp -r ./config/* /etc


echo "将用于https和turn服务器的签名文件复制到/etc/webrtc_Tony/"
if [ ! -d "/etc/webrtc_Tony/" ]; then
    mkdir /etc/webrtc_Tony/
fi
\cp ./source/cert.crt ./source/cert.key /etc/webrtc_Tony

echo "将数据库示例文件复制到/etc/webrtc_Tony/"
\cp ./source/user.sql /etc/webrtc_Tony/

echo "将用于开机自启动的脚本复制到/usr/bin/webrtc_Tony目录下"
chmod +x ./source/flask_run.sh
\cp ./source/flask_run.sh /usr/bin/webrtc_Tony/

echo "建立日志目录"
if [ ! -d "/var/log/webrtc_Tony/" ]; then
    mkdir /var/log/webrtc_Tony/
fi

echo "将开机自启动服务复制到/etc/systemd/system, 开启开机自启"
\cp ./source/flask.service /etc/systemd/system/
systemctl daemon-reload
systemctl start flask.service
systemctl enable flask.service

echo "导入数据库信息"
mysql -u root -proot123 < /etc/webrtc_Tony/user.sql


echo "所有需要的文件都已经复制到对应位置!"
echo "用户数据库示例在/etc/webrtc_Tony/user.sql, 如有需要请自行导入数据库!"
echo "导入命令为 mysql -u root -proot123 < /etc/webrtc_Tony/user.sql"