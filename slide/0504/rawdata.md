思考時間: 2 ～ 3 秒


本番運用では、以下のように「生データ」と「集計用データ」を分離し、かつ厳重に保護するのが一般的です。

---

## 1. 生データの安全な配置場所

1. **暗号化ストレージ**

   * 生データ（`history.txt` 相当）は、ディスクやオブジェクトストレージ上に平文で置かず、必ず\*\*サーバー側で暗号化（AES-GCM など）\*\*して保存します。
   * たとえば AWS であれば S3 バケットに SSE-KMS（キー管理サービス）を使う、GCP なら Cloud Storage の CMEK を使う、といった具合です。

2. **アクセス制御／IAM ロール**

   * アプリケーションからしか読み書きできないように、**最小権限の IAM ロール**・サービスアカウントを振り分けます。
   * ヒューマンオペレータ向けにはさらに別レイヤーで MFA＋監査ログを必須に。

3. **ネットワーク分離**

   * 生データ保存用サーバーはパブリックネットワークから切り離し、アプリケーションサーバーや集計サーバーからのみ VPC 内通信でアクセス可能にします。

4. **ローテーションと監査**

   * 定期的に古いログを処分（Secure Delete）し、KMS キーのローテーション設定。
   * 誰がいつ生データを操作したかを**監査ログ**（Audit Trail）に残す。

---

## 2. 集計結果の精度評価方法

RAPPOR ＋ CMS-LDP のようなノイズ付き集計では、**実データに対する推定誤差**を定量的に評価することが重要です。以下のステップで行います。

1. **実データから「真のカウント」を算出**

   ```python
   # raw_history.txt から真の頻度をカウント
   from collections import Counter
   true_cnt = Counter()
   with open("history.txt") as f:
       for line in f:
           ts, url = line.strip().split(" ", 1)
           true_cnt[url] += 1
   ```

2. **推定結果を取得**

   ```python
   est_cnt = {}
   for url in true_cnt:
       est_cnt[url] = aggregator.estimate_url(url)
   ```

3. **誤差指標を計算**

   ```python
   import numpy as np

   eps = []
   rel = []
   for url in true_cnt:
       t = true_cnt[url]
       e = est_cnt[url]
       eps.append(abs(e - t))              # 絶対誤差
       if t > 0:
           rel.append(abs(e - t) / t)      # 相対誤差
   print("平均絶対誤差(MAE):", np.mean(eps))
   print("平均相対誤差(MAPE):", np.mean(rel) * 100, "%")
   ```

   * **MAE**: Mean Absolute Error
   * **MAPE**: Mean Absolute Percentage Error
   * 必要に応じて **RMSE**（二乗平均平方根誤差） も計算できます。

4. **サンプル数の影響を見る**

   * データ件数を増減させて、誤差がどの程度変わるかグラフ化すると、必要なサンプルサイズの目安が立ちます。

---

### まとめ

* **生データ** は「暗号化＋アクセス制御＋ネットワーク分離」で厳重に管理し、直接扱う人・サービスを限定します。
* **精度評価** は真のカウントと推定値を比較し、MAE／MAPE／RMSE など標準的な指標で誤差を定量化することで行います。

この方法で、運用上のセキュリティ要件を満たしつつ、集計精度を体系的にモニタリングできます。もし「可視化したい」「自動レポートに組み込みたい」といった要望があれば、さらにダッシュボード化や CI テストへの組み込みも検討してみてください。
