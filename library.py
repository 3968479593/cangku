import pymysql
import time

class libraryManager:
    def __init__(self):
        try:
            self.conn = pymysql.connect(
                host="localhost",
                user="root",       
                password="123456",
                database="book_db",
                charset="utf8mb4",
                autocommit=False
            )
            self.cursor = self.conn.cursor(pymysql.cursors.DictCursor)
            print("数据库连接成功")
        except Exception as e:
            print("数据库连接失败：", e)

    # 管理员登录
    def admin_login(self, username, password):
        sql = "SELECT * FROM administer WHERE user_name=%s AND password=%s"
        self.cursor.execute(sql, (username, password))
        return self.cursor.fetchone() is not None

    # 学生登录
    def student_login(self, student_id, password):
        sql = "SELECT * FROM student WHERE student_id=%s AND password=%s"
        self.cursor.execute(sql, (student_id, password))
        return self.cursor.fetchone() is not None

    # 学生注册
    def student_register(self, student_id, password):
        try:
            sql_check = "SELECT * FROM student WHERE student_id=%s"
            self.cursor.execute(sql_check, (student_id,))
            if self.cursor.fetchone():
                print("该账号已被注册！")
                return False
            
            # 插入新学生账号
            sql = "INSERT INTO student(student_id, password) VALUES(%s, %s)"
            self.cursor.execute(sql, (student_id, password))
            self.conn.commit()
            print("注册成功，请登录！")
            self.write_log(f"新学生账号注册：{student_id}")
            return True
        except Exception as e:
            self.conn.rollback()
            print("注册失败：", e)
            return False

    # 日志
    def write_log(self, msg):
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        with open("log.txt", "a", encoding="utf-8") as f:
            f.write(f"[{now}] {msg}\n")

    # 添加图书
    def add_book(self,book_id,name,author,leibie):
        try:
            sql = "INSERT INTO book(book_id,name,author,leibie) VALUES(%s,%s,%s,%s)"
            self.cursor.execute(sql, (book_id,name,author,leibie))
            self.conn.commit()
            print("添加成功")
            self.write_log(f"管理员添加图书：{book_id}")
        except:
            self.conn.rollback()
            print("添加失败")

    # 查看所有
    def show_all(self):
        self.cursor.execute("SELECT * FROM book")
        books = self.cursor.fetchall()
        if not books:
            print("暂无图书")
            return
        print("\n===== 图书列表 =====")
        for b in books:
            print(f"编号:{b['book_id']} | 书名:{b['name']} | 作者:{b['author']} | 分类:{b['leibie']} | 状态:{b['zhuangtai']}")

    # 查询
    def search_book(self):
        print("\n===== 图书查询菜单 =====")
        print("1 按图书编号精准查询")
        print("2 按书名模糊查询")
        print("3 按分类筛选")
        print("4 按作者查询")
        choice = input("请选择查询方式：")

        if choice == "1":
            book_id = input("输入图书编号：")
            sql = "SELECT * FROM book WHERE book_id = %s"
            self.cursor.execute(sql, (book_id,))
        elif choice == "2":
            name = input("输入书名（可模糊）：")
            sql = "SELECT * FROM book WHERE name LIKE %s"
            self.cursor.execute(sql, (f"%{name}%",))
        elif choice == "3":
            leibie = input("输入图书分类：")
            sql = "SELECT * FROM book WHERE leibie = %s"
            self.cursor.execute(sql, (leibie,))
        elif choice == "4":
            author = input("输入作者名：")
            sql = "SELECT * FROM book WHERE author = %s"
            self.cursor.execute(sql, (author,))
        else:
            print("无效选项")
            return

        res = self.cursor.fetchall()
        if not res:
            print("未查询到相关图书")
            return
        print("\n===== 查询结果 =====")
        for b in res:
            print(f"编号:{b['book_id']} | 书名:{b['name']} | 作者:{b['author']} | 分类:{b['leibie']} | 状态:{b['zhuangtai']}")

    # 修改图书
    def update_book(self,book_id,name,author,leibie):
        try:
            sql = "UPDATE book SET name=%s,author=%s,leibie=%s WHERE book_id=%s"
            self.cursor.execute(sql,(name,author,leibie,book_id))
            self.conn.commit()
            print("修改成功")
        except:
            self.conn.rollback()
            print("修改失败")

    # 删除图书
    def delete_book(self,book_id):
        try:
            self.cursor.execute("DELETE FROM book WHERE book_id=%s",(book_id,))
            self.conn.commit()
            print("删除成功")
        except:
            self.conn.rollback()
            print("删除失败")

    # 借阅
    def borrow_book(self, book_id, user_id, role):
        try:
            self.cursor.execute("SELECT zhuangtai FROM book WHERE book_id=%s", (book_id,))
            book = self.cursor.fetchone()
            if not book:
                print("无此书")
                return
            if book['zhuangtai'] == "已借出":
                print("该书已借出")
                return
            self.cursor.execute("UPDATE book SET zhuangtai='已借出' WHERE book_id=%s", (book_id,))
            self.conn.commit()
            print("借阅成功")
            self.write_log(f"用户[{user_id}] ({role}) 借阅图书：{book_id}")
        except Exception as e:
            self.conn.rollback()
            print("借阅失败")

    # 归还
    def return_book(self, book_id, user_id, role):
        try:
            self.cursor.execute("SELECT zhuangtai FROM book WHERE book_id=%s", (book_id,))
            book = self.cursor.fetchone()
            if not book:
                print("无此书")
                return
            if book['zhuangtai'] == "可借阅":
                print("该书未借出")
                return
            self.cursor.execute("UPDATE book SET zhuangtai='可借阅' WHERE book_id=%s", (book_id,))
            self.conn.commit()
            print("归还成功")
            self.write_log(f"用户[{user_id}] ({role}) 归还图书：{book_id}")
        except Exception as e:
            self.conn.rollback()
            print("归还失败")

    def close(self):
        self.cursor.close()
        self.conn.close()

# ===================== 主程序 =====================
def main():
    sm = libraryManager()
    print("===== 图书管理系统 =====")
    print("1 管理员登录")
    print("2 学生登录")
    print("3 学生注册")
    choice = input("请选择：")

    is_admin = False
    login_user = ""
    role = ""

    if choice == "1":
        user = input("管理员账号：")
        pwd = input("管理员密码：")
        if sm.admin_login(user, pwd):
            print("管理员登录成功")
            is_admin = True
            login_user = user
            role = "管理员"
        else:
            print("登录失败")
            return

    elif choice == "2":
        sid = input("学生账号：")
        pwd = input("学生密码：")
        if sm.student_login(sid, pwd):
            print("学生登录成功")
            is_admin = False
            login_user = sid
            role = "学生"
        else:
            print("登录失败，请检查账号密码或先注册！")
            return

    elif choice == "3":
        sid = input("请设置学生账号：")
        pwd = input("请设置学生密码：")
        sm.student_register(sid, pwd)
        return

    else:
        print("无效输入")
        return

    # 系统菜单
    while True:
        print("\n===== 图书管理系统 =====")
        if is_admin:
            print("1 添加图书")
            print("2 查看全部")
            print("3 图书查询（高级）")
            print("4 修改图书")
            print("5 删除图书")
            print("6 借阅图书")
            print("7 归还图书")
            print("0 退出")
        else:
            print("2 查看全部图书")
            print("3 图书查询（高级）")
            print("6 借阅图书")
            print("7 归还图书")
            print("0 退出")

        op = input("请输入功能：")

        if is_admin:
            if op == "1":
                book_id = input("图书编号：")
                name = input("书名：")
                author = input("作者：")
                leibie = input("类别：")
                sm.add_book(book_id,name,author,leibie)
            elif op == "4":
                book_id = input("要修改的编号：")
                name = input("新书名：")
                author = input("新作者：")
                leibie = input("新类别：")
                sm.update_book(book_id,name,author,leibie)
            elif op == "5":
                book_id = input("要删除的编号：")
                sm.delete_book(book_id)

        if op == "2":
            sm.show_all()
        elif op == "3":
            sm.search_book()
        elif op == "6":
            book_id = input("借阅编号：")
            sm.borrow_book(book_id, login_user, role)
        elif op == "7":
            book_id = input("归还编号：")
            sm.return_book(book_id, login_user, role)
        elif op == "0":
            sm.close()
            print("退出成功")
            break

if __name__ == "__main__":
    main()