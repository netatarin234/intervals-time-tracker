# api_client.py

import requests
from requests.auth import HTTPBasicAuth
from typing import Dict, Any, List

class IntervalsAPI:
    BASE_URL = "https://unifun.intervalsonline.com/api"

    def __init__(self, api_token: str):
        self.api_token = api_token
        self.auth = HTTPBasicAuth(self.api_token, "X")
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        # Автоматически получаем personid при инициализации
        self.personid = self._get_my_personid()

    def _get_my_personid(self) -> int:
        """
        GET /me/
        Возвращает int(personid). Бросает RuntimeError, если не удалось разобрать ответ.
        """
        url = f"{self.BASE_URL}/me/"
        resp = requests.get(url, auth=self.auth, headers=self.headers)
        if resp.status_code != 200:
            raise RuntimeError(f"GET /me/ вернул HTTP {resp.status_code}:\n{resp.text}")

        try:
            data = resp.json()
        except ValueError:
            raise RuntimeError(f"GET /me/ вернул не JSON:\n{resp.text}")

        if "personid" in data:
            try:
                return int(data["personid"])
            except (ValueError, TypeError):
                raise RuntimeError(f"Невозможно преобразовать data['personid']='{data['personid']}' в int")

        if "me" in data and isinstance(data["me"], list) and data["me"]:
            # fallback: если нет "personid", то берём "me"[0]["id"]
            first = data["me"][0]
            if isinstance(first, dict) and "id" in first:
                try:
                    return int(first["id"])
                except (ValueError, TypeError):
                    raise RuntimeError(f"Невозможно преобразовать me[0]['id']='{first['id']}' в int")

        raise RuntimeError(f"Не удалось найти personid в ответе /me/. Данные:\n{data}")

    def get_task_details(self, taskid: int) -> Dict[str, Any]:
        """
        GET /task/{taskid}/ 
        Возвращает словарь с деталями задачи (берёт первую запись из data['task']).
        Если формат неожидан, кидает RuntimeError.
        """
        url = f"{self.BASE_URL}/task/?localid={taskid}"
        resp = requests.get(url, auth=self.auth, headers=self.headers)
        resp.raise_for_status()

        data = resp.json()

        # Ожидаем, что data["task"] — это список с одним элементом
        if "task" in data and isinstance(data["task"], list) and len(data["task"]) > 0:
            # возвращаем «плоский» словарь с полями задачи
            return data["task"][0]

        # Если вдруг API возвращает «плоский» объект (хотя в вашем случае он этого не делает),
        # и там есть projectid напрямую — можно вернуть data:
        if "projectid" in data:
            return data

        raise RuntimeError(f"В ответе API нет поля 'task' или список пуст для задачи {taskid}. Данные:\n{data}")

    def get_worktypes_for_project(self, projectid: int) -> List[Dict[str, Any]]:
        """
        GET /projectworktype/?projectid={projectid}
        Возвращает список WorkType (каждый элемент – словарь с "worktypeid" и "name").
        """
        url = f"{self.BASE_URL}/projectworktype/?projectid={projectid}&limit=100"
        resp = requests.get(url, auth=self.auth, headers=self.headers)
        resp.raise_for_status()

        data = resp.json()
        if isinstance(data, list):
            return data
        # Если API обёрнут в ключ "projectworktype"
        if isinstance(data, dict) and "projectworktype" in data and isinstance(data["projectworktype"], list):
            return data["projectworktype"]

        raise RuntimeError(f"Неподдерживаемый формат ответа /projectworktype/?projectid={projectid}:\n{data}")

    def create_time_entry(
        self,
        taskid: int,
        worktypeid: int,
        date: str,
        hours: float,
        description: str = "",
        billable: bool = True
    ) -> Dict[str, Any]:
        """
        POST /time/
        Создаёт запись времени. Возвращает JSON новой записи.
        """
        url = f"{self.BASE_URL}/time/"
        payload = {
            "taskid":      taskid,
            "worktypeid":  worktypeid,
            "personid":    self.personid,
            "date":        date,
            "time":        hours,
            "description": description,
            "billable":    billable
        }
        resp = requests.post(url, auth=self.auth, headers=self.headers, json=payload)
        resp.raise_for_status()
        return resp.json()

    def create_task_note(self, taskid: int, note: str) -> Dict[str, Any]:
        """POST /tasknote/ to add a comment to a task."""
        url = f"{self.BASE_URL}/tasknote/"
        payload = {
            "taskid": taskid,
            "note": note,
            "public": "f",

        }
        resp = requests.post(url, auth=self.auth, headers=self.headers, json=payload)
        resp.raise_for_status()
        return resp.json()
