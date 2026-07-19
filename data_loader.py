import pandas as pd

def load_price_data(csv_path: str) -> pd.DataFrame:
    """
    تحميل بيانات الأسعار من ملف CSV
    الأعمدة المتوقعة: Date, Open, High, Low, Close, Volume
    """
    df = pd.read_csv(csv_path, parse_dates=["Date"])
    df = df.sort_values("Date")
    return df
