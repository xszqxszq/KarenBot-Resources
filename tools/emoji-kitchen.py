import argparse
import json
import os
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
from urllib.request import Request, urlopen

METADATA_URL = "https://emojikitchen.dev/metadata.json"
ROOT = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "data", "meme", "emoji"
))
HEADERS = {"User-Agent": "Mozilla/5.0"}


def fetch(url, timeout):
    return urlopen(Request(url, headers=HEADERS), timeout=timeout).read()


def load_metadata(directory):
    path = os.path.join(directory, "metadata.json")
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            print("metadata.json 读取失败，重新拉取中……")
    print(f"正在拉取 {METADATA_URL}……")
    buffer = bytearray()
    with urlopen(Request(METADATA_URL, headers=HEADERS), timeout=1800) as resp:
        total = int(resp.headers.get("Content-Length") or 0)
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            buffer += chunk
            print(f"metadata {len(buffer) // 1048576}/{total // 1048576} MB", end="\r")
    print()
    json.loads(buffer.decode("utf-8"))
    tmp = path + ".part"
    with open(tmp, "wb") as f:
        f.write(buffer)
    os.replace(tmp, path)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def collect(metadata):
    items = {}
    for emoji in metadata["data"]:
        for comb in metadata["data"][emoji]["combinations"].values():
            for record in comb:
                parts = urlparse(record["gStaticUrl"]).path.strip("/").split("/")
                items.setdefault(
                    os.path.join(parts[-2], parts[-1].split("_")[1]),
                    record["gStaticUrl"],
                )
    return items


def download(directory, item, force):
    path, url = item
    target = os.path.join(directory, path)
    if not force and os.path.exists(target):
        return None
    try:
        content = fetch(url, 30)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        tmp = target + ".part"
        with open(tmp, "wb") as f:
            f.write(content)
        os.replace(tmp, target)
        return None
    except Exception as e:
        return (url, repr(e))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="重新下载全部图片")
    parser.add_argument("--concurrency", type=int, default=8)
    args = parser.parse_args()

    directory = ROOT
    os.makedirs(directory, exist_ok=True)
    items = collect(load_metadata(directory))
    if args.all:
        todo = sorted(items.items())
    else:
        todo = sorted(
            (path, url) for path, url in items.items()
            if not os.path.exists(os.path.join(directory, path))
        )
    print(f"共 {len(items)} 个文件，本次下载 {len(todo)} 个")
    if not todo:
        return

    done = 0
    failed = []
    with ThreadPoolExecutor(args.concurrency) as pool:
        for result in pool.map(lambda item: download(directory, item, args.all), todo):
            done += 1
            if result:
                failed.append(result)
            print(f"进度 {done}/{len(todo)}", end="\r")
    print()
    print(f"完成，失败 {len(failed)} 个")
    for url, err in failed[:20]:
        print("  ", url, err)


if __name__ == "__main__":
    main()
