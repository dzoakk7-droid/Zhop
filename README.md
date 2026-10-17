# 🧭 GeoSleuth Web

**Упрощённая веб-версия инструмента геолокации фотографий**

Inspired by [geo-sleuth](https://github.com/Oldcircle/geo-sleuth) — agent skill that finds where a photo was taken.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Что это

Веб-приложение, которое принимает фотографию и пытается определить место съёмки, используя доступные метаданные и открытые данные.

### Что умеет сейчас

| Функция | Статус |
|---------|--------|
| Загрузка фото (drag & drop) | ✅ |
| Извлечение GPS, даты, камеры из EXIF | ✅ |
| Базовая информация об изображении | ✅ |
| Поиск ближайших объектов через OpenStreetMap | ✅ (если есть GPS) |
| Интерактивная карта (Leaflet) | ✅ |
| Пошаговый лог анализа | ✅ |
| Адаптивный интерфейс (удобно с телефона) | ✅ |

### Чего пока нет (ограничения веб-версии)

Оригинальный [geo-sleuth](https://github.com/Oldcircle/geo-sleuth) — это мощный локальный agent skill со скриптами, Playwright и ML-моделями. В чистом вебе часть функций пока недоступна:

- Полноценный reverse image search (Baidu / Yandex через браузерную автоматизацию)
- Skyline matching и анализ высот (DEM)
- CLIP / DINOv2 ранжирование спутниковых и street-view снимков
- Геометрический анализ (пирсы, тени, bearings)

---

## Быстрый старт

### 1. Клонировать репозиторий

```bash
git clone https://github.com/<your-username>/geo-sleuth-web.git
cd geo-sleuth-web
```

### 2. Установить зависимости

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Запустить

```bash
python main.py
```

Откройте в браузере: **http://localhost:8000**

---

## Структура проекта

```
geo-sleuth-web/
├── main.py                 # FastAPI приложение
├── services/
│   ├── exif_service.py     # Извлечение EXIF + GPS
│   ├── image_service.py    # Базовая обработка изображения
│   ├── osm_service.py      # OpenStreetMap Overpass API
│   └── reverse_service.py  # Заглушка reverse image search
├── templates/
│   ├── index.html          # Страница загрузки
│   └── result.html         # Результаты + карта
├── static/                 # Статические файлы
├── uploads/                # Загруженные фото (в .gitignore)
├── requirements.txt
├── LICENSE
└── README.md
```

---

## API

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/` | Главная страница |
| `POST` | `/api/upload` | Загрузка фото (multipart/form-data) |
| `GET` | `/api/job/{job_id}` | Статус и результат анализа |
| `GET` | `/result/{job_id}` | HTML-страница с результатами |
| `GET` | `/health` | Проверка работоспособности |
| `GET` | `/docs` | Swagger UI (автоматически) |

---

## Дальнейшее развитие

Можно постепенно добавлять возможности оригинального geo-sleuth:

1. **OCR** — easyocr / RapidOCR
2. **Reverse image search** — Playwright + Yandex/Baidu
3. **Elevation / skyline** — подключение terrain-скриптов
4. **ML matching** — CLIP и DINOv2 (потребует GPU)
5. **Очередь задач** — Celery / Redis вместо in-memory

Pull requests приветствуются.

---

## Благодарности

- [geo-sleuth](https://github.com/Oldcircle/geo-sleuth) by Oldcircle — основная идея и вдохновение
- [OpenStreetMap](https://www.openstreetmap.org/) и Overpass API
- [Leaflet](https://leafletjs.com/)
- [FastAPI](https://fastapi.tiangolo.com/)

---

## Лицензия

MIT. См. [LICENSE](LICENSE).

**Ответственное использование:** используйте только на своих фотографиях или тех, на анализ которых у вас есть разрешение. Не применяйте для поиска людей без их согласия.
