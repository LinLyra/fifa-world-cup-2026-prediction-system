from pathlib import Path
import re
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup

OUT_DIR = Path("data/intelligence")
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUT_DIR / "transfermarkt_national_team_values_v1.csv"

URL = "https://www.transfermarkt.com/vereinsstatistik/wertvollstenationalmannschaften/marktwertetop"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}


def parse_market_value(text: str):
    text = str(text).replace("\xa0", " ").strip()
    text = text.replace("€", "").replace(",", "").strip()

    m = re.search(r"([\d.]+)\s*(bn|m|k)?", text, flags=re.I)
    if not m:
        return None

    value = float(m.group(1))
    unit = (m.group(2) or "").lower()

    if unit == "bn":
        return value * 1_000_000_000
    if unit == "m":
        return value * 1_000_000
    if unit == "k":
        return value * 1_000

    return value


def main():
    rows = []

    # Transfermarkt list is paginated. Usually 25 rows per page.
    for page in range(1, 5):
        url = f"{URL}?page={page}"
        print(f"Fetching {url}")

        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.select_one("table.items")

        if table is None:
            print("No table found. Stopping.")
            break

        for tr in table.select("tbody tr"):
            cols = [td.get_text(" ", strip=True) for td in tr.select("td")]

            text = " | ".join(cols)

            # Find rank
            rank_match = re.search(r"^\s*(\d+)", text)
            rank = int(rank_match.group(1)) if rank_match else None

            # Country name is usually inside hauptlink
            country_el = tr.select_one("td.hauptlink a")
            if not country_el:
                continue

            team = country_el.get_text(" ", strip=True)

            # Market value is usually in rechts hauptlink
            value_el = tr.select_one("td.rechts.hauptlink")
            market_text = value_el.get_text(" ", strip=True) if value_el else cols[-1]
            market_value_eur = parse_market_value(market_text)

            # Confederation appears in columns text, but parsing varies.
            rows.append({
                "rank": rank,
                "team": team,
                "market_value_text": market_text,
                "market_value_eur": market_value_eur,
                "source_url": url,
            })

        time.sleep(1)

    df = pd.DataFrame(rows)
    df = df.dropna(subset=["team"])
    df = df.drop_duplicates("team")
    df = df.sort_values("market_value_eur", ascending=False)

    df.to_csv(OUT_FILE, index=False)

    print(f"\nSaved {OUT_FILE}")
    print(f"Rows: {len(df)}")
    print(df.head(30))


if __name__ == "__main__":
    main()