import uuid
from datetime import datetime
from typing import Optional

import boto3
from botocore.config import Config

from app.core.config import get_settings


class R2Service:
    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[boto3.client] = None

    @property
    def client(self):
        if self._client is None:
            if not all([
                self.settings.r2_account_id,
                self.settings.r2_access_key_id,
                self.settings.r2_secret_access_key,
            ]):
                raise ValueError("R2 credentials not configured")

            self._client = boto3.client(
                "s3",
                endpoint_url=f"https://{self.settings.r2_account_id}.r2.cloudflarestorage.com",
                aws_access_key_id=self.settings.r2_access_key_id,
                aws_secret_access_key=self.settings.r2_secret_access_key,
                config=Config(
                    signature_version="s3v4",
                    retries={"max_attempts": 3, "mode": "standard"},
                ),
            )
        return self._client

    def _generate_filename(self, original_filename: str) -> str:
        ext = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else "jpg"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        return f"pr_images/{timestamp}_{unique_id}.{ext}"

    async def upload_image(self, file_content: bytes, filename: str, content_type: str) -> str:
        key = self._generate_filename(filename)

        self.client.put_object(
            Bucket=self.settings.r2_bucket_name,
            Key=key,
            Body=file_content,
            ContentType=content_type,
        )

        if self.settings.r2_public_url:
            return f"{self.settings.r2_public_url.rstrip('/')}/{key}"
        return f"https://{self.settings.r2_bucket_name}.{self.settings.r2_account_id}.r2.cloudflarestorage.com/{key}"

    async def delete_image(self, url: str) -> bool:
        try:
            if self.settings.r2_public_url and url.startswith(self.settings.r2_public_url):
                key = url.replace(self.settings.r2_public_url.rstrip("/") + "/", "")
            else:
                key = url.split("/")[-1]
                if "pr_images/" not in key:
                    key = f"pr_images/{key}"

            self.client.delete_object(
                Bucket=self.settings.r2_bucket_name,
                Key=key,
            )
            return True
        except Exception:
            return False


def get_r2_service() -> R2Service:
    return R2Service()
