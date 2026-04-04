#!/usr/bin/env python3
"""Скрипт для код-ревью через Claude Code CLI.

Использование: cat file.py | python claude_code_review.py [имя_файла]
Результат сохраняется в HTML и открывается в браузере.
"""

import json
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path

# Директория для сохранения HTML-отчётов
REPORTS_DIR = Path(__file__).parent / "reports"

# Промпт для код-ревью — роль Senior Engineer с критериями анализа
PROMPT_TEMPLATE =   """
Цель: Получить структурированную оценку качества кода от опытного инженера

Ты — Senior Software Engineer с многолетним опытом код-ревью. Тщательно
разбирай код, находи баги, предлагай улучшения и следи за качеством —
так, как это делает опытный инженер в команде. Отвечай только на русском языке.

Проанализируй код по следующим критериям:

Правила качества
1 Надежность и стабильность тестов
2 Ассерты и проверяемость результата
3 Читаемость и намерение кода
4 Хардкод и тестовые данные
5 Повторяемость и DRY
6 Архитектура тестов

Представь результат в виде списка замечаний. Для каждой проблемы покажи
рядом два блока: ❌ проблемный фрагмент и ✅ как должно быть.
Не вноси правки в исходный код. Паттерны важнее отдельных инцидентов.
Автоматизируй повторяющиеся ревью-комментарии с помощью правил линтера.
Категоризируй находки: баг, безопасность, производительность, поддерживаемость, стиль

Контекст:
   Язык/фреймворк: Python, Pytest
   Что делает код: проектирует автоматизированные api тесты

CODE:
$code
"""

# HTML-шаблон отчёта — тёмная тема в стиле GitHub, рендеринг markdown через marked.js
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Code Review — $filename</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 900px;
            margin: 40px auto;
            padding: 0 20px;
            background: #0d1117;
            color: #c9d1d9;
            line-height: 1.6;
        }
        h1, h2, h3 { color: #58a6ff; }
        h1 { border-bottom: 1px solid #30363d; padding-bottom: 12px; }
        pre {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 16px;
            overflow-x: auto;
        }
        code {
            background: #161b22;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 14px;
        }
        pre code { background: none; padding: 0; }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 16px 0;
        }
        th, td {
            border: 1px solid #30363d;
            padding: 8px 12px;
            text-align: left;
        }
        th { background: #161b22; }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: #8b949e;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="header">
        <span>$filename</span>
        <span>$date</span>
    </div>
    <div id="content"></div>
    <script>
        const md = $json_content;
        document.getElementById("content").innerHTML = marked.parse(md);
    </script>
</body>
</html>"""


def read_code_from_stdin() -> str:
    """Читает исходный код из stdin (через pipe)."""
    code = sys.stdin.read().strip()
    if not code:
        print("No code selected")
        sys.exit(0)
    return code


def run_with_spinner(prompt: str) -> subprocess.CompletedProcess:
    """Запускает Claude CLI и показывает счётчик секунд пока ждём ответ."""
    stop = threading.Event()

    def spinner():
        elapsed = 0
        while not stop.is_set():
            print(f"\rОжидаю ответ от Claude... {elapsed}с", end="", flush=True)
            time.sleep(1)
            elapsed += 1

    thread = threading.Thread(target=spinner, daemon=True)
    thread.start()

    result = subprocess.run(
        ["claude", "-p"],
        input=prompt,
        capture_output=True,
        text=True,
    )

    stop.set()
    thread.join()
    print()
    return result


def save_html_report(review_text: str, filename: str) -> Path:
    """Сохраняет результат ревью в HTML-файл с markdown-рендерингом."""
    REPORTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORTS_DIR / f"review_{filename}_{timestamp}.html"

    html = (
        HTML_TEMPLATE
        .replace("$filename", filename)
        .replace("$date", datetime.now().strftime("%d.%m.%Y %H:%M"))
        .replace("$json_content", json.dumps(review_text))
    )
    report_path.write_text(html, encoding="utf-8")
    return report_path


def main():
    """Точка входа: читает код, отправляет на ревью, сохраняет отчёт."""
    filename = sys.argv[1] if len(sys.argv) > 1 else "stdin"
    code = read_code_from_stdin()
    prompt = PROMPT_TEMPLATE.replace("$code", code)

    print("Отправляю код на ревью в Claude...")
    result = run_with_spinner(prompt)

    if result.returncode != 0:
        print(
            f"Ошибка Claude CLI (код {result.returncode}): "
            f"{result.stdout or result.stderr}",
            file=sys.stderr,
        )
        sys.exit(result.returncode)

    report = save_html_report(result.stdout, filename)
    print(f"Отчёт сохранён: {report}")
    webbrowser.open(report.as_uri())


if __name__ == "__main__":
    main()
