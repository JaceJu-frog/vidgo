# video/apps.py
from django.apps import AppConfig
import threading, time, random
from django.db import connection
import os

class VideoConfig(AppConfig):
    name = "video"

    def ready(self):
        if getattr(self, "_worker_started", False):
            return

        from .tasks import process_next_task,process_download_task,process_export_task  # 延迟导入防止循环

        def _subtitle_worker():
            while True:
                try:
                    connection.close_if_unusable_or_obsolete()
                    process_next_task()
                    time.sleep(1 + random.random())  # 随机抖动
                except Exception as e:
                    print("Task worker error:", e)
                    time.sleep(5)
        def _download_worker():
            while True:
                try:
                    connection.close_if_unusable_or_obsolete()
                    process_download_task()
                    time.sleep(1 + random.random())  # 随机抖动
                except Exception as e:
                    print("Task worker error:", e)
                    time.sleep(5)
        def _export_worker():
            while True:
                try:
                    connection.close_if_unusable_or_obsolete()
                    process_export_task()
                    time.sleep(1 + random.random())  # 随机抖动
                except Exception as e:
                    print("Export worker error:", e)
                    time.sleep(5)

        t1 = threading.Thread(target=_subtitle_worker, daemon=True)
        t2 = threading.Thread(target=_download_worker, daemon=True)
        t3 = threading.Thread(target=_export_worker, daemon=True)
        t1.start(); t2.start(); t3.start()
        self._worker_started = True
