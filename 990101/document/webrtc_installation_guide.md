## ��װ����

[toc]

**(��ǰĿ¼Ĭ����990101/)**

### 1. ����epel�ֿ�(coturn��Ҫ��������ֿ�)

rpm�ļ���`990101/source/epel-release-8-15.el8.noarch.rpm`

```shell
rpm -Uvh --force ./source/epel-release*rpm
```

![���òֿ�](./photo_install/image-20220630211559882.png)

### 2. ��װcoturn��python3

```shell
dnf -y -q install python3 coturn 
```

![��װ](./photo_install/image-20220630213127150.png)

### 3. ʹ��pip��װ��Ҫ�İ�

```shell
pip3 install -q -r ./source/requirements.txt
```

![image-20220701160423992](./photo_install/image-20220701160423992.png)

**ע**: �˴����pip�汾����, ���ܻ����UnicodeError, ��Ҫ�Ƚ�linux���ַ�������ΪUTF-8��������pip

(������pip�޷�ִ���κΰ�װ/�����Ĳ���, ��GB18030������ʹ��`python3 -m pip install --upgrade pip`Ҳ��UnicodeError)

### 4. ����flask�Ĳ���Դ��, ������ҳ�ַ�����GB18030��Ҫ��

�޸ĺõ�scaffold.py�Ѿ�����`990101/source/scaffold.py`, ִ�еĲ�����

```shell
 \cp ./source/scaffold.py $(pip3 show flask | grep Location | awk -F "Location: " '{printf "%s/flask/",$2}')
```



Ҫ���ǵ��ļ���flask���scaffold.py, ����ͼ, ��Ҫ��345�����ҵ�λ�����encoding="GB18030", ����ʹ��Ĭ�ϱ���ΪUTF-8

![](./photo_install/scaffold.png)

``

### 5. ��webrtc��Դ�벿�ָ��Ƶ�/usr/bin/webrtc_Tony

Դ�벿�ֵ�λ����`990101/source/code`

```shell
mkdir /usr/bin/webrtc_Tony/
\cp -r ./source/code /usr/bin/webrtc_Tony/
```



### 6. ��webrtc��turnserver��config�ļ����Ƶ�/etc

����config�ļ�����`99011/config`Ŀ¼��, ����Ҫ���Ƶ�/etc/��

```shell
\cp -r ./config/* /etc
```



### 7. ������https��turn��������ǩ���ļ����Ƶ�/etc/webrtc_Tony/

��Ҫpem��ʽ��ǩ���ļ���Կ��˽Կ

�ṩ��Ĭ�ϵ�ǩ���ļ�`990101/source/cert.crt` ��`990101/source/cert.key`

```shell
mkdir /etc/webrtc_Tony/
\cp ./source/cert.crt ./source/cert.key /etc/webrtc_Tony
```



### 8. ����������־Ŀ¼

```shell
mkdir /var/log/webrtc_Tony/
```





### 9. �����ڿ����Զ������Ľű��ͷ����Ƶ���Ӧ��λ��, ���ÿ�������

```shell
chmod +x ./source/flask_run.sh
\cp ./source/flask_run.sh /usr/bin/webrtc_Tony/
\cp ./source/flask.service /etc/systemd/system/
systemctl daemon-reload
systemctl start flask.service
systemctl enable flask.service
```





������Ҫ���ļ����Ѿ����Ƶ���Ӧλ��

���ݿ�����˳�ʼ��, ���ݿ�ĵ�����ʹ���ֲ��н���

�����Ҫ�����������ݿ���Ϣ, ִ��`mysql -u root -proot123 < /etc/webrtc_Tony/user.sql` ����
