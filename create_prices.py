import pandas as pd
import random

dates = pd.date_range(start="2024-01-01", periods=60)

prices = []
price = 100

for d in dates:
    open_p = price
    high_p = price + random.uniform(1, 5)
    low_p = price - random.uniform(1, 5)
    close_p = low_p + (high_p - low_p) * random.random()
    volume = random.randint(50000, 120000)

    prices.append([d.strftime("%Y-%m-%d"), round(open_p,2), round(high_p,2),
                   round(low_p,2), round(close_p,2), volume])

    price = close_p  # تحديث السعر لليوم التالي

df = pd.DataFrame(prices, columns=["Date","Open","High","Low","Close","Volume"])
df.to_csv("prices.csv", index=False)

print("✔ تم إنشاء ملف أسعار كبير (60 يوم) بنجاح")


