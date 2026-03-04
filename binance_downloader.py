import io
import zipfile
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone, date
from collections import defaultdict
from tqdm import tqdm
import psutil, time

import config
from utils.logger import get_logger
from yandex_storage import YandexObjectStorage


logger = get_logger(__name__)
p = psutil.Process()

# =========================
# STORAGE
# =========================
raw_storage = YandexObjectStorage(
    bucket=config.YC_BUCKET,
    prefix="klines_raw"
)

base_storage = YandexObjectStorage(
    bucket=config.YC_BUCKET,
    prefix="klines_base"
)



# =========================
# DATES
# =========================
today = datetime.now(timezone.utc).date()
today = date(2026, 2, 1)
dates = sorted([
    today - timedelta(days=i)
    for i in range(1, config.DAYS_BACK + 1)
])

logger.info(
    "Start parquet download | symbol=%s interval=%s days=%d",
    config.SYMBOL,
    config.INTERVAL,
    config.DAYS_BACK,
)


# =========================
# LOAD + PROCESS
# =========================
def extract_klines_base(df: pd.DataFrame) -> pd.DataFrame:
    base = df[[
        "open_time",
        "close",
    ]].copy()

    # защита
    base = base.drop_duplicates(subset=["open_time"])
    base = base.sort_values("open_time")

    return base[[
        "open_time",
        "close",
    ]]


def load_and_process_file(url: str) -> pd.DataFrame | None:
    try:
        r = requests.get(url, timeout=20)
        if r.status_code != 200:
            logger.warning("File not found: %s", url)
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

    except Exception:
        logger.exception("Failed to load %s", url)
        return None


# =========================
# MAIN LOOP
# =========================

weeks: dict[tuple[int, int], list[datetime]] = defaultdict(list)

for dt in dates:
    year, week, _ = dt.isocalendar()
    weeks[(year, week)].append(dt)
weekly_frames: list[pd.DataFrame] = []

for (year, week), week_dates in weeks.items():
    weekly_frames = []

    for dt in tqdm(week_dates, desc=f"Week {year}-W{week}"):
        y, m, d = dt.year, dt.month, dt.day

        path = (
            f"{config.BASE_ROOT}/"
            f"{config.SOURCE}/"
            f"{config.SYMBOL}/"
            f"{config.INTERVAL}"
        )

        file_name = f"{config.SYMBOL}-{config.INTERVAL}-{y}-{m:02d}-{d:02d}.zip"
        url = f"{path}/{file_name}"

        df = load_and_process_file(url)

        if df is None or df.empty:
            logger.info("Skipped %s (no data)", dt)
            continue

        weekly_frames.append(df)

    if not weekly_frames:
        logger.warning("No data collected for week %s-W%s", year, week)
        continue

    weekly_df = pd.concat(weekly_frames, ignore_index=True)
    klines_base_df = extract_klines_base(weekly_df)

    start_date = min(week_dates)
    end_date = max(week_dates)

    key = (
        f"{config.SYMBOL}-{config.INTERVAL}-"
        f"{start_date:%Y-%m-%d}_{end_date:%Y-%m-%d}.parquet"
    )

    raw_storage.write_parquet(weekly_df, key)
    base_storage.write_parquet(klines_base_df, key)

    logger.info(
        "Saved weekly parquet %s | rows=%d",
        key,
        len(weekly_df)
    )



logger.info("Parquet download finished successfully")

print("RAM (MB):", p.memory_info().rss / 1024 / 1024)
print("CPU (%):", p.cpu_percent(interval=1))