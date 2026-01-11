import io
import pandas as pd
import boto3
from config import YC_ACCESS_KEY_ID, YC_SECRET_ACCESS_KEY, YC_REGION


class YandexObjectStorage:
    
    def __init__(self, bucket: str, prefix: str = ""):
        self.bucket = bucket
        self.prefix = prefix

        self.s3 = boto3.client(
        "s3",
        endpoint_url="https://storage.yandexcloud.net",
        region_name=YC_REGION,
        aws_access_key_id=YC_ACCESS_KEY_ID,
        aws_secret_access_key=YC_SECRET_ACCESS_KEY,
    )


    def write_parquet(self, df: pd.DataFrame, key: str) -> None:
        buffer = io.BytesIO()

        df.to_parquet(
            buffer,
            index=False,
            engine="pyarrow",
            compression="zstd",
        )

        full_key = f"{self.prefix}/{key}".lstrip("/")

        self.s3.put_object(
            Bucket=self.bucket,
            Key=full_key,
            Body=buffer.getvalue(),
        )
