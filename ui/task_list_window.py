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

        # Храним ссылки на открытые окна, чтобы их не собирал GC
        self.time_windows = []

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        lbl_info = QLabel(
            "Введите localid (ID) задачи через запятую и нажмите \"Загрузить задачу\":"
        )
        lbl_info.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(lbl_info)

        row = QHBoxLayout()
        self.input_taskid = QLineEdit()
        self.input_taskid.setPlaceholderText("Например: 126464,126465")
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
            QMessageBox.warning(self, "Внимание", "Пожалуйста, введите ID задач через запятую.")
            return

        id_parts = [t.strip() for t in text.split(',') if t.strip()]
        if not id_parts:
            QMessageBox.warning(self, "Внимание", "Список ID пуст.")
            return

        for part in id_parts:
            try:
                localid = int(part)
            except ValueError:
                QMessageBox.warning(self, "Внимание", f"Некорректный формат ID: «{part}». Ожидается число.")
                continue

            try:
                details: Dict[str, Any] = self.api.get_task_details(localid)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось получить детали задачи {localid}:\n{e}")
                continue

            try:
                internal_id = int(details.get("id"))
            except (TypeError, ValueError):
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"В ответе API не найден внутренний 'id' для задачи {localid}. Данные:\n{details}"
                )
                continue

            projectid = details.get("projectid")
            if projectid is None:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"В ответе API нет поля 'projectid' для задачи {localid}.\nДанные:\n{details}"
                )
                continue

            try:
                projectid = int(projectid)
            except (TypeError, ValueError):
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Невозможно преобразовать projectid='{details.get('projectid')}' в int."
                )
                continue

            title = details.get("name") or details.get("title", "")

            win = TimeEntryWindow(
                api=self.api,
                internal_taskid=internal_id,
                projectid=projectid,
                title=title,
                localid=localid
            )
            win.show()
            self.time_windows.append(win)
