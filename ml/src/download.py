"""Download the original UCI archive without extracting arbitrary paths."""
import hashlib
import io
import json
import zipfile
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
URL = "https://archive.ics.uci.edu/static/public/601/ai4i+2020+predictive+maintenance+dataset.zip"
SOURCE = "https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset"


def main():
    response = requests.get(URL, timeout=(10, 60))
    response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        content = archive.read("ai4i2020.csv")
    target = ROOT / "ml/data"
    target.mkdir(parents=True, exist_ok=True)
    (target / "ai4i2020.csv").write_bytes(content)
    manifest = {"source": SOURCE, "download_url": URL, "license": "CC BY 4.0",
                "doi": "10.24432/C5HS5C", "sha256": hashlib.sha256(content).hexdigest()}
    (target / "source.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Dados UCI salvos em {target}. SHA256: {manifest['sha256']}")


if __name__ == "__main__":
    main()
