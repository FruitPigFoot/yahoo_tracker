import requests
from bs4 import BeautifulSoup

WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbzU-b7ignxsiBdN0JKKt0HxET8J-9QVAHy-3Mwbvacr8AvGesKNU6EaeSdPYJdPQX5O/exec"
SHEET_ID = "1_2t1ByUIxaMty-cJK0e_ouPBwylM_les0L57Q70TvQY"

def get_urls_from_sheet():
    SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    res = requests.get(SHEET_URL)
    rows = res.text.splitlines()[1:]  # skip header
    return [row.split(",")[0] for row in rows if row.strip()]

def get_price_status(url, row):
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(res.text, "html.parser")

    span = soup.find("span", class_=lambda c: c and "kxUAXU" in c)
    price = span.get_text(strip=True).replace(",", "").replace("円", "") if span else "N/A"
    is_closed = "closedNotice" in res.text
    status = "CLOSED" if is_closed else "OPEN"

    return {
        "row": row,
        "price": price,
        "status": status,
        "is_closed": is_closed
    }

def main():
    urls = get_urls_from_sheet()
    for i, url in enumerate(urls, start=2):
        if not url.startswith("http"):
            continue
        print(f"Checking row {i}: {url}")
        data = get_price_status(url, i)
        if data["is_closed"]:
            print(f" → Skipping CLOSED auction at row {i}")
            continue
        try:
            res = requests.post(WEBHOOK_URL, json={
                "row": data["row"],
                "price": data["price"],
                "status": data["status"]
            })
            print(f" → Updated row {i}: {res.text}")
        except Exception as e:
            print(f" → Error updating row {i}: {e}")

if __name__ == "__main__":
    main()
