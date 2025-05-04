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
            # "ワンホット" 全バケット分をランダム化
            for j in range(self.w):
                x = 1 if j == col else 0
                prob = self.q if x == 1 else self.p
                b = 1 if random.random() < prob else 0
                rec.append((i, j, b))
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

    # --- 各種パラメータ ---
    WIDTH, DEPTH = 128, 4
    P, Q = 0.5, 0.75
    # WIDTH, DEPTH = 128, 4
    # P, Q = 0.0, 1.0   # p=0, q=1 とすると IRR のノイズが消え、正確にカウントできます
    client     = CMS_LDP_Client(WIDTH, DEPTH, prob_p=P, prob_q=Q)
    aggregator = CMS_LDP_Aggregator(WIDTH, DEPTH, prob_p=P, prob_q=Q)

    # 1) 履歴ファイルから実際に訪れた URL を読み込む
    visited_urls = []
    with open('history.txt', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # date, time, url に分割
            parts = line.split(' ', 2)
            if len(parts) < 3:
                continue
            url = parts[2]   # これで先頭のタイムスタンプ2つを飛ばし、純粋な URL 部分だけ取得
            visited_urls.append(url)

    # 2) CMS+LDP の ingest 処理
    for url in visited_urls:
        rec = client.privatize(url)
        aggregator.ingest(rec)

    # 3) 推定結果を出力（重複を除いて一度だけクエリ）
    unique_urls = set(visited_urls)
    for url in unique_urls:
        est = aggregator.estimate_url(url)
        print(f"{url} の推定出現回数: {est:.1f}")

    # （オプション）実際のカウントも並べて確認
    from collections import Counter
    cnt = Counter(visited_urls)
    print("\n実際の出現回数")
    for url, c in cnt.items():
        print(f"{url}: {c}")
