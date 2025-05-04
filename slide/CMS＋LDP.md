
## 概要

Count–Min Sketch (CMS) は幅 $w$、深さ $d$ の行列を使ってストリーム内の要素頻度を近似的に推定するデータ構造です ([ウィキペディア][1])。
ローカル差分プライバシ (LDP) では各クライアントが送信前にランダム化応答（RR）を適用し、中央集約者に生データを明かさずに ε-DP を保証します ([VLDB][2])。
CMS×LDP ではクライアント側で CMS のワンホット位置に RR を適用し、サーバ側で累積カウンタから線形逆変換を行って頻度を推定します ([Apple Developer Documentation][3])。
この組み合わせにより、**固定サイズメモリ**と**クライアントのみのノイズ付与**で大規模ストリームのプライバシ保護付き頻度推定が可能になります ([VLDB][2])。

---

## 1. Count–Min Sketch の定義

### 1.1 データ構造

* CMS は行数 $d$、列数 $w$ の非負整数行列 $\mathbf{C}\in\mathbb{N}^{d\times w}$ を維持します ([ウィキペディア][1])。
* 各行 $\ell=1,\dots,d$ にはペアワイズ独立なハッシュ関数 $h_\ell: \mathcal{U}\to \{0,\dots,w-1\}$ を割り当て、要素 $x$ の到着時に

  $$
    C[\ell,h_\ell(x)] \leftarrow C[\ell,h_\ell(x)] + 1
  $$

  と更新します ([ウィキペディア][1])。

### 1.2 点クエリと誤差保証

* クエリ $x$ に対する推定値は

  $$
    \hat f(x) \;=\; \min_{\ell=1..d} C\bigl[\ell,\,h_\ell(x)\bigr]
  $$

  で与えられ、真値 $f(x)\le\hat f(x)$ が成り立ちます ([ウィキペディア][1])。
* 誤差境界として

  $$
    \Pr\bigl[\hat f(x) > f(x) + \varepsilon N \bigr] < \delta,\quad
    \text{where } \varepsilon = \frac{1}{w},\;\delta = e^{-d}
  $$

  が保証されます ([VLDB][2])。

---

## 2. ローカル差分プライバシ (LDP) の定義

### 2.1 ε-LDP

* メカニズム $\mathcal{A}$ が入力 $x$ を確率的に出力 $y$ にマップするとき、任意の $x,x'$ と $y$ に対し

  $$
    \Pr[\mathcal{A}(x)=y]\;\le\; e^{\varepsilon}\,\Pr[\mathcal{A}(x')=y]
  $$

  を満たすと ε-LDP と呼びます ([VLDB][2])。

### 2.2 ランダム化応答（Randomized Response, RR）

* ビット $b\in\{0,1\}$ を

  $$
    \Pr[\text{出力}=1\mid b=1]=q,\quad
    \Pr[\text{出力}=1\mid b=0]=p
  $$

  で返し、プライバシ損失は
  $\varepsilon = \ln\!\bigl(\tfrac{q(1-p)}{p(1-q)}\bigr)$ となります ([thesequence.substack.com][4])。

---

## 3. CMS × LDP の結合手順

### 3.1 クライアント側

1. 要素 $x$ に対し各行 $\ell$ のハッシュ位置 $h_\ell(x)$ を計算
2. その位置のワンホットベクトルに対し、RR を適用してビット列 $\{b_{\ell,j}\}$ を生成
3. $\{(\ell,j,b_{\ell,j})\}$ をサーバへ送信（通信量 $O(d)$） ([Apple Developer Documentation][3])。

### 3.2 サーバー側

1. 受信した各クライアントビットを対応するセルに加算し、総スケッチ $\mathbf{C}$ を更新
2. N 件のレコード後、クエリ要素 $x$ について各行の観測比
   $\hat y_\ell = C[\ell,h_\ell(x)]/N$ を計算
3. 逆変換
   $\hat f_\ell = (\hat y_\ell - p)/(q - p)$
   を行い、最終推定値
   $\hat f(x) = \min_\ell \hat f_\ell\cdot N$
   を返します ([VLDB][2])。

---

## 4. 実例と応用

### 4.1 Apple iOS の絵文字統計

Apple は「Private Count Mean Sketch」を用いてユーザーの絵文字使用頻度を収集し、ε-LDP を実現しています ([arXiv][5])。

### 4.2 大規模ログ・IoT データ

ストリーミングトラフィックや IoT データの頻度解析にも CMS×LDP が応用され始めています ([サイエンスダイレクト][6])。

---

## 5. 改善と拡張

### 5.1 通信量の最適化

ワンホット全幅ではなく「ハッシュ位置 $\ell$ のみ」を RR し、クライアント／サーバ間通信量を $O(d)$ に削減できます ([Redis][7])。

### 5.2 Gaussian 機構による集中差分プライバシ

各カウンタ初期化時にガウスノイズを加え、集中差分プライバシ（zCDP）を保証する手法も提案されています ([arXiv][8])。

---

以上が Count–Min Sketch とローカル差分プライバシの数式を交えた詳細な解説です。実装やパラメータ設計の参考にしてください。

[1]: https://en.wikipedia.org/wiki/Count%E2%80%93min_sketch?utm_source=chatgpt.com "Count–min sketch"
[2]: https://vldb.org/pvldb/vol14/p2046-cormode.pdf?utm_source=chatgpt.com "[PDF] Frequency Estimation under Local Differential Privacy"
[3]: https://docs-assets.developer.apple.com/ml-research/papers/learning-with-privacy-at-scale.pdf?utm_source=chatgpt.com "[PDF] Learning with Privacy at Scale - Apple"
[4]: https://thesequence.substack.com/p/-edge31-differential-privacy?utm_source=chatgpt.com "🔊 Edge#31: Differential Privacy - by Ksenia Se - TheSequence"
[5]: https://arxiv.org/pdf/2205.08397?utm_source=chatgpt.com "[PDF] Improved Utility Analysis of Private CountSketch - arXiv"
[6]: https://www.sciencedirect.com/science/article/abs/pii/S0020025523012525?utm_source=chatgpt.com "Local differentially private frequency estimation based on learned ..."
[7]: https://redis.io/blog/count-min-sketch-the-art-and-science-of-estimating-stuff/?utm_source=chatgpt.com "Count-Min Sketch: The Art and Science of Estimating Stuff | Redis"
[8]: https://arxiv.org/pdf/2205.09873?utm_source=chatgpt.com "[PDF] Differentially Private Linear Sketches - arXiv"
