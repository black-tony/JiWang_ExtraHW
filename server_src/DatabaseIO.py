# coding=GB18030
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Query

db = SQLAlchemy()

class Student(db.Model):
    query: Query
    __tablename__ = 'student'
    stu_grade = db.Column(db.String(4), primary_key=True, nullable=False)
    stu_no  = db.Column(db.String(8), primary_key=True, nullable=False)
    stu_name  = db.Column(db.String(16), nullable=False)
    stu_password = db.Column(db.String(32), nullable=False)
    stu_sex = db.Column(db.String(2), nullable=False, default='男')
    stu_class_fname = db.Column(db.String(32), nullable=False)
    stu_class_sname = db.Column(db.String(16), nullable=False)
    stu_term = db.Column(db.String(11), nullable=False)
    stu_cno = db.Column(db.String(8), nullable=False)
    stu_wtype = db.Column(db.String(1), nullable=False, default='0')
    stu_userlevel = db.Column(db.String(1), nullable=False, default='0')
    stu_enable = db.Column(db.String(1), nullable=False, default='1')
    
    def __init__(self, stu_grade, 
                 stu_no, stu_name, 
                 stu_password, 
                 stu_sex, 
                 stu_class_fname, 
                 stu_class_sname, 
                 stu_term, 
                 stu_cno, 
                 stu_wtype, 
                 stu_userlevel, 
                 stu_enable):
        self.stu_grade = stu_grade
        self.stu_no = stu_no
        self.stu_name = stu_name
        self.stu_password = stu_password
        self.stu_sex = stu_sex
        self.stu_class_fname = stu_class_fname
        self.stu_class_sname = stu_class_sname
        self.stu_term = stu_term
        self.stu_cno = stu_cno
        self.stu_wtype = stu_wtype
        self.stu_userlevel = stu_userlevel
        self.stu_enable = stu_enable
    def __repr__(self):
        return f"<Student {self.stu_grade}:{self.stu_no} >"
        

# print("DB_FINISH!")




'''
_DEBUG = Myconstants.DEBUG
TABLE_CONST = "employee"


class MysqlUtil(object):

    def __init__(self, databaseName=Myconstants.DATABASE_CONST, closeInst=True):
        host = Myconstants.HOST_CONST
        user = Myconstants.USER_CONST
        port = Myconstants.PORT_CONST
        password = Myconstants.PASSWORD_CONST
        database = databaseName
        self.db = pymysql.connect(host=host, port=port, user=user, password=password, db=database)
        self.cursor = self.db.cursor(cursor=pymysql.cursors.DictCursor)
        self.closeAtOnce = closeInst

    @staticmethod
    def __phraseSQL(table, fields, needNum=-1, condition="NULL"):
        sql = "SELECT "
        haveQuote = 0
        if fields:
            for i in fields:
                if haveQuote == 0:
                    haveQuote = 1
                else:
                    sql += ', '
                sql += i
        else:
            sql += '*'
        sql += " FROM " + table

        if condition != "NULL":
            sql += f' WHERE {condition}'
        if needNum > 0:
            sql += f' LIMIT {needNum}'
        sql += ';'
        if _DEBUG:
            print(sql)
        return sql

    def setCloseTime(self, closeInst=True):
        self.closeAtOnce = closeInst

    def changeDatabase(self, databaseName):
        self.db.close()
        self.cursor.close()
        host = Myconstants.HOST_CONST
        user = Myconstants.USER_CONST
        port = Myconstants.PORT_CONST
        password = Myconstants.PASSWORD_CONST
        database = databaseName
        self.db = pymysql.connect(host=host, port=port, user=user, password=password, db=database)
        self.cursor = self.db.cursor(cursor=pymysql.cursors.DictCursor)

    def insert(self, table=TABLE_CONST, fields_and_vals=None):
        if fields_and_vals is None:
            fields_and_vals = {}
        sql = "INSERT INTO " + table
        sql += '('
        haveQuote = 0
        for firstPart, secondPart in fields_and_vals.items():
            if haveQuote == 0:
                haveQuote = 1
            else:
                sql += ', '
            sql += f"{firstPart}"
        sql += ') VALUES ('
        haveQuote = 0
        for firstPart, secondPart in fields_and_vals.items():
            if haveQuote == 0:
                haveQuote = 1
            else:
                sql += ', '
            if type(secondPart) == string:
                sql += f'"{secondPart}"'
            else:
                sql += f"{secondPart}"

        sql += ');'
        if _DEBUG:
            print(sql)
        try:
            self.cursor.execute(sql)
            self.db.commit()
        except pymysql.DatabaseError:
            traceback.print_exc()
            self.db.rollback()
        finally:
            if self.closeAtOnce:
                self.db.close()

    def fetchone(self, table, condition="NULL", *fields):
        # return with list<dictionary>
        sql = self.__phraseSQL(table=table, condition=condition, fields=fields)

        result = list()
        try:
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
        except pymysql.DatabaseError:
            traceback.print_exc()
            self.db.rollback()
        finally:
            if self.closeAtOnce:
                self.db.close()
        return result

    def fetchall(self, table, condition="NULL", *fields):
        # return with list<dictionary>
        sql = self.__phraseSQL(table=table, condition=condition, fields=fields)
        results = list()
        try:
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
        except pymysql.DatabaseError:
            traceback.print_exc()
            self.db.rollback()
        finally:
            self.db.close()
        return results

    def fetchOrderedNum(self, table, needNum, condition="NULL", *fields):
        sql = self.__phraseSQL(table=table, condition=condition, fields=fields, needNum=needNum)

        result = list()
        try:
            self.cursor.execute(sql)
            result = self.cursor.fetchall()
        except pymysql.DatabaseError:
            traceback.print_exc()
            self.db.rollback()
        finally:
            if self.closeAtOnce:
                self.db.close()
        return result

    def delete(self, table, condition):
        sql = f"DELETE FROM {table} WHERE {condition}"
        if _DEBUG:
            print(sql)
        try:
            self.cursor.execute(sql)
            self.db.commit()
        except pymysql.DatabaseError:
            traceback.print_exc()
            self.db.rollback()
        finally:
            if self.closeAtOnce:
                self.db.close()

    def update(self, condition="NULL", table=TABLE_CONST, fields_and_vals=None):
        if fields_and_vals is None:
            fields_and_vals = {}
        sql = f'UPDATE {table} SET '
        haveQuote = 0
        for firstVal, secondVal in fields_and_vals.items():
            if haveQuote == 0:
                haveQuote = 1
            else:
                sql += ', '
            sql += f"{firstVal}="
            if type(secondVal) == string:
                sql += f'"{secondVal}"'
            else:
                sql += f"{secondVal}"
        if condition != "NULL":
            sql += condition
        if _DEBUG:
            print(sql)
        try:
            self.cursor.execute(sql)
            self.db.commit()
        except pymysql.DatabaseError:
            traceback.print_exc()
            self.db.rollback()
        finally:
            if self.closeAtOnce:
                self.db.close()
'''