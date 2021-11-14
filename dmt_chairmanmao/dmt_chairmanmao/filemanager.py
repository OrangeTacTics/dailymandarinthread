from __future__ import annotations
import typing as t
from io import BytesIO

import boto3

from .config import Configuration


class FileManager:
    def __init__(self, config: Configuration) -> None:
        self.config = config

        self.session = boto3.session.Session()
        self.client = self.session.client(
            "s3",
            region_name=config.DO_SPACES_REGION,
            endpoint_url=config.DO_SPACES_URL,
            aws_access_key_id=config.DO_SPACES_KEY,
            aws_secret_access_key=config.DO_SPACES_SECRET,
        )

    def download(self, filename: str) -> t.BinaryIO:
        buf = BytesIO()
        self.client.download_fileobj(self.config.DO_SPACES_BUCKETNAME, filename, buf)
        buf.seek(0)
        return buf

    def upload(self, filename: str, fp: t.BinaryIO) -> None:
        self.client.upload_fileobj(fp, self.config.DO_SPACES_BUCKETNAME, filename)

    def list(self, dirname: str) -> t.List[str]:
        results = []
        response = self.client.list_objects(Bucket=self.config.DO_SPACES_BUCKETNAME)
        for obj in response["Contents"]:
            key = obj["Key"]
            if key == dirname + "/":
                continue

            if key.startswith(dirname + "/"):
                results.append(key)
        return results
