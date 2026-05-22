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

    # 数据库验证管理员登录
    def admin_login_from_db(self, username, password):
        sql = "SELECT * FROM administer WHERE user_name=%s AND password=%s"
        self.cursor.execute(sql, (username, password))
        res = self.cursor.fetchone()
        return res is not None

    # 日志记录工具
    def write_log(self, msg):
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        with open("library_log.txt", "a", encoding="utf-8") as f:
            f.write(f"[{now}] {msg}\n")

    # 1. 添加图书信息
    def add_library(self,book_id,name,author,leibie):
        try:
            sql_lib = "INSERT INTO book(book_id,name,author,leibie) VALUES(%s,%s,%s,%s)"
            self.cursor.execute(sql_lib, (book_id,name,author,leibie))

            self.conn.commit()
            print("图书信息添加成功")
            self.write_log(f"新增图书：书籍编号{book_id} 书名{name} 作家{author} 类别{leibie} 状态【可借阅】")
        except Exception as e:
            self.conn.rollback()
            print("添加失败！书本重复或数据格式错误")

    # 2. 查看所有图书
    def show_all_library(self):
        sql = "SELECT * from book"
        self.cursor.execute(sql)
        res = self.cursor.fetchall()
        if not res:
            print("暂无图书数据！")
            return
        print("\n========== 图书完整信息 ==========")
        for item in res:
            print(f"书籍编号：{item['book_id']} | 书名：{item['name']} | 作者：{item['author']} | 类别：{item['leibie']} | 状态：{item['zhuangtai']}")

    # 3. 按图书编号精准查询图书信息
    def search_score_by_id(self, book_id):
        sql = "SELECT * FROM book WHERE book_id = %s"
        self.cursor.execute(sql, (book_id,))  # 修复：参数必须为元组
        res = self.cursor.fetchone()
        if res:
            print("\n========== 图书书籍详情 ==========")
            print(f"书籍编号：{res['book_id']}")
            print(f"书名：{res['name']}")
            print(f"作者：{res['author']}")
            print(f"类别：{res['leibie']}")
            print(f"状态：{res['zhuangtai']}")
        else:
            print("未查询到该图书信息！")

    # 4. 修改图书信息（只改书名、作者、类别，不改状态）
    def update_book_info(self,book_id,name,author,leibie):
        try:
            sql = "UPDATE book SET name=%s, author=%s,leibie=%s WHERE book_id=%s"
            self.cursor.execute(sql, (name, author, leibie, book_id))
            self.conn.commit()
            if self.cursor.rowcount > 0:
                print("图书基础信息修改成功")
                self.write_log(f"修改图书基础信息：书籍编号{book_id}")
            else:
                print("未找到该书")
        except:
            self.conn.rollback()
            print("修改失败")

    # 5. 删除图书信息
    def delete_book(self, book_id):
        try:
            confirm = input(f"确定删除书籍编号 {book_id} 吗？(y/n)")
            if confirm.lower() != "y":
                print("已取消操作")
                return
            sql = "DELETE FROM book WHERE book_id=%s"
            self.cursor.execute(sql, (book_id,)) # 修复：参数必须为元组
            self.conn.commit()
            if self.cursor.rowcount > 0:
                print("书籍信息已全部删除")
                self.write_log(f"删除图书数据：书籍编号{book_id}")
            else:
                print("未找到该图书")
        except:
            self.conn.rollback()
            print("删除失败")

    #6.借阅图书（适配中文状态）
    def borrow_book(self, book_id):
        try:
            sql_check = "SELECT zhuangtai FROM book WHERE book_id=%s"
            self.cursor.execute(sql_check, (book_id,))
            book = self.cursor.fetchone()
            if not book:
                print("未找到该书籍！")
                return
            status = book['zhuangtai']
            if status == "已借出":
                print("该书已被借出，无法借阅！")
                return
            sql_update = "UPDATE book SET zhuangtai=%s WHERE book_id=%s"
            self.cursor.execute(sql_update, ("已借出", book_id))
            self.conn.commit()
            print("图书借阅成功！")
            self.write_log(f"借阅：书籍编号{book_id}")
        except Exception as e:
            self.conn.rollback()
            print("借阅失败：", e)

    #7.归还图书（适配中文状态）
    def return_book(self, book_id):
        try:
            sql_check = "SELECT zhuangtai FROM book WHERE book_id=%s"
            self.cursor.execute(sql_check, (book_id,))
            book = self.cursor.fetchone()
            if not book:
                print("未找到该书籍！")
                return
            status = book['zhuangtai']
            if status == "可借阅":
                print("该书未借出，无需归还！")
                return
            sql_update = "UPDATE book SET zhuangtai=%s WHERE book_id=%s"
            self.cursor.execute(sql_update, ("可借阅", book_id))
            self.conn.commit()
            print("图书归还成功！")
            self.write_log(f"归还：书籍编号{book_id}")
        except Exception as e:
            self.conn.rollback()
            print("归还失败：", e)

    # 关闭数据库连接
    def close(self):
        self.cursor.close()
        self.conn.close()
        print("✅ 数据库连接已关闭")

# 主菜单函数
def main():
    sm = libraryManager()
    if not sm.conn:
        return

    print("\n============ 管理员登录 ============")
    while True:
        username = input("请输入管理员账号：")
        password = input("请输入管理员密码：")
        if sm.admin_login_from_db(username, password):
            print("登录成功，进入系统")
            break
        else:
            print("账号或密码错误，请重新输入\n")
    while True:
        print("\n======= 图书管理系统=======")
        print("1. 添加书籍")
        print("2. 查看所有图书完整信息")
        print("3. 按书籍编号查询书籍信息")
        print("4. 修改图书信息")
        print("5. 删除图书")
        print('6. 借阅图书')
        print('7. 归还图书')
        print("0. 退出系统")
        print("==========================================")

        choice = input("请输入功能编号：")
        if choice == "1":
            book_id = input("请输入图书编号：")
            name = input("请输入书名：")
            author = input("请输入作者：")
            leibie = input("请输入书籍类别：")

            sm.add_library(book_id,name,author,leibie)

        elif choice == "2":
            sm.show_all_library()

        elif choice == "3":
            sid = input("请输入查询书籍编号：")
            sm.search_score_by_id(sid)

        elif choice == "4":
            book_id = input("请输入要修改的书籍编号：")
            name = input("请输入新书名：")
            author = input("请输入新作者：")
            leibie = input("请输入新类别：")
            sm.update_book_info(book_id,name,author,leibie)

        elif choice == "5":
            book_id = input("请输入要删除的书籍号：")
            sm.delete_book(book_id)
        elif choice == "6":
            book_id = input("请输入想借阅的书籍编号：")
            sm.borrow_book(book_id)
        elif choice == "7":
            book_id = input("请输入想归还的书籍编号：")
            sm.return_book(book_id)
        elif choice == "0":
            sm.close()
            print("系统退出成功，再见！")
            break
        else:
            print("输入无效，请输入0-7的数字！")

if __name__ == "__main__":
    main()