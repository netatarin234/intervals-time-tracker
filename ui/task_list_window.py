# ui/task_list_window.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt
from typing import Any, Dict

from api_client import IntervalsAPI
from ui.time_entry_window import TimeEntryWindow

class TaskListWindow(QWidget):
    def __init__(self, api: IntervalsAPI):
        super().__init__()
        self.api = api
        self.setWindowTitle("Ввод ID задачи")
        self.resize(400, 150)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        lbl_info = QLabel("Введите localid (ID) задачи и нажмите \"Загрузить задачу\":")
        lbl_info.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(lbl_info)

        row = QHBoxLayout()
        self.input_taskid = QLineEdit()
        self.input_taskid.setPlaceholderText("Например: 126464")
        self.input_taskid.setFixedWidth(200)
        row.addWidget(self.input_taskid)

        btn_load = QPushButton("Загрузить задачу")
        btn_load.clicked.connect(self.on_load_task)
        row.addWidget(btn_load)

        main_layout.addLayout(row)
        main_layout.addStretch()

    def on_load_task(self):
        text = self.input_taskid.text().strip()
        if not text:
            QMessageBox.warning(self, "Внимание", "Пожалуйста, введите числовой ID задачи.")
            return

        try:
            localid = int(text)
        except ValueError:
            QMessageBox.warning(self, "Внимание", f"Некорректный формат ID: «{text}».\nОжидается целое число.")
            return

        # 1) Запрашиваем детали задачи по localid
        try:
            details: Dict[str, Any] = self.api.get_task_details(localid)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить детали задачи {localid}:\n{e}")
            return

        # 2) Из details берём внутренний taskid и projectid, name
        #    В ответе details = data["task"][0], и там есть “id” (internal id) и "projectid", "worktypeid" и т.д.
        try:
            internal_id = int(details.get("id"))
        except (TypeError, ValueError):
            QMessageBox.critical(
                self, "Ошибка",
                f"В ответе API не найден внутренний 'id' для задачи {localid}. Данные:\n{details}"
            )
            return

        projectid = details.get("projectid")
        if projectid is None:
            QMessageBox.critical(
                self, "Ошибка",
                f"В ответе API нет поля 'projectid' для задачи {localid}.\nДанные:\n{details}"
            )
            return

        # JSON в этом поле даёт строку, например "921833" — приведём к int
        try:
            projectid = int(projectid)
        except (TypeError, ValueError):
            QMessageBox.critical(
                self, "Ошибка",
                f"Невозможно преобразовать projectid='{details.get('projectid')}' в int."
            )
            return

        # Название таска лежит в details["name"]
        title = details.get("name") or details.get("title", "")

        # 3) Открываем окно ввода времени, передаём:
        #    - internal_taskid (для POST)
        #    - projectid
        #    - title
        #    - localid (для показа)
        self.time_window = TimeEntryWindow(
            api=self.api,
            internal_taskid=internal_id,
            projectid=projectid,
            title=title,
            localid=localid
        )
        self.time_window.show()
