class ParquetDayReader:

    def __init__(self, storage):
        self.storage = storage

    def read_day(self, symbol, interval, day):
        key = f"{symbol}-{interval}-{day}.parquet"
        try:
            return self.storage.read_parquet(key)
        except Exception:
            return None
