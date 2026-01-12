import io
import zipfile
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone, date
from collections import defaultdict
from tqdm import tqdm
import psutil, time
import gc

import config
from utils.logger import get_logger
from yandex_storage import YandexObjectStorage


logger = get_logger(__name__)
p = psutil.Process()

# =========================
# STORAGE
# =========================
dataset_cfg = config.DATASETS[config.DATASET]

raw_storage = YandexObjectStorage(
    bucket=config.YC_BUCKET,
    prefix=dataset_cfg["storage_prefix"]
)

base_storage = YandexObjectStorage(
    bucket=config.YC_BUCKET,
    prefix="klines_base"
)

# =========================
# DATES
# =========================
# today = datetime.now(timezone.utc).date()
today = date(2026, 1, 10)
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
def build_url(dataset, *, symbol, interval, date, base_root):
    cfg = config.DATASETS[dataset]

    path = [base_root, cfg["source"], symbol]
    if cfg["has_interval"]:
        path.append(interval)

    filename = cfg["file_pattern"].format(
        symbol=symbol,
        interval=interval,
        date=f"{date:%Y-%m-%d}",
    )

    return "/".join(path) + "/" + filename


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
        columns = dataset_cfg["columns"]
        df = df.iloc[:, :len(columns)]
        df.columns = columns


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

        file_name = f"{config.SYMBOL}-{config.INTERVAL}-{y}-{m:02d}-{d:02d}.zip"
        url = build_url(
            dataset=config.DATASET,
            symbol=config.SYMBOL,
            interval=config.INTERVAL,
            date=dt,
            base_root=config.BASE_ROOT,
        )

        df = load_and_process_file(url)

        if df is None or df.empty:
            logger.info("Skipped %s (no data)", dt)
            continue

        weekly_frames.append(df)

    if not weekly_frames:
        logger.warning("No data collected for week %s-W%s", year, week)
        continue

    weekly_df = pd.concat(weekly_frames, ignore_index=True)
    if config.DATASET == "klines":
        klines_base_df = extract_klines_base(weekly_df)

    start_date = min(week_dates)
    end_date = max(week_dates)

    key = (
        f"{config.SYMBOL}-{config.INTERVAL}-"
        f"{start_date:%Y-%m-%d}_{end_date:%Y-%m-%d}.parquet"
    )

    raw_storage.write_parquet(weekly_df, key)
    if config.DATASET == "klines":
        base_storage.write_parquet(klines_base_df, key)

    logger.info(
        "Saved weekly parquet %s | rows=%d",
        key,
        len(weekly_df)
    )

    raw_storage.write_parquet(weekly_df, key)

    del weekly_df
    del weekly_frames
    del df
    gc.collect()



logger.info("Parquet download finished successfully")

print("RAM (MB):", p.memory_info().rss / 1024 / 1024)
print("CPU (%):", p.cpu_percent(interval=1))