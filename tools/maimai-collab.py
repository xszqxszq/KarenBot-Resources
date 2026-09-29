#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
import tempfile
import unicodedata
from urllib.request import Request, urlopen

ROOT = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), ".."
))
GAMES = ["chunithm", "ongeki", "wacca", "taiko", "gc", "sdvx"]
URL = "https://dp4p6x0xfi5o9.cloudfront.net/%s/data.json"
HEADERS = {"User-Agent": "Mozilla/5.0"}

ORIG = {
    "ongeki": lambda c: c == "オンゲキ",
    "chunithm": lambda c: c in ("ORIGINAL", "イロドリミドリ"),
    "wacca": lambda c: c in ("オリジナル", "TANO*C（オリジナル）"),
    "taiko": lambda c: "ナムコオリジナル" in (c or ""),
    "gc": lambda c: c == "オリジナル",
    "sdvx": lambda c: "SDVXオリジナル" in (c or ""),
}
SCOPE = {g: ("オンゲキCHUNITHM" if g in ("ongeki", "chunithm") else "ゲームバラエティ")
         for g in GAMES}
SPECIAL = {"chunithm": [11604, 11605]}

IRODORI_NAMES = [
    "御形アリシアナ", "明坂芹菜", "天王洲なずな", "小仏凪", "箱部なる",
    "月鈴白奈", "月鈴那知", "五十嵐撫子", "萩原七々瀬", "葛城華", "小野美苗",
    "イロドリミドリ", "月鈴姉妹", "舞ヶ原シンセ研究会", "舞ヶ原高校軽音部", "HaNaMiNa",
]

_PUNCT = (r"[\s\u3000・、。，,．.!！?？~～〜ー\-‐‑–—―−「」『』【】（）()\[\]{}｛｝"
          r"×✕✖⤫⤴⤵/／＼\\&＆+＋:：;；'\"”’‘`´*＊#＃@＠＄$％%＾^＝=｜|＜＞]")
_PUNCT_RE = re.compile(_PUNCT)


def normalize(title):
    return _PUNCT_RE.sub("", unicodedata.normalize("NFKC", title or "")).casefold()


def load_data(game, cache):
    path = os.path.join(cache, game + ".json")
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)["songs"]
    os.makedirs(cache, exist_ok=True)
    print(f"下载 {game} ...", file=sys.stderr)
    request = Request(URL % game, headers=HEADERS)
    raw = urlopen(request, timeout=60).read()
    with open(path, "wb") as f:
        f.write(raw)
    return json.loads(raw)["songs"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-o", "--output", help="输出 JSON 路径")
    parser.add_argument("--music", default=os.path.join(ROOT, "data", "maimai", "music.json"),
                        help="maimai music.json 路径")
    parser.add_argument("--cache", default=os.path.join(tempfile.gettempdir(), "maimai-collab-data"),
                        help="各游戏 data.json 的缓存目录")
    args = parser.parse_args()

    with open(args.music, encoding="utf-8") as f:
        musics = json.load(f)

    result = {}
    for game in GAMES:
        pool = {normalize(s["title"]) for s in load_data(game, args.cache)
                if ORIG[game](s.get("category"))}
        result[game] = sorted(m["id"] for m in musics
                              if m["genre"] == SCOPE[game] and normalize(m["name"]) in pool)
    for game, extra in SPECIAL.items():
        result[game] = sorted(set(result[game]) | set(extra))

    names = [normalize(n) for n in IRODORI_NAMES]
    result["irodori"] = sorted(
        m["id"] for m in musics
        if m["genre"] == "オンゲキCHUNITHM"
        and any(n in normalize(m["artist"]) for n in names))

    for key in GAMES + ["irodori"]:
        print("%-9s %3d" % (key, len(result[key])), file=sys.stderr)

    text = json.dumps(result, ensure_ascii=False, indent=1) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        print("→ %s" % args.output, file=sys.stderr)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
