from __future__ import annotations

import csv
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "audit" / "url-normalization-after.csv"

URLS = [
    "https://studyhub.co.kr/",
    "https://studyhub.co.kr/index.html",
    "https://studyhub.co.kr/서울과외/",
    "https://studyhub.co.kr/서울과외",
    "https://studyhub.co.kr/서울과외/index.html",
    "https://studyhub.co.kr//서울과외//",
    "https://studyhub.co.kr/서울과외/?test=1",
    "https://studyhub.co.kr/서울과외/index.html?test=1",
]


def parse_headers(raw: str) -> list[dict[str, str]]:
    blocks = []
    current: dict[str, str] | None = None
    for line in raw.splitlines():
        line = line.strip("\r")
        if not line:
            continue
        if line.startswith("HTTP/"):
            if current:
                blocks.append(current)
            parts = line.split(" ", 2)
            current = {"status": parts[1] if len(parts) > 1 else "", "location": "", "content_type": "", "server": ""}
            continue
        if current is None or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.lower()
        value = value.strip()
        if key == "location":
            current["location"] = value
        elif key == "content-type":
            current["content_type"] = value
        elif key == "server":
            current["server"] = value
    if current:
        blocks.append(current)
    return blocks


def main() -> None:
    rows = []
    for url in URLS:
        command = ["curl.exe", "-I", "-L", "--max-redirs", "6", "--connect-timeout", "10", "--max-time", "30", url]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        headers = parse_headers(result.stdout + "\n" + result.stderr)
        statuses = " -> ".join(block["status"] for block in headers)
        locations = " | ".join(block["location"] for block in headers if block["location"])
        rows.append(
            {
                "url": url,
                "status_chain": statuses,
                "redirect_count": str(max(0, len(headers) - 1)),
                "locations": locations,
                "final_status": headers[-1]["status"] if headers else "",
                "final_content_type": headers[-1]["content_type"] if headers else "",
                "server": headers[-1]["server"] if headers else "",
                "curl_exit": str(result.returncode),
            }
        )

    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "url",
                "status_chain",
                "redirect_count",
                "locations",
                "final_status",
                "final_content_type",
                "server",
                "curl_exit",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
