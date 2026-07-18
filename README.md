# Ashamy - محلل الأسهم الذكي 📈

نظام متقدم لتحليل الأسهم بالذكاء الاصطناعي مع دقة عالية في التنبؤات والإشارات.

## المميزات

### 🤖 نماذج Deep Learning
- **LSTM** - للتسلسلات الزمنية الطويلة
- **GRU** - للتنبؤ السريع والدقيق
- **Transformer** - لتحليل العلاقات طويلة المدى
- **Ensemble** - دمج النماذج الثلاثة بأوزان متعلَّمة

### 📊 10 استراتيجيات تقنية
| الاستراتيجية | الوصف |
|---|---|
| Moving Average | SMA, EMA, WMA بأوزان مختلفة |
| RSI | مؤشر القوة النسبية |
| MACD | تقاطع المتوسطات المتحركة |
| Bollinger Bands | نطاقات التذبذب |
| Stochastic | مؤشر العشوائية |
| ATR | متوسط المدى الحقيقي |
| VWAP | متوسط السعر الموزون بالحجم |
| Fibonacci | مستويات فيبوناتشي |
| Ichimoku | سحابة إيشيموكو |
| Camarilla | نقاط محور كاماريلا |

### 🎯 نظام الإشارات الذكي
- دمج إشارات جميع الاستراتيجيات
- تصفية الإشارات الكاذبة بالحجم والتذبذب
- دمج تنبؤات ML مع الإشارات التقنية
- تقييم مستوى الثقة لكل إشارة

### 📉 Backtesting احترافي
- محاكاة دقيقة للتداول التاريخي
- حساب العمولة والانزلاق
- مقاييس شاملة: Sharpe، Sortino، Max Drawdown، Win Rate

## الهيكل

```
Ashamy/
├── backend/
│   ├── app.py                 # FastAPI رئيسي
│   ├── config.py              # إعدادات
│   ├── requirements.txt
│   ├── data/
│   │   ├── fetcher.py         # جلب البيانات (yfinance)
│   │   ├── processor.py       # تنظيف ومعالجة البيانات
│   │   └── validator.py       # التحقق من الجودة
│   ├── strategies/
│   │   ├── base.py
│   │   ├── technical.py       # Moving Averages
│   │   ├── momentum.py        # RSI, MACD
│   │   ├── volatility.py      # BB, Stochastic, ATR
│   │   └── trend.py           # VWAP, Fibonacci, Ichimoku, Camarilla
│   ├── ml_models/
│   │   ├── lstm_model.py
│   │   ├── gru_model.py
│   │   ├── transformer.py
│   │   ├── ensemble.py
│   │   └── trainer.py
│   ├── signals/
│   │   ├── generator.py
│   │   ├── validator.py
│   │   └── combiner.py
│   ├── backtesting/
│   │   ├── engine.py
│   │   ├── metrics.py
│   │   └── reporter.py
│   └── api/
│       ├── routes.py
│       └── models.py
├── frontend/
│   └── src/
│       ├── components/        # Chart, SignalsList, Recommendations, NavBar
│       ├── pages/             # AnalysisPage, BacktestPage
│       └── services/          # API client
├── tests/
│   ├── test_strategies.py
│   ├── test_ml_models.py
│   ├── test_signals.py
│   └── test_backtesting.py
└── docker-compose.yml
```

## التشغيل السريع

```bash
# مع Docker
docker-compose up --build

# بدون Docker - Backend
cd backend
pip install -r requirements.txt
uvicorn app:app --reload

# بدون Docker - Frontend
cd frontend
npm install
npm run dev
```

## مقاييس الأداء المستهدفة

| المقياس | الهدف |
|---|---|
| Sharpe Ratio | > 1.5 |
| Win Rate | > 55% |
| Max Drawdown | < 20% |
| Profit Factor | > 1.5 |

## التوثيق

- [INSTALLATION.md](docs/INSTALLATION.md) - دليل التثبيت
- [USAGE.md](docs/USAGE.md) - دليل الاستخدام
- [API.md](docs/API.md) - توثيق API