---

marp: true
title: CMS × LDP で頻度推定
description: Count–Min Sketch とローカル差分プライバシの組み合わせ概説
paginate: true
theme: default
header: "CMS × LDP"
footer: "村瀬淳 — 2025/05/04"
--------------------------

# Count–Min Sketch × Local DP

大規模ストリームで**プライバシを保ちつつ頻度を推定**する軽量フレームワーク。

* **固定サイズ**スケッチでメモリ効率◎
* 各ユーザーが **ε‑ローカル差分プライバシ** を満たすランダム化を実施
* サーバは合計だけ保持し⏩ 個人データは不明

---

## なぜ必要？

| 従来手法        | 課題             |
| ----------- | -------------- |
| 生データ集中収集    | プライバシ侵害リスク     |
| サーバ側差分プライバシ | 信頼されたカスタマイズが前提 |

> **CMS×LDP** は「個々の端末でランダム化 → 集約はSketch」の合わせ技で
> *プライバシ*と*効率*を両立。

---

## Count–Min Sketch (CMS)

* 行 \$d\$ × 列 \$w\$ の **ハッシュ行列**
* 挿入: 各行の \$h\_i(x)\$ バケットを `+1`
* クエリ: 対応セルの **最小値** が推定頻度
* 誤差上界: \$\varepsilon \approx \frac{1}{w}\$，失敗確率 \$\delta \approx e^{-d}\$

---

### CMS の利点

* **\$O(d)\$** 更新／クエリ
* メモリは \$O(d\times w)\$ — 大規模でも小さく抑えられる
* ストリーム順序に依存しない

---

## ローカル差分プライバシ (LDP)

* 乱択化機構 \$\mathcal A\$ が
  \$\Pr\[\mathcal A(x)=y]\le e^{\varepsilon}\Pr\[\mathcal A(x')=y]\$
* 代表例: **ランダム化応答 (RR)**
* ユーザー側だけで完結 → サーバを信頼しなくてOK

---

## クライアント側処理

1. アイテム \$x\$ を \$d\$ 個のハッシュで位置決定
2. 各行で「送信ビット=1」を **RR** でノイズ付与

   * 真ビットなら確率 \$q\$ で 1
   * 偽ビットなら確率 \$p\$ で 1
3. $d$ ビット送信 → 通信量は定数

---

## サーバ側処理

1. 受信ビットを対応セルに **加算**
2. ユーザー数 \$N\$ で正規化し観測率 \$\hat y\$
3. 逆変換: \$\hat f = (\hat y - p)/(q-p)\$
4. 各行の推定値の **min** が最終頻度

---

## 保証と誤差分析

* **プライバシ**: 各ビットが \$\varepsilon\$‑LDP
* **期待誤差**:
  \$\text{bias}*{CMS} + \text{noise}*{LDP}\$
* パラメータ例:
  \$\varepsilon=1,\ d=5,\ w=\lceil e/\varepsilon \rceil\$ で
  数百万ユーザーでも誤差 <1%

---

## 実運用例

* **Apple iOS** 絵文字・語彙統計 (\[Apple ML Research 2017])
* 広告クリック率集計
* IoT ログ頻度解析 など

---

## 参考文献

1. Apple ML Research “Learning with Privacy at Scale” 2017
2. Cormode et al. “Frequency Estimation under LDP” PVLDB 2021
3. Cormode et al. “Answering Range Queries under LDP” PVLDB 2019
4. Zhao et al. “Differentially Private Linear Sketches” NeurIPS 2022
5. GeeksforGeeks “Count‑Min Sketch in Java/Python” 2023
6. ACM DL article “Frequency estimation under LDP” 2021

---

# ご清聴ありがとうございます
