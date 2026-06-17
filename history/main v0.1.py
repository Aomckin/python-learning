# 宅宅能量条系统 v0.1
# 目标：先搭出主菜单和基础结构，后续慢慢加功能


energy = 50  # 当前宅宅能量，初始值
history = [] # 历史记录

def show_status():
    """查看当前状态"""
    print("\n===== 当前状态 =====")
    print(f"宅宅能量：{energy}")
    print("====================")


def study():
    """学习模块"""
    global energy
    energy += 10
    history.append("学习 +10")
    print("\n你学习了一会儿，宅宅能量 +10")


def exercise():
    """健身模块"""
    global energy
    energy += 15
    history.append("健身 +15")
    print("\n你去健身了，宅宅能量 +15")


def watch_anime():
    """看番模块"""
    global energy
    energy -= 20
    history.append("看番 -20")
    print("\n你沉浸式看番，宅宅能量 -20")


def check_energy():
    global energy

    energy = max(0, energy)
    energy = min(100, energy)


def show_history():
    print("\n===== 行动记录 =====")

    if len(history) == 0:
        print("今天什么都还没做喵")
    else:
        for record in history:
            print(record)

    print("===================")


def show_menu():
    """显示菜单"""
    print("\n====== 宅宅能量条系统 ======")
    print("1. 查看状态")
    print("2. 学习")
    print("3. 健身")
    print("4. 看番")
    print("5. 查看行动记录")
    print("0. 退出系统")
    print("===========================")


def main():
    """程序主入口"""
    print("欢迎进入：宅宅能量条系统！")

    while True:
        show_menu()
        choice = input("请选择操作：")

        if choice == "1":
            show_status()
        elif choice == "2":
            study()
            check_energy()
        elif choice == "3":
            exercise()
            check_energy()
        elif choice == "4":
            watch_anime()
            check_energy()
        elif choice == "5":
            show_history()
        elif choice == "0":
            print("\n系统关闭。今天也辛苦了喵。")
            break
        else:
            print("\n输入无效，请重新选择。")


main()