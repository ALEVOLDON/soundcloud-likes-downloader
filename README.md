# SoundCloud Likes Downloader 🎵

Удобное приложение с графическим интерфейсом для скачивания лайкнутых треков с SoundCloud. 

## Возможности 🚀

- Автоматический сбор ссылок с вашей страницы лайков
- Умная фильтрация (пропускает миксы, подкасты и плейлисты)
- Графический интерфейс с прогрессом загрузки
- Визуализация скорости скачивания
- Сохранение всех треков в отдельную папку
- Логирование процесса и ошибок
- Возможность остановки загрузки в любой момент

## Установка 🔧

1. Убедитесь, что у вас установлен Python 3.7 или выше
2. Склонируйте репозиторий:
```bash
git clone https://github.com/ALEVOLDON/soundcloud-likes-downloader.git
cd soundcloud-likes-downloader
```

3. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/MacOS
source .venv/bin/activate
```

4. Установите зависимости:
```bash
pip install selenium matplotlib scdl
```

5. Установите Chrome WebDriver:
   - Скачайте [ChromeDriver](https://sites.google.com/chromium.org/driver/) для вашей версии Chrome
   - Добавьте его в PATH или положите в папку проекта

## Использование 💻

1. Откройте файл `soundcloud_likes_downloader.py` и замените URL в переменной `LIKES_URL` на ваш URL страницы лайков SoundCloud:
```python
LIKES_URL = "https://soundcloud.com/your-username/likes"
```

2. Запустите программу:
```bash
python soundcloud_likes_downloader.py
```

3. В открывшемся окне нажмите "▶ Начать загрузку"
4. Следите за прогрессом в интерфейсе
5. Все скачанные треки будут находиться в папке `downloads`

## Настройка фильтров 🔍

Вы можете настроить какие треки пропускать, отредактировав список `EXCLUDE_KEYWORDS` в файле `soundcloud_likes_downloader.py`:

```python
EXCLUDE_KEYWORDS = [
    "mix", "set", "podcast", "dj", "hour", "live", "sessions",
    "/sets/", "/likes/", "/reposts/", "playlist"
]
```

## Требования 📋

- Python 3.7+
- Chrome браузер
- ChromeDriver
- Доступ к интернету
- Достаточно места на диске для скачивания треков

## Решение проблем ⚠️

1. Если возникает ошибка с ChromeDriver:
   - Убедитесь, что версия ChromeDriver соответствует версии вашего Chrome
   - Проверьте, что ChromeDriver доступен в PATH

2. Если треки не скачиваются:
   - Проверьте подключение к интернету
   - Убедитесь, что трек доступен для скачивания на SoundCloud
   - Проверьте логи в интерфейсе программы

## Лицензия 📄

MIT License - делайте что хотите, просто указывайте автора 😊

## Поддержка 💖

Если у вас есть предложения по улучшению или вы нашли баг, создавайте Issue или Pull Request! 