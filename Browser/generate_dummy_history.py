import random
from datetime import datetime, timedelta
import os

# RAPPOR dummy encoder (simplified, no real privacy protection here)
def encode_url_rappor_dummy(url, num_cohorts=64, num_bloombits=16):
    # Dummy: cohort random, irr = hash(url) % 2**num_bloombits
    cohort = random.randint(0, num_cohorts-1)
    irr = hash(url) & ((1 << num_bloombits) - 1)
    return cohort, irr

# Configuration
num_entries = 1000  # 作成したいダミー履歴の件数
start_time = datetime(2025, 5, 1, 0, 0, 0)
urls = [
    "https://example.com/page1",
    "https://example.com/page2",
    "https://another-site.org/foo",
    "https://news.yahoo.co.jp/search?p=test",
    "https://www.google.com/search?q=privacy",
    "https://www.newsweekjapan.jp/stories/world/2025/05/549455.php"
]

# 出力ファイルパス
raw_path = "history_dummy.txt"
enc_path = "encoded_history_dummy.txt"

# 古いファイルがあれば削除
for p in (raw_path, enc_path):
    if os.path.exists(p):
        os.remove(p)

current_time = start_time
with open(raw_path, "w", encoding="utf-8") as f_raw, open(enc_path, "w", encoding="utf-8") as f_enc:
    for _ in range(num_entries):
        # ランダムに時間を進める
        delta = timedelta(seconds=random.randint(10, 300))
        current_time += delta

        # ランダムURLを選択
        url = random.choice(urls)
        ts = current_time.strftime("%Y-%m-%d %H:%M:%S")

        # 生URLをhistory_dummy.txtに書き込む
        f_raw.write(f"{ts} {url}\n")

        # RAPPORエンコード結果をencoded_history_dummy.txtに書き込む
        cohort, irr = encode_url_rappor_dummy(url)
        f_enc.write(f"{ts} cohort={cohort} irr={irr}\n")

# 完了メッセージ
print(f"Generated {num_entries} entries:")
print(f"- Raw history -> {raw_path}")
print(f"- Encoded history -> {enc_path}")
