from pathlib import Path
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup

OUT_DIR = Path("data/raw")
OUT_DIR.mkdir(parents=True, exist_ok=True)

URL = "https://www.international-football.net/elo-ratings-table"

def main():
    html = requests.get(
        URL,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0"}
    ).text

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n")

    rows = []

    # 解析类似：1. Spain, 2165
    pattern = re.compile(r"^\s*(\d+)\.\s*([A-Za-zÀ-ÿ .'-]+),\s*(\d{3,4})\s*$")

    for line in text.splitlines():
        line = line.strip()
        m = pattern.match(line)
        if m:
            rows.append({
                "rank": int(m.group(1)),
                "team": m.group(2).strip(),
                "official_elo": int(m.group(3)),
            })

    if not rows:
        raise ValueError("Could not parse Elo table from international-football.net")

    df = pd.DataFrame(rows).drop_duplicates("team")
    df = df.sort_values("rank")

    out = OUT_DIR / "official_elo_raw.csv"
    df.to_csv(out, index=False)

    print(f"Saved {out}")
    print(f"Rows: {len(df)}")
    print(df.head(30))

if __name__ == "__main__":
    main()