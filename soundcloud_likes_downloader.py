#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import os
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

INPUT_FILE = "links.txt"
OUTPUT_FILE = "filtered_links.txt"
LIKES_URL = "https://soundcloud.com/g_t_w_y/likes"
DOWNLOAD_DIR = "downloads"

EXCLUDE_KEYWORDS = [
    "mix", "set", "podcast", "dj", "hour", "live", "sessions",
    "/sets/", "/likes/", "/reposts/", "playlist", "comments", "followers",
    "following", "/tags/"
]

stop_download = False


def run_downloader(log_callback, update_stats_callback, update_progress_callback, update_errors_callback, update_chart_callback):
    global stop_download
    stop_download = False

    # Создаем папку downloads, если её нет
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
        log_callback(f"Создана папка {DOWNLOAD_DIR} для загрузки треков")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")

    log_callback("Запуск браузера и переход на страницу лайков...")
    driver = webdriver.Chrome(options=options)
    driver.get(LIKES_URL)
    time.sleep(5)

    log_callback("Прокрутка страницы для загрузки всех лайков...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(30):
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    log_callback("Сбор ссылок на треки...")
    a_tags = driver.find_elements(By.XPATH, "//a[contains(@href, '/')]")
    track_links = set()
    for tag in a_tags:
        href = tag.get_attribute("href")
        if href and "soundcloud.com" in href:
            parts = href.split("/")
            if len(parts) >= 5 and parts[3] != "you":
                track_links.add(href)

    driver.quit()

    with open(INPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(track_links)))

    log_callback(f"Найдено {len(track_links)} ссылок. Сохранено в {INPUT_FILE}")

    filtered = []
    for link in track_links:
        lower_link = link.lower()
        if any(keyword in lower_link for keyword in EXCLUDE_KEYWORDS):
            log_callback(f"Исключено: {link}")
            continue
        filtered.append(link)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(filtered)))

    total = len(filtered)
    update_stats_callback(total, 0)
    percent = (total / len(track_links)) * 100 if track_links else 0
    log_callback(f"\n📊 Статистика:\nВсего треков: {len(track_links)}\nПрошли фильтр: {total} ({percent:.1f}%)")

    log_callback("\nНачинаю скачивание треков...")
    downloaded = 0
    failed = []
    start_time = time.time()
    progress_data = []

    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        links = f.readlines()
        for idx, link in enumerate(links):
            if stop_download:
                log_callback("⛔️ Загрузка остановлена пользователем.")
                break

            link = link.strip()
            if not link:
                continue
            log_callback(f"\n🎧 Скачивание: {link}")
            try:
                result = subprocess.run(["scdl", "-l", link, "-c", "--onlymp3", "-p", DOWNLOAD_DIR], capture_output=True, text=True, encoding="utf-8", errors="replace")
                if result.returncode != 0:
                    log_callback(result.stderr)
                    raise subprocess.CalledProcessError(result.returncode, result.args, output=result.stdout, stderr=result.stderr)
                downloaded += 1
                elapsed = time.time() - start_time
                speed = downloaded / elapsed * 60 if elapsed else 0
                update_stats_callback(total, downloaded)
                update_progress_callback(idx + 1, total, speed)
                progress_data.append(downloaded)
                update_chart_callback(progress_data)
            except Exception as e:
                failed.append(link)
                update_errors_callback(len(failed))
                log_callback(f"❌ Не удалось скачать: {link} — {e}")

    if failed:
        with open("failed_links.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(failed))
        log_callback(f"\n⚠️ Не удалось скачать {len(failed)} треков. Список сохранён в failed_links.txt")


def start_gui():
    root = tk.Tk()
    root.title("🎵 SoundCloud Likes Downloader")
    root.geometry("1000x850")
    style = ttk.Style()
    root.tk_setPalette(background="#121212", foreground="#e0e0e0")
    style.theme_use("clam")
    style.configure("TButton", font=("Segoe UI", 10), padding=10, background="#2c2c2c", foreground="#ffffff")
    style.configure("TLabel", font=("Segoe UI", 10), background="#121212", foreground="#e0e0e0")
    style.configure("TFrame", background="#121212")
    style.map("TButton", background=[("active", "#444444")])

    main_frame = ttk.Frame(root, padding=10)
    main_frame.pack(fill=tk.BOTH, expand=True)

    text_box = tk.Text(main_frame, height=20, wrap=tk.WORD, bg="#1e1e1e", fg="#e0e0e0", insertbackground="#ffffff", font=("Consolas", 10), relief=tk.FLAT)
    text_box.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    stats_label = ttk.Label(main_frame, text="📦 Отфильтровано: 0 | 📥 Загружено: 0 | ❌ Ошибок: 0")
    stats_label.pack(anchor=tk.W, pady=2)

    progress_label = ttk.Label(main_frame, text="🔄 Прогресс: 0/0 | 🚀 Скорость: 0.00 треков/мин")
    progress_label.pack(anchor=tk.W, pady=2)

    fig, ax = plt.subplots(figsize=(6, 3))
    fig.patch.set_facecolor("#121212")
    ax.set_facecolor("#1e1e1e")
    chart_canvas = FigureCanvasTkAgg(fig, master=main_frame)
    chart_widget = chart_canvas.get_tk_widget()
    chart_widget.pack(pady=10, fill=tk.BOTH, expand=True)

    def log_callback(message):
        text_box.insert(tk.END, message + "\n")
        text_box.see(tk.END)

    def update_stats(total, downloaded):
        stats_label.config(text=f"📦 Отфильтровано: {total} | 📥 Загружено: {downloaded} | ❌ Ошибок: 0")

    def update_progress(current, total, speed):
        progress_label.config(text=f"🔄 Прогресс: {current}/{total} | 🚀 Скорость: {speed:.2f} треков/мин")

    def update_errors(error_count):
        current = stats_label.cget("text")
        parts = current.split("|")
        if len(parts) == 3:
            stats_label.config(text=f"{parts[0].strip()} | {parts[1].strip()} | ❌ Ошибок: {error_count}")

    def update_chart(progress_data):
        ax.clear()
        ax.plot(progress_data, marker='o', linestyle='-', linewidth=2, color="#03dac6")
        ax.set_title("📈 Прогресс загрузки", fontsize=12, color="#ffffff")
        ax.set_xlabel("Итерация", color="#ffffff")
        ax.set_ylabel("Скачано", color="#ffffff")
        ax.tick_params(colors="#ffffff")
        ax.grid(True, color="#444444")
        chart_canvas.draw()

    def on_start():
        text_box.delete("1.0", tk.END)
        threading.Thread(target=run_downloader, args=(log_callback, update_stats, update_progress, update_errors, update_chart), daemon=True).start()

    def on_stop():
        global stop_download
        stop_download = True

    buttons_frame = ttk.Frame(main_frame)
    buttons_frame.pack(pady=10)

    start_button = ttk.Button(buttons_frame, text="▶ Начать загрузку", command=on_start)
    start_button.pack(side=tk.LEFT, padx=5)

    stop_button = ttk.Button(buttons_frame, text="⛔ Стоп", command=on_stop)
    stop_button.pack(side=tk.LEFT, padx=5)

    root.mainloop()


if __name__ == "__main__":
    start_gui()
