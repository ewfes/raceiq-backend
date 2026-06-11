# RaceIQ Backend

Python Flask proxy для Racing API. Вирішує CORS проблему між браузером і theracingapi.com.

## Деплой на Railway (безкоштовно, 5 хвилин)

### 1. Завантаж на GitHub
```bash
git init
git add .
git commit -m "RaceIQ backend"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/raceiq-backend.git
git push -u origin main
```

### 2. Деплой на Railway
1. Зайди на https://railway.app
2. "New Project" → "Deploy from GitHub repo"
3. Вибери репозиторій `raceiq-backend`
4. Railway автоматично задеплоїть
5. Зайди в Settings → Networking → "Generate Domain"
6. Скопіюй URL (типу `https://raceiq-backend-production.up.railway.app`)

### 3. Встав URL в апку RaceIQ
У полі "Backend URL" в апці встав свій Railway URL.

## API Endpoints

### GET /health
Перевірка що сервер живий.

### POST /horses-batch
Отримати дані по кількох конях одразу.
```json
{
  "names": ["Storm Point", "Suggy"],
  "username": "your_racing_api_username",
  "password": "your_racing_api_password"
}
```

### POST /racecards/today
Картки забігів на сьогодні.
```json
{
  "username": "...",
  "password": "...",
  "region": "gb"
}
```

## Локальний запуск (для тесту)
```bash
pip install -r requirements.txt
python app.py
# Сервер на http://localhost:5000
```
