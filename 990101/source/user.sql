set names gbk;
drop database if exists user;
create database user;
use user;

/* ѧ����Ϣ��
   �꼶 ��������
   ѧ�� �����������ǵ�ͬһѧ�ſ���Ҫ�����Σ�
   ����
   ����
   ѧ��
   �κ�
   ��Ŀ��𣨿�����Щѧ�����������⣩
   ѧ����ݣ���ͨѧ��������Ա��Ŀǰ�涨0-5Ϊѧ����6-9Ϊ��ʦ��
   �Ƿ������¼ */
drop table if exists student;
create table student (
stu_grade char(4) not null,
stu_no char(8) not null,
stu_name char(16) not null,
stu_password char(32) not null,
stu_sex char(2) not null default '��',
stu_class_fname char(32) not null,
stu_class_sname char(16) not null,
stu_term char(11) not null,
stu_cno char(8) not null,
stu_wtype char(1) not null default '0',
stu_userlevel char(1) not null default '0',
stu_enable char(1) not null default '1',
primary key(stu_grade, stu_no)
) ENGINE=InnoDB CHARSET=gbk;


insert student values("2019", "1234567", "����", MD5("1234567"), "��", "�������ѧ�뼼��", "�ƿ�", "2021/2022/2", "10106203", "0", "0", "1");
insert student values("0000", "9999999", "���", MD5("9999999"), "��", "�����", "�����", "0000", "0000", "0", "1", "1");
insert student values("2020", "2053402", "��Ӣ�", MD5("2053402"), "��", "�������ѧ�뼼��", "�ƿ�", "2021/2022/2", "10106203", "0", "0", "1");
insert student values("2020", "2052590", "������", MD5("2052590"), "��", "�������ѧ�뼼��", "�ƿ�", "2021/2022/2", "10106203", "0", "0", "1");
insert student values("2020", "2052525", "�����", MD5("2052525"), "��", "�������ѧ�뼼��", "�ƿ�", "2021/2022/2", "10106203", "0", "0", "1");
insert student values("2020", "7654321", "����", MD5("7654321"), "��", "�������ѧ�뼼��", "�ƿ�", "2021/2022/2", "10106203", "0", "0", "1");
