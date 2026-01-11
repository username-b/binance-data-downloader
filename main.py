import os
import pandas as pd
import requests
import zipfile
import io
from datetime import datetime, timedelta, timezone
from tqdm import tqdm

import config


# =========================
# DATES
# =========================
today = datetime.now(timezone.utc).date()
dates = sorted([
    today - timedelta(days=i)
    for i in range(1, config.DAYS_BACK + 1)
])


# =========================
# LOAD + PROCESS
# =========================
def load_and_process_file(url: str) -> pd.DataFrame | None:
    try:
        r = requests.get(url, timeout=20)
        if r.status_code != 200:
            return None

        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            with z.open(z.namelist()[0]) as f:
                df = pd.read_csv(f, header=0, low_memory=False)

        df = df.dropna(how="all")
        df = df.iloc[:, :len(config.KLINES_COLUMNS)]
        df.columns = config.KLINES_COLUMNS


        for c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="ignore")

        return df

    except Exception as e:
        print(f"⚠️ Ошибка {url}: {e}")
        return None


# =========================
# SAVE DIR
# =========================
timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
save_dir = os.path.join(config.DATA_ROOT, timestamp_str)
os.makedirs(save_dir, exist_ok=True)

out_file = os.path.join(save_dir, "klines_1m.csv")

print(f"\n📁 Сохраняем в: {save_dir}")


# =========================
# MAIN LOOP
# =========================
for dt in tqdm(dates, desc="Downloading klines"):
    y = dt.year
    m = f"{dt.month:02d}"
    d = f"{dt.day:02d}"

    path = (
        f"{config.BASE_ROOT}/"
        f"{config.SOURCE}/"
        f"{config.SYMBOL}/"
        f"{config.INTERVAL}"
    )

    file_name = f"{config.SYMBOL}-{config.INTERVAL}-{y}-{m}-{d}.zip"
    url = f"{path}/{file_name}"

    df = load_and_process_file(url)

    if df is not None and not df.empty:
        header = not os.path.exists(out_file)
        df.to_csv(out_file, mode="a", header=header, index=False)

    del df


print("\n✅ Загрузка klines завершена")
