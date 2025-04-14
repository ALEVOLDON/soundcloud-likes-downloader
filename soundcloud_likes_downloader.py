#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import os
import subprocess
import threading
import tkinter as tk
from tkinter import ttk
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import shutil
import re

INPUT_FILE = "links.txt"
OUTPUT_FILE = "filtered_links.txt"
DEFAULT_LIKES_URL = "https://soundcloud.com/g_t_w_y/likes"
DOWNLOAD_DIR = "downloads"

EXCLUDE_KEYWORDS = [
    "mix", "set", "podcast", "dj", "hour", "live", "sessions",
    "/sets/", "/likes/", "/reposts/", "playlist", "comments", "followers",
    "following", "/tags/"
]

# Utility: Scroll to load all tracks
def scroll_to_bottom(driver, max_scrolls=30, delay=2):
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(max_scrolls):
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
        time.sleep(delay)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

# Utility: Extract track links from the page
def extract_track_links(driver):
    a_tags = driver.find_elements(By.XPATH, "//a[contains(@href, '/')]")
    links = set()
    for tag in a_tags:
        href = tag.get_attribute("href")
        if href and "soundcloud.com" in href:
            parts = href.split("/")
            if len(parts) >= 5 and parts[3] != "you":
                links.add(href)
    return links

# Utility: Validate URL to avoid shell injection
def is_valid_url(url):
    return re.match(r'^https://soundcloud\.com/[^\s]+$', url)

# Core download runner
def run_downloader(url, log, update_stats, update_progress, update_errors, update_chart, stop_flag):
    if not shutil.which("scdl"):
        log("❌ SCDL is not installed or not in PATH.")
        return

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    log(f"📁 Using download directory: {DOWNLOAD_DIR}")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")

    log("🌐 Opening SoundCloud likes page...")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(5)
    scroll_to_bottom(driver)
    links = extract_track_links(driver)
    driver.quit()

    with open(INPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(links)))
    log(f"✅ Found {len(links)} links. Saved to {INPUT_FILE}")

    filtered = [l for l in links if not any(k in l.lower() for k in EXCLUDE_KEYWORDS)]
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(filtered)))

    total = len(filtered)
    update_stats(total, 0)
    log(f"📊 Total: {len(links)} | Filtered: {total} ({(total/len(links)*100):.1f}%)")

    log("⬇️ Starting downloads...")
    downloaded, failed = 0, []
    start_time = time.time()
    progress_data = []

    for idx, link in enumerate(filtered):
        if stop_flag[0]:
            log("🛑 Download manually stopped.")
            break
        if not is_valid_url(link):
            log(f"⚠️ Skipping invalid URL: {link}")
            continue

        log(f"🎧 Downloading: {link}")
        try:
            result = subprocess.run([
                "scdl", "-l", link, "-c", "--onlymp3", "--path", DOWNLOAD_DIR
            ], capture_output=True, text=True, encoding="utf-8", errors="replace")

            if result.returncode != 0:
                log(result.stderr)
                raise Exception("Download error")

            downloaded += 1
            elapsed = time.time() - start_time
            speed = downloaded / elapsed * 60 if elapsed else 0
            update_stats(total, downloaded)
            update_progress(idx + 1, total, speed)
            progress_data.append(downloaded)
            update_chart(progress_data)

        except Exception as e:
            failed.append(link)
            update_errors(len(failed))
            log(f"❌ Failed: {link} — {e}")

    if failed:
        with open("failed_links.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(failed))
        log(f"⚠️ {len(failed)} downloads failed. See failed_links.txt")

# Count likes only
def count_likes_links(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")

    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(5)
    scroll_to_bottom(driver)
    links = extract_track_links(driver)
    driver.quit()
    return len(links)

# GUI
def start_gui():
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

    stop_flag = [False]  # mutable flag for threading

    frame = ttk.Frame(root, padding=10)
    frame.pack(fill=tk.BOTH, expand=True)

    url_label = ttk.Label(frame, text="🔗 Likes Page URL:")
    url_label.pack(anchor=tk.W, padx=5, pady=(5, 0))

    url_entry = tk.Entry(frame, bg="#1e1e1e", fg="#e0e0e0", insertbackground="#ffffff", font=("Consolas", 10))
    url_entry.insert(0, DEFAULT_LIKES_URL)
    url_entry.pack(fill=tk.X, padx=5, pady=5)

    text_box = tk.Text(frame, height=20, wrap=tk.WORD, bg="#1e1e1e", fg="#e0e0e0", insertbackground="#ffffff", font=("Consolas", 10), relief=tk.FLAT)
    text_box.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    stats_label = ttk.Label(frame, text="📦 Filtered: 0 | 📥 Downloaded: 0 | ❌ Errors: 0")
    stats_label.pack(anchor=tk.W, pady=2)

    progress_label = ttk.Label(frame, text="🔄 Progress: 0/0 | 🚀 Speed: 0.00 tracks/min")
    progress_label.pack(anchor=tk.W, pady=2)

    progress_bar = ttk.Progressbar(frame, orient="horizontal", mode="determinate")
    progress_bar.pack(fill=tk.X, padx=5, pady=(0, 10))

    fig, ax = plt.subplots(figsize=(6, 3))
    fig.patch.set_facecolor("#121212")
    ax.set_facecolor("#1e1e1e")
    chart_canvas = FigureCanvasTkAgg(fig, master=frame)
    chart_widget = chart_canvas.get_tk_widget()
    chart_widget.pack(pady=10, fill=tk.BOTH, expand=True)

    def log(message):
        text_box.insert(tk.END, message + "\n")
        with open("log.txt", "a", encoding="utf-8") as f:
            f.write(message + "\n")
        text_box.see(tk.END)

    def update_stats(total, downloaded):
        stats_label.config(text=f"📦 Filtered: {total} | 📥 Downloaded: {downloaded} | ❌ Errors: 0")

    def update_progress(current, total, speed):
        progress_label.config(text=f"🔄 Progress: {current}/{total} | 🚀 Speed: {speed:.2f} tracks/min")
        progress_bar["maximum"] = total
        progress_bar["value"] = current

    def update_errors(error_count):
        current = stats_label.cget("text").split("|")
        if len(current) == 3:
            stats_label.config(text=f"{current[0].strip()} | {current[1].strip()} | ❌ Errors: {error_count}")

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
        stop_flag[0] = False
        url = url_entry.get().strip()
        text_box.delete("1.0", tk.END)
        threading.Thread(target=run_downloader, args=(url, log, update_stats, update_progress, update_errors, update_chart, stop_flag), daemon=True).start()

    def on_stop():
        stop_flag[0] = True

    def on_count():
        url = url_entry.get().strip()
        text_box.delete("1.0", tk.END)
        def count_thread():
            log(f"🔍 Counting liked tracks at: {url}")
            count = count_likes_links(url)
            log(f"❤️ Found {count} liked tracks on SoundCloud")
        threading.Thread(target=count_thread, daemon=True).start()

    buttons = ttk.Frame(frame)
    buttons.pack(pady=10)
    ttk.Button(buttons, text="▶ Start Download", command=on_start).pack(side=tk.LEFT, padx=5)
    ttk.Button(buttons, text="⛔ Stop", command=on_stop).pack(side=tk.LEFT, padx=5)
    ttk.Button(buttons, text="🔍 Count Tracks", command=on_count).pack(side=tk.LEFT, padx=5)

    root.mainloop()

if __name__ == "__main__":
    start_gui()
