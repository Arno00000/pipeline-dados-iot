"""Baixa o dataset do Kaggle com kagglehub e copia o CSV para data/.

Uso:  python src/download_data.py
Só é necessário se data/IOT-temp.csv não existir.
"""
import shutil
from pathlib import Path

import kagglehub

DATASET = "atulanandjha/temperature-readings-iot-devices"
DEST = Path(__file__).resolve().parent.parent / "data" / "IOT-temp.csv"


def main() -> None:
    folder = Path(kagglehub.dataset_download(DATASET))
    csv = next(folder.rglob("*.csv"))
    DEST.parent.mkdir(exist_ok=True)
    shutil.copy(csv, DEST)
    print(f"CSV copiado para {DEST}")


if __name__ == "__main__":
    main()
