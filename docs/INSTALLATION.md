# دليل التثبيت - Ashamy

## المتطلبات

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose (اختياري)

## تثبيت Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Linux/macOS
# أو: venv\Scripts\activate       # Windows

pip install -r requirements.txt
```

## إعداد المتغيرات البيئية

```bash
cp .env.example .env
# عدّل .env وأضف مفاتيح API إن أردت
```

## تشغيل Backend

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

الواجهة التفاعلية: http://localhost:8000/docs

## تثبيت Frontend

```bash
cd frontend
npm install
npm run dev
```

التطبيق يعمل على: http://localhost:3000

## تشغيل بـ Docker

```bash
# من جذر المشروع
docker-compose up --build
```

## تشغيل الاختبارات

```bash
cd backend
pip install pytest pytest-asyncio
pytest ../tests/ -v
```
