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
import shutil

INPUT_FILE = "links.txt"
OUTPUT_FILE = "filtered_links.txt"
DEFAULT_LIKES_URL = "https://soundcloud.com/g_t_w_y/likes"
DOWNLOAD_DIR = "downloads"

EXCLUDE_KEYWORDS = [
    "mix", "set", "podcast", "dj", "hour", "live", "sessions",
    "/sets/", "/likes/", "/reposts/", "playlist", "comments", "followers",
    "following", "/tags/"
]

stop_download = False
LIKES_URL = DEFAULT_LIKES_URL

def count_likes_links(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")

    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(5)

    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(30):
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    a_tags = driver.find_elements(By.XPATH, "//a[contains(@href, '/')]")
    track_links = set()
    for tag in a_tags:
        href = tag.get_attribute("href")
        if href and "soundcloud.com" in href:
            parts = href.split("/")
            if len(parts) >= 5 and parts[3] != "you":
                track_links.add(href)

    driver.quit()
    return len(track_links)

def run_downloader(log_callback, update_stats_callback, update_progress_callback, update_errors_callback, update_chart_callback):
    global stop_download
    stop_download = False

    if not shutil.which("scdl"):
        log_callback("❌ SCDL is not installed or not in PATH.")
        return

    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
        log_callback(f"📁 Created directory: {DOWNLOAD_DIR}")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")

    log_callback("🌐 Starting browser and navigating to likes page...")
    driver = webdriver.Chrome(options=options)
    driver.get(LIKES_URL)
    time.sleep(5)

    log_callback("🔄 Scrolling page to load all likes...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(30):
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    log_callback("🔎 Collecting track links...")
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

    log_callback(f"✅ Found {len(track_links)} links. Saved to {INPUT_FILE}")

    filtered = []
    for link in track_links:
        lower_link = link.lower()
        if any(keyword in lower_link for keyword in EXCLUDE_KEYWORDS):
            log_callback(f"⛔ Excluded: {link}")
            continue
        filtered.append(link)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(filtered)))

    total = len(filtered)
    update_stats_callback(total, 0)
    percent = (total / len(track_links)) * 100 if track_links else 0
    log_callback(f"\n📊 Statistics:\nTotal tracks: {len(track_links)}\nPassed filter: {total} ({percent:.1f}%)")

    log_callback("⬇️ Starting downloads...")
    downloaded = 0
    failed = []
    start_time = time.time()
    progress_data = []

    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        links = f.readlines()
        for idx, link in enumerate(links):
            if stop_download:
                log_callback("🛑 Download stopped by user.")
                break

            link = link.strip()
            if not link:
                continue
            log_callback(f"🎧 Downloading: {link}")
            try:
                result = subprocess.run([
                    "scdl", "-l", link, "-c", "--onlymp3", "--path", DOWNLOAD_DIR
                ], capture_output=True, text=True, encoding="utf-8", errors="replace")

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
                log_callback(f"❌ Failed to download: {link} — {e}")

    if failed:
        with open("failed_links.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(failed))
        log_callback(f"⚠️ Failed to download {len(failed)} tracks. List saved to failed_links.txt")

# Добавим GUI и точку входа

def start_gui():
    global LIKES_URL

    root = tk.Tk()
    root.title("🎵 SoundCloud Likes Downloader")
    root.geometry("1000x900")
    style = ttk.Style()
    root.tk_setPalette(background="#121212", foreground="#e0e0e0")
    style.theme_use("clam")
    style.configure("TButton", font=("Segoe UI", 10), padding=10, background="#2c2c2c", foreground="#ffffff")
    style.configure("TLabel", font=("Segoe UI", 10), background="#121212", foreground="#e0e0e0")
    style.configure("TFrame", background="#121212")
    style.map("TButton", background=[("active", "#444444")])

    main_frame = ttk.Frame(root, padding=10)
    main_frame.pack(fill=tk.BOTH, expand=True)

    url_entry_label = ttk.Label(main_frame, text="🔗 Likes Page URL:")
    url_entry_label.pack(anchor=tk.W, padx=5, pady=(5, 0))

    url_entry = tk.Entry(main_frame, bg="#1e1e1e", fg="#e0e0e0", insertbackground="#ffffff", font=("Consolas", 10))
    url_entry.insert(0, DEFAULT_LIKES_URL)
    url_entry.pack(fill=tk.X, padx=5, pady=5)

    text_box = tk.Text(main_frame, height=20, wrap=tk.WORD, bg="#1e1e1e", fg="#e0e0e0", 
                      insertbackground="#ffffff", font=("Consolas", 10), relief=tk.FLAT)
    text_box.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    stats_label = ttk.Label(main_frame, text="📦 Filtered: 0 | 📥 Downloaded: 0 | ❌ Errors: 0")
    stats_label.pack(anchor=tk.W, pady=2)

    progress_label = ttk.Label(main_frame, text="🔄 Progress: 0/0 | 🚀 Speed: 0.00 tracks/min")
    progress_label.pack(anchor=tk.W, pady=2)

    progress_bar = ttk.Progressbar(main_frame, orient="horizontal", mode="determinate")
    progress_bar.pack(fill=tk.X, padx=5, pady=(0, 10))

    fig, ax = plt.subplots(figsize=(6, 3))
    fig.patch.set_facecolor("#121212")
    ax.set_facecolor("#1e1e1e")
    chart_canvas = FigureCanvasTkAgg(fig, master=main_frame)
    chart_widget = chart_canvas.get_tk_widget()
    chart_widget.pack(pady=10, fill=tk.BOTH, expand=True)

    def log_callback(message):
        text_box.insert(tk.END, message + "\n")
        with open("log.txt", "a", encoding="utf-8") as log_file:
            log_file.write(message + "\n")
        text_box.see(tk.END)

    def update_stats(total, downloaded):
        stats_label.config(text=f"📦 Filtered: {total} | 📥 Downloaded: {downloaded} | ❌ Errors: 0")

    def update_progress(current, total, speed):
        progress_label.config(text=f"🔄 Progress: {current}/{total} | 🚀 Speed: {speed:.2f} tracks/min")
        progress_bar["maximum"] = total
        progress_bar["value"] = current

    def update_errors(error_count):
        current = stats_label.cget("text")
        parts = current.split("|")
        if len(parts) == 3:
            stats_label.config(text=f"{parts[0].strip()} | {parts[1].strip()} | ❌ Errors: {error_count}")

    def update_chart(progress_data):
        ax.clear()
        ax.plot(progress_data, marker='o', linestyle='-', linewidth=2, color="#03dac6")
        ax.set_title("📈 Download Progress", fontsize=12, color="#ffffff")
        ax.set_xlabel("Iteration", color="#ffffff")
        ax.set_ylabel("Downloaded", color="#ffffff")
        ax.tick_params(colors="#ffffff")
        ax.grid(True, color="#444444")
        chart_canvas.draw()

    def on_start():
        global LIKES_URL
        LIKES_URL = url_entry.get().strip()
        text_box.delete("1.0", tk.END)
        threading.Thread(target=run_downloader, 
                         args=(log_callback, update_stats, update_progress, update_errors, update_chart), 
                         daemon=True).start()

    def on_stop():
        global stop_download
        stop_download = True

    def on_count():
        url = url_entry.get().strip()
        text_box.delete("1.0", tk.END)
        def count_thread():
            log_callback(f"🔍 Counting liked tracks at: {url}")
            count = count_likes_links(url)
            log_callback(f"❤️ Found {count} liked tracks on SoundCloud")
        threading.Thread(target=count_thread, daemon=True).start()

    buttons_frame = ttk.Frame(main_frame)
    buttons_frame.pack(pady=10)

    start_button = ttk.Button(buttons_frame, text="▶ Start Download", command=on_start)
    start_button.pack(side=tk.LEFT, padx=5)

    stop_button = ttk.Button(buttons_frame, text="⛔ Stop", command=on_stop)
    stop_button.pack(side=tk.LEFT, padx=5)

    count_button = ttk.Button(buttons_frame, text="🔍 Count Tracks", command=on_count)
    count_button.pack(side=tk.LEFT, padx=5)

    root.mainloop()

if __name__ == "__main__":
    start_gui()
