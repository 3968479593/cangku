import pymysql
class DBHelper:
    def __init__(self, host='localhost', user='root', password='123456', db='school_db'):
     
        try:
            self.conn = pymysql.connect(
                host=host,
                user=user,
                password=password,
                db=db,
                charset='utf8mb4'  # 关键：支持中文
            )
            self.cursor = self.conn.cursor()
            print(" 数据库连接成功！")
        except Exception as e:
            print(f"数据库连接失败：{e}")
            self.conn = None
            self.cursor = None

    def execute(self, sql, params=None):
  
        if not self.conn or not self.cursor:
            print(" 数据库连接未建立，无法执行操作")
            return False
        
        try:
            self.cursor.execute(sql, params or ())
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print(f" 执行失败：{e}")
            return False

    def query_one(self, sql, params=None):
        """查询单条数据"""
        if not self.conn or not self.cursor:
            print(" 数据库连接未建立，无法查询")
            return None
        
        try:
            self.cursor.execute(sql, params or ())
            return self.cursor.fetchone()
        except Exception as e:
            print(f" 查询失败：{e}")
            return None

    def query_all(self, sql, params=None):
  
        if not self.conn or not self.cursor:
            print(" 数据库连接未建立，无法查询")
            return []
        
        try:
            self.cursor.execute(sql, params or ())
            return self.cursor.fetchall()
        except Exception as e:
            print(f" 查询失败：{e}")
            return []

    def close(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("数据库连接已关闭")