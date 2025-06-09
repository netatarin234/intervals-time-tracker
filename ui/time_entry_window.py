from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QMessageBox,
    QFrame,
    QDateEdit,
    QTextEdit,
)
from PyQt5.QtCore import Qt, QDate
from typing import List, Dict, Any

class TimeEntryWindow(QWidget):
    """
    Окно для внесения записей времени.
    Принимает:
      - internal_taskid (int)  — реальный ID таска для POST /time/
      - projectid     (int)
      - title         (str)    — заголовок задачи
      - localid       (int)    — публичный номер (для показа)
    """


    def __init__(self, api, internal_taskid: int, projectid: int, title: str, localid: int):
        super().__init__()
        self.api = api
        self.internal_taskid = internal_taskid
        self.projectid = projectid
        self.title = title
        self.localid = localid

        self.setWindowTitle(f"Запись времени для задачи {self.localid}")
        self.resize(800, 600)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # --- Шапка: localid : title + выбор даты ---
        header = QHBoxLayout()
        lbl_task = QLabel(f"{self.localid} : {self.title}")
        lbl_task.setStyleSheet("font-weight: bold; font-size: 16px;")
        header.addWidget(lbl_task, stretch=1)

        # Добавляем QDateEdit
        self.date_edit = QDateEdit()
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        header.addWidget(self.date_edit, stretch=0)

        link_url = f"https://unifun.intervalsonline.com/tasks/view/{self.localid}/notes"
        lbl_link = QLabel(f'<a href="{link_url}">Открыть в браузере</a>')
        lbl_link.setOpenExternalLinks(True)
        lbl_link.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl_link.setStyleSheet("font-size: 14px;")
        header.addWidget(lbl_link, stretch=0)

        layout.addLayout(header)
        # --- Комментарий (скрывается/раскрывается по кнопке) ---
        comment_toggle_layout = QHBoxLayout()
        self.btn_comment = QPushButton("Показать комментарий")
        self.btn_comment.setCheckable(True)
        self.btn_comment.toggled.connect(self.on_toggle_comment)
        comment_toggle_layout.addWidget(self.btn_comment)
        layout.addLayout(comment_toggle_layout)

        self.comment_edit = QTextEdit()
        self.comment_edit.setPlaceholderText("Комментарий")
        self.comment_edit.setVisible(False)
        layout.addWidget(self.comment_edit)
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # --- Получаем список WorkType ---
        try:
            self.worktypes: List[Dict[str, Any]] = self.api.get_worktypes_for_project(self.projectid)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить WorkType:\n{e}")
            self.worktypes = []

        if not self.worktypes:
            QMessageBox.warning(self, "Внимание", "Список WorkType для этого проекта пуст.")

        # --- Строки для ввода: динамически добавляемые ---
        self.row_widgets = []
        self.rows_layout = QVBoxLayout()
        layout.addLayout(self.rows_layout)
        self.add_row()

        layout.addStretch()

        btn_submit = QPushButton("Submit")
        btn_submit.clicked.connect(self.on_submit)
        btn_submit.setFixedHeight(40)
        layout.addWidget(btn_submit, alignment=Qt.AlignCenter)

    def add_row(self):
        idx = len(self.row_widgets) + 1
        row_layout = QHBoxLayout()

        desc = QLineEdit()
        desc.setPlaceholderText(f"Описание (строка {idx})")
        desc.setMinimumWidth(300)
        desc.textChanged.connect(self.check_last_row_filled)
        row_layout.addWidget(desc, stretch=3)

        combo = QComboBox()
        combo.setMinimumWidth(200)
        combo.addItem("--- Тип работы ---", userData=None)
        for wt in self.worktypes:
            display_name = wt.get("worktype", "<без названия>")
            try:
                wt_id = int(wt.get("worktypeid", "0"))
            except (ValueError, TypeError):
                wt_id = 0
            combo.addItem(display_name, userData=wt_id)
        combo.currentIndexChanged.connect(self.check_last_row_filled)
        row_layout.addWidget(combo, stretch=2)

        self.rows_layout.addLayout(row_layout)
        self.row_widgets.append((desc, combo))

    def check_last_row_filled(self):
        if not self.row_widgets:
            return
        desc, combo = self.row_widgets[-1]
        if desc.text().strip() and combo.currentData():
            self.add_row()

    def on_toggle_comment(self, checked: bool):
        self.comment_edit.setVisible(checked)
        self.btn_comment.setText("Скрыть комментарий" if checked else "Показать комментарий")

    def on_submit(self):
        errors = []
        success_count = 0
        comment_added = False

        date_str = self.date_edit.date().toString("yyyy-MM-dd")

        for idx, (desc_edit, combo) in enumerate(self.row_widgets, 1):
            desc_text = desc_edit.text().strip()
            worktypeid = combo.currentData()

            if not desc_text and (worktypeid is None or worktypeid == 0):
                continue

            if not desc_text:
                errors.append(f"Строка {idx}: не задано описание.")
                continue
            if not worktypeid:
                errors.append(f"Строка {idx}: не выбран тип работы.")
                continue

            try:
                self.api.create_time_entry(
                    taskid=self.internal_taskid,
                    worktypeid=worktypeid,
                    date=date_str,
                    hours=1.0,
                    description=desc_text,
                    billable=True
                )
                success_count += 1
            except Exception as e:
                errors.append(f"Строка {idx}: ошибка при создании записи: {e}")

        comment_text = self.comment_edit.toPlainText().strip()
        if comment_text:
            try:
                self.api.create_task_note(
                    taskid=self.internal_taskid,
                    note=comment_text,
                )
                comment_added = True
            except Exception as e:
                errors.append(f"Ошибка добавления комментария: {e}")

        msg = f"Успешно создано {success_count} entr{'y' if success_count == 1 else 'ies'}."
        if comment_added:
            msg += "\nКомментарий добавлен."
        if errors:
            msg += "\nОшибки:\n" + "\n".join(errors)
            QMessageBox.warning(self, "Результат загрузки", msg)
        else:
            QMessageBox.information(self, "ОК", msg)
