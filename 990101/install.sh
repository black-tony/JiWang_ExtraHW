#!/bin/bash
set -e

echo "��װrepo: epel"
rpm -Uvh --force ./source/epel-release*rpm

echo "��װpython3��coturn"
dnf -y -q install python3 coturn 

echo "ͨ��pip��װ��Ҫ�İ�"
pip3 install -q -r ./source/requirements.txt

echo "����flask��scaffold.pyԴ��, ������GB18030�����Ҫ��"
\cp ./source/scaffold.py $(pip3 show flask | grep Location | awk -F "Location: " '{printf "%s/flask/",$2}')

echo "��Դ�븴�Ƶ�/usr/bin/webrtc_TonyĿ¼��"
if [ ! -d "/usr/bin/webrtc_Tony/" ]; then
    mkdir /usr/bin/webrtc_Tony/
fi
\cp -r ./source/code/* /usr/bin/webrtc_Tony/

echo "��config�ļ������Ƶ�/etcĿ¼��"
\cp -r ./config/* /etc


echo "������https��turn��������ǩ���ļ����Ƶ�/etc/webrtc_Tony/"
if [ ! -d "/etc/webrtc_Tony/" ]; then
    mkdir /etc/webrtc_Tony/
fi
\cp ./source/cert.crt ./source/cert.key /etc/webrtc_Tony

echo "�����ݿ�ʾ���ļ����Ƶ�/etc/webrtc_Tony/"
\cp ./source/user.sql /etc/webrtc_Tony/

echo "�����ڿ����������Ľű����Ƶ�/usr/bin/webrtc_TonyĿ¼��"
chmod +x ./source/flask_run.sh
\cp ./source/flask_run.sh /usr/bin/webrtc_Tony/

echo "������־Ŀ¼"
if [ ! -d "/var/log/webrtc_Tony/" ]; then
    mkdir /var/log/webrtc_Tony/
fi

echo "�����������������Ƶ�/etc/systemd/system, ������������"
\cp ./source/flask.service /etc/systemd/system/
systemctl daemon-reload
systemctl start flask.service
systemctl enable flask.service

echo "�������ݿ���Ϣ"
mysql -u root -proot123 < /etc/webrtc_Tony/user.sql


echo "������Ҫ���ļ����Ѿ����Ƶ���Ӧλ��!"
echo "�û����ݿ�ʾ����/etc/webrtc_Tony/user.sql, ������Ҫ�����е������ݿ�!"
echo "��������Ϊ mysql -u root -proot123 < /etc/webrtc_Tony/user.sql"