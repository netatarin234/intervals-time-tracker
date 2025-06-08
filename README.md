# intervals-time-tracker
# Intervals Time Logger

**Desktop GUI** for quick, batch logging of hours into Intervals (Unifun) via API.

## ⚙️ Prerequisites

* Python 3.7+
* Intervals API Token (My Account → API Access)
* Install dependencies:

  ```bash
  pip install -r requirements.txt
  ```

## 🚀 Quick Start

1. Clone repo:

   ```bash
   git clone https://github.com/yourusername/intervals-time-tracker.git
   cd intervals-time-tracker
   ```
2. Configure **`main.py`**:

   ```python
   API_TOKEN = "YOUR_API_TOKEN"
   ```
3. Run application:

   ```bash
   python main.py
   ```
4. Workflow:

   * Enter **localid** of the task
   * Click **Load Task** to fetch details
   * Fill up to **8** rows: description, work type, hours
   * Press **Submit** to post entries to Intervals API

## 🗂️ Project Layout

```
intervals-time-tracker/
├── main.py
├── api_client.py
├── requirements.txt
└── ui/
    ├── task_list_window.py
    └── time_entry_window.py
```
