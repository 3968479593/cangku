class BankAccount:
    def __init__(self,account_id,name,balance,password):
        self.account_id=account_id
        self.name=name
        self.__balance=balance
        self.__password=password
        def get_balance(self):
            return self.__balance
        def deposit(self, amount):
            if amount > 0:
                self.__balance += amount
                print(f"存款成功！存入金额：{amount}，当前余额：{self.__balance}")
            else:
                print("存款失败，金额必须大于0！")
        def withdraw(self, amount, password):
            if password!=self.__password:
                print('密码错误请重新输入')
                return
            if amount <= 0:
                print('余额不足，取款失败')
                return
            if amount >= self.__balance:
                print('取款超额，取款失败')
                return
            self.__balance-=amount
            print(f'取出{amount},余额{self.__balance}')
        def change_password(self,old,new):
            if old!=self.__password:
                print('密码错误请重新输入')
                return
            self.__password=new
            print('修改成功')
if __name__=="__main__":
    account = BankAccount("1001", "张三", 1000, "123456")
    print("当前余额：", account.get_balance())

    # 存款
    account.deposit(500)

    # 取款
    account.withdraw(300, "123456")

    # 取款
    account.withdraw(2000, "123456")

    # 取款
    account.withdraw(100, "wrongpass")

    # 修改密码
    account.change_password("123456", "654321")