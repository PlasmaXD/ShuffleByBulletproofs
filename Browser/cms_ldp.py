# cms_ldp.py

import hashlib
import math
import random


class CMS_LDP_Client:
    """
    クライアント側：URL を Count–Min Sketch の d×w ビット空間にマッピングし、
    元の「1ビット」を IRR（瞬間ランダム応答）で乱数化して返却します。
    """

    def __init__(self, width: int, depth: int, prob_p: float = 0.5, prob_q: float = 0.75):
        """
        :param width: Sketch の列数（バケット数）
        :param depth: Sketch の行数（ハッシュ関数の数）
        :param prob_p: IRR の 0→1 誤陽性確率
        :param prob_q: IRR の 1→1 真陽性確率
        """
        self.w = width
        self.d = depth
        self.p = prob_p
        self.q = prob_q

    def _hash(self, url: str, i: int) -> int:
        """
        行インデックス i 用のハッシュ関数：
        MD5(url + i) を用い、0..w-1 にマップ
        """
        data = url.encode("utf-8") + i.to_bytes(2, "big")
        return int(hashlib.md5(data).hexdigest(), 16) % self.w

    def privatize(self, url: str) -> list[tuple[int,int,int]]:
        """
        :param url: エンドポイント URL
        :return: List[ (row, col, bit) ] — 各行 row, 列 col, IRR で乱数化した 0/1
        """
        rec = []
        for i in range(self.d):
            col = self._hash(url, i)
            # 本来のビット x = 1（このバケットだけ）
            x = 1
            # IRR: x=1 のとき 1 を出力する確率 q、0 を出す確率 1-q
            # IRR: x=0 のとき 1 を出す確率 p、0 を出す確率 1-p
            prob = self.q if x == 1 else self.p
            b = 1 if random.random() < prob else 0
            rec.append((i, col, b))
        return rec


class CMS_LDP_Aggregator:
    """
    サーバー側：クライアントからの非同期レコードを受け取り、
    Count–Min Sketch を累積→逆ノイズ化→URL 頻度推定を行います。
    """

    def __init__(self, width: int, depth: int, prob_p: float = 0.5, prob_q: float = 0.75):
        """
        :param width: クライアントと同じ Sketch の列数
        :param depth: クライアントと同じ Sketch の行数
        :param prob_p: クライアント側と同じ IRR パラメータ
        :param prob_q: クライアント側と同じ IRR パラメータ
        """
        self.w = width
        self.d = depth
        self.p = prob_p
        self.q = prob_q
        # 行×列 の累積スケッチ
        self.sketch = [[0]*self.w for _ in range(self.d)]
        self.N = 0  # ユーザーレコード数

    def ingest(self, record: list[tuple[int,int,int]]):
        """
        クライアント record を受け取って Sketch に加算
        :param record: CMS_LDP_Client.privatize() の戻り値
        """
        for i, col, b in record:
            self.sketch[i][col] += b
        self.N += 1

    def _hash(self, url: str, i: int) -> int:
        # クライアントと同じハッシュ実装
        data = url.encode("utf-8") + i.to_bytes(2, "big")
        return int(hashlib.md5(data).hexdigest(), 16) % self.w

    def estimate_url(self, url: str) -> float:
        """
        URL の出現回数を推定
        スケッチ内の該当バケットを参照し、
        逆ノイズ化した上で "min" を取る
        """
        estimates = []
        for i in range(self.d):
            col = self._hash(url, i)
            y_hat = self.sketch[i][col] / self.N  # 観測1割合
            # 線形逆変換
            f_hat = (y_hat - self.p) / (self.q - self.p)
            # 負値防止
            estimates.append(max(f_hat * self.N, 0))
        # 最小値を返すことで Count–Min Sketch のバイアスを軽減
        return min(estimates)


if __name__ == "__main__":
    # --- 動作例 ---
    urls = [
        "https://example.com/page1",
        "https://example.com/page2",
        "https://another-site.org/foo",
        "https://example.com/page1",
        "https://example.com/page1",
    ]

    # クライアント／集計サーバー設定
    WIDTH, DEPTH = 128, 4
    P, Q = 0.5, 0.75

    client = CMS_LDP_Client(WIDTH, DEPTH, prob_p=P, prob_q=Q)
    aggregator = CMS_LDP_Aggregator(WIDTH, DEPTH, prob_p=P, prob_q=Q)

    # 各 URL についてクライアントで privatize → サーバーで ingest
    for url in urls:
        rec = client.privatize(url)
        aggregator.ingest(rec)

    # 推定結果表示
    for u in set(urls):
        est = aggregator.estimate_url(u)
        print(f"{u} の推定出現回数: {est:.1f}")

    # 実際の出現回数表示
    from collections import Counter
    cnt = Counter(urls)
    print("\n実際の出現回数")
    for u, c in cnt.items():
        print(f"{u}: {c}")
