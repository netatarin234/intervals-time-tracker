# main.py

import sys
from PyQt5.QtWidgets import QApplication
from api_client import IntervalsAPI
from ui.task_list_window import TaskListWindow

def main():
    # Вставьте сюда ваш API_TOKEN (строкой, ASCII: латиница+цифры)
    API_TOKEN = "TOKEN_HERE"

    # Создаём клиента API (внутри он запросит /me/ и получит personid)
    api = IntervalsAPI(API_TOKEN)

    # Запускаем Qt-приложение
    app = QApplication(sys.argv)

    # Отобразим окно с вводом ID задачи
    win = TaskListWindow(api=api)
    win.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()