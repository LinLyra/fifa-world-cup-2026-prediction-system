from pathlib import Path
import pandas as pd

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

URLS = {
    "results": "https://raw.githubusercontent.com/martj42/international_results/master/results.csv",
    "shootouts": "https://raw.githubusercontent.com/martj42/international_results/master/shootouts.csv",
    "goalscorers": "https://raw.githubusercontent.com/martj42/international_results/master/goalscorers.csv",
}

def download():
    for name, url in URLS.items():
        print(f"Downloading {name}...")
        df = pd.read_csv(url)
        out = RAW_DIR / f"{name}.csv"
        df.to_csv(out, index=False)
        print(f"Saved {out} | rows={len(df):,} | cols={len(df.columns)}")

if __name__ == "__main__":
    download()