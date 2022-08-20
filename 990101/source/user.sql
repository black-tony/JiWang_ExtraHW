set names gbk;
drop database if exists user;
create database user;
use user;

/* 学生信息表
   年级 （主键）
   学号 （主键，考虑到同一学号可能要修两次）
   姓名
   密码
   学期
   课号
   题目类别（考虑有些学生单独做大题）
   学生身份（普通学生及管理员，目前规定0-5为学生，6-9为教师）
   是否允许登录 */
drop table if exists student;
create table student (
stu_grade char(4) not null,
stu_no char(8) not null,
stu_name char(16) not null,
stu_password char(32) not null,
stu_sex char(2) not null default '男',
stu_class_fname char(32) not null,
stu_class_sname char(16) not null,
stu_term char(11) not null,
stu_cno char(8) not null,
stu_wtype char(1) not null default '0',
stu_userlevel char(1) not null default '0',
stu_enable char(1) not null default '1',
primary key(stu_grade, stu_no)
) ENGINE=InnoDB CHARSET=gbk;


insert student values("2019", "1234567", "张三", MD5("1234567"), "男", "计算机科学与技术", "计科", "2021/2022/2", "10106203", "0", "0", "1");
insert student values("0000", "9999999", "监控", MD5("9999999"), "男", "计算机", "计算机", "0000", "0000", "0", "1", "1");
insert student values("2020", "2053402", "杨英颢", MD5("2053402"), "男", "计算机科学与技术", "计科", "2021/2022/2", "10106203", "0", "0", "1");
insert student values("2020", "2052590", "王万骥", MD5("2052590"), "男", "计算机科学与技术", "计科", "2021/2022/2", "10106203", "0", "0", "1");
insert student values("2020", "2052525", "胥军杰", MD5("2052525"), "男", "计算机科学与技术", "计科", "2021/2022/2", "10106203", "0", "0", "1");
insert student values("2020", "7654321", "张三", MD5("7654321"), "男", "计算机科学与技术", "计科", "2021/2022/2", "10106203", "0", "0", "1");
