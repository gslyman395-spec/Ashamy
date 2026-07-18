# دليل الاستخدام - Ashamy

## تحليل سهم

### من الواجهة الأمامية (Frontend)
1. افتح http://localhost:3000
2. أدخل رمز السهم (مثال: `AAPL`, `MSFT`, `2222.SR`)
3. اختر الفترة الزمنية والفاصل
4. اضغط **تحليل**
5. راجع الرسم البياني والإشارات والتوصية

### من API مباشرة

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "period": "2y", "interval": "1d"}'
```

## Backtesting

### من الواجهة
1. انتقل إلى صفحة **الباك تست**
2. أدخل الرمز ورأس المال الابتدائي
3. اضغط **اختبار**
4. راجع المقاييس ومنحنى الأسهم والتقرير

### من API

```bash
curl -X POST http://localhost:8000/api/v1/backtest \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "period": "2y", "initial_capital": 100000}'
```

## تدريب نموذج ML

```python
from backend.data import DataFetcher, DataProcessor
from backend.ml_models import ModelTrainer

fetcher = DataFetcher()
processor = DataProcessor()

df = fetcher.fetch("AAPL", period="5y")
df = processor.clean(df)
df = processor.add_returns(df)

features = processor.prepare_features(df)
X, y = processor.create_sequences(features, sequence_length=60, horizon=1)

trainer = ModelTrainer(input_size=features.shape[1], epochs=50)
history = trainer.train(X[:800], y[:800], X[800:], y[800:])
trainer.save()
```

## الإشارات المتاحة

| القيمة | المعنى |
|---|---|
| `1` | إشارة شراء |
| `-1` | إشارة بيع |
| `0` | انتظار |
