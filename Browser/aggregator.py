# aggregator.py
import numpy as np
from scipy.optimize import nnls        # NNLSで非負最小二乗法を解くための関数 :contentReference[oaicite:4]{index=4}
import rappor                           # RAPPORのParamsやエンコーダ :contentReference[oaicite:5]{index=5}
import json

def load_reports(filepath):
    """履歴ファイルから cohort と IRR を読み込む"""
    reports = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split()
            cohort = int(parts[2].split('=')[1])
            irr    = int(parts[3].split('=')[1])
            reports.append({'cohort': cohort, 'irr': irr})
    return reports

def decode_irr_to_bits(reports, k):
    """
    各 IRR 整数を k ビットのビット列に展開
    例: format(40005, '016b')
    """
    M = len(reports)
    B = np.zeros((M, k), dtype=int)
    for i, r in enumerate(reports):
        bit_str = format(r['irr'], f'0{k}b')
        B[i] = np.array(list(map(int, bit_str)))
    return B

def aggregate_bits(B):
    """行列 B からビットごとの 1 の個数を集計"""
    return np.sum(B, axis=0)

def denoise_counts(counts, N, p, q):
    """
    観測ビット頻度 y = counts/N に対し、
    f = (y - p) / (q - p) の線形逆変換を適用 :contentReference[oaicite:6]{index=6}
    """
    y = counts / N
    return (y - p) / (q - p)

def bloom_filter_matrix(candidates, k):
    """
    各候補文字列をコホート 0 とみなして Bloom フィルタ化した行列を作成
    実運用では各 cohort ごとに行列を別途構築して混合も可能 :contentReference[oaicite:7]{index=7}
    """
    params = rappor.Params()
    params.num_bloombits = k
    # 簡易化のため cohort=0 固定
    cohort = 0
    secret = f"secret_key_{cohort}".encode('utf-8')
    irr_rand = rappor.SecureIrrRand(params)
    # 各候補のビット配列を列ベクトルとして積み上げ
    cols = []
    for url in candidates:
        encoder = rappor.Encoder(params, cohort, secret, irr_rand)
        bits_int = encoder._internal_encode(url.encode('utf-8'))[0]  # Bloomビット列 (整数) :contentReference[oaicite:8]{index=8}
        bits = np.array(list(map(int, format(bits_int, f'0{k}b'))))
        cols.append(bits)
    return np.vstack(cols).T  # shape: (k, num_candidates)

def estimate_frequencies(bit_freqs, A):
    """
    行列 A と観測ビット頻度 bit_freqs に対し、
    nnls で x>=0 の線形回帰を解く :contentReference[oaicite:9]{index=9}
    """
    x, rnorm = nnls(A, bit_freqs)
    return x

def main():
    # パラメータ設定
    filepath    = 'history.txt'
    candidates_file = 'candidates.txt'
    k = 16            # Bloomフィルタ長 :contentReference[oaicite:10]{index=10}
    p, q = 0.5, 0.75  # RAPPOR IRR パラメータ :contentReference[oaicite:11]{index=11}

    # 1. レポート読み込み・ビット変換・集計
    reports = load_reports(filepath)
    B       = decode_irr_to_bits(reports, k)
    counts  = aggregate_bits(B)

    # 2. ノイズ逆変換でビット頻度を推定
    bit_freqs = denoise_counts(counts, len(reports), p, q)

    # 3. 候補URL行列を生成
    with open(candidates_file, 'r', encoding='utf-8') as f:
        candidates = [u.strip() for u in f if u.strip()]
    A = bloom_filter_matrix(candidates, k)

    # 4. NNLS で頻度推定
    freqs = estimate_frequencies(bit_freqs, A)

    # 結果表示
    result = {url: float(freq) for url, freq in zip(candidates, freqs)}
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
