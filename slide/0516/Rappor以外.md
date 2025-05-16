以下の４つはすべて **ローカル Differential Privacy（Local DP）** の下でユーザーの生データを秘匿しつつ、**集団の頻度分布**や**カテゴリ分布**を推定するための代表的なプロトコルです。それぞれが異なるエンコード・乱択手法を採用し、**精度**・**通信量**・**計算コスト**・**ドメインサイズ対応**を最適化しています。

* **RAPPOR**：Bloom フィルタ＋二段階ランダム化による文字列集計 ([arXiv][1], [GitHub][2])
* **OLH**（Optimal Local Hashing）：大規模ドメインを小ドメインにハッシュ圧縮 ＋ 乱択 ([SpringerOpen][3], [Usenix][4])
* **OUE**（Optimized Unary Encoding）：ワンホット符号化＋最適パラメータによるビット翻転 ([Usenix][4], [ScienceDirect][5])
* **HR**（Hadamard Response）：Hadamard 変換を利用し、低通信コストかつ高速推定 ([arXiv][6], [people.ece.cornell.edu][7])

---

## RAPPOR

**Randomized Aggregatable Privacy-Preserving Ordinal Response** の略称で、Google が提案した文字列収集メカニズムです。

1. **Bloom フィルタ化**：文字列を複数ハッシュでビット配列にエンコード
2. **PRR**（Permanent Randomized Response）：永続的にビットを確率的反転し固有ノイズを導入
3. **IRR**（Instantaneous Randomized Response）：報告時に再び確率的反転
4. **サーバー推定**：多数報告を集約し、事前定義の辞書内の文字列 Bloom 表現と EM 法などで一致度を逆推定

* クライアント数千万規模で実運用例あり（Chrome 設定値収集、Windows プロセス名収集） ([arXiv][1], [DBLP][8])
* 各クライアント報告は個別特定不可能で、集団統計のみ高精度に取得可能 ([Google Research][9], [GitHub][2])

---

## OLH（Optimal Local Hashing）

大規模カテゴリを扱う際の周波数推定プロトコル。

1. クライアントは真の値をハッシュ関数で小ドメイン $\{1,\dots,g\}$ に写像
2. そのハッシュ値に対してランダム応答を実施
3. サーバーは受信乱択値の分布から元の頻度を逆推定

* パラメータ $g=e^{\varepsilon}+1$ のとき情報損失とノイズのトレードオフが最適化される ([SpringerOpen][3], [Cryptology ePrint Archive][10])
* 通信コストは $\log g$ ビット、計算コストも低く抑えられる ([Usenix][4], [VLDB][11])

---

## OUE（Optimized Unary Encoding）

ワンホット（Unary）エンコードをベースに、最適パラメータでビットをフリップする方式。

1. 値 $v\in\{1,\dots,k\}$ を長さ $k$ のワンホットベクトルに変換
2. 各ビットを確率的にフリップ：

   * 元が1なら確率 $q=\tfrac12$ で1を報告
   * 元が0なら確率 $p=\tfrac{1}{e^{\varepsilon}+1}$ で1を報告
3. サーバーは各ビットの観測割合を補正し周波数を推定

* 通信コストは $k$ ビット（中規模ドメイン向け） ([Usenix][4], [Usenix][12])
* パラメータ最適化で GRR や RAPPOR を上回る精度を実現 ([ScienceDirect][5])

---

## HR（Hadamard Response）

高速かつ低通信量な分布推定のため、Hadamard 行列を活用したプロトコル。

1. 入力ベクトルを Hadamard 変換し、行列の行インデックスをサンプリング
2. 対応する Hadamard 係数を確率的に乱択
3. サーバーは受信係数を高速 Walsh–Hadamard 逆変換で全ドメインの頻度を推定

* 通信量は $\log k + 2$ ビット、計算量は $\tilde O(n+k)$ で非常に効率的 ([arXiv][6], [people.ece.cornell.edu][7])
* 大規模ドメインで OLH/OUE 同等の精度を保ちつつ、数十倍の高速化を実現 ([VLDB][13], [Cryptology ePrint Archive][10])

---

これらのプロトコルは、用途やドメインサイズ、通信・計算コスト要件に応じて使い分けることで、Local DP 下でも高精度な統計推定を可能にします。

[1]: https://arxiv.org/abs/1407.6981?utm_source=chatgpt.com "RAPPOR: Randomized Aggregatable Privacy-Preserving Ordinal Response"
[2]: https://github.com/google/rappor?utm_source=chatgpt.com "google/rappor - Privacy-Preserving Reporting Algorithms - GitHub"
[3]: https://jwcn-eurasipjournals.springeropen.com/articles/10.1186/s13638-020-01675-8?utm_source=chatgpt.com "Local differential privacy for human-centered computing"
[4]: https://www.usenix.org/system/files/conference/usenixsecurity17/sec17-wang-tianhao.pdf?utm_source=chatgpt.com "[PDF] Locally Differentially Private Protocols for Frequency Estimation"
[5]: https://www.sciencedirect.com/science/article/pii/S2352864822001444?utm_source=chatgpt.com "Improving the utility of locally differentially private protocols for ..."
[6]: https://arxiv.org/abs/1802.04705?utm_source=chatgpt.com "Hadamard Response: Estimating Distributions Privately, Efficiently, and with Little Communication"
[7]: https://people.ece.cornell.edu/acharya/talks/ita-18.pdf?utm_source=chatgpt.com "[PDF] Hadamard Response: Local Private Distribution Estimation"
[8]: https://dblp.org/rec/conf/ccs/ErlingssonPK14?utm_source=chatgpt.com "Randomized Aggregatable Privacy-Preserving Ordinal Response."
[9]: https://research.google.com/pubs/archive/42852.pdf?utm_source=chatgpt.com "[PDF] RAPPOR: Randomized Aggregatable Privacy-Preserving Ordinal ..."
[10]: https://eprint.iacr.org/2024/1464.pdf?utm_source=chatgpt.com "[PDF] SoK: Descriptive Statistics Under Local Differential Privacy"
[11]: https://www.vldb.org/pvldb/vol12/p1126-cormode.pdf?utm_source=chatgpt.com "[PDF] Answering Range Queries Under Local Differential Privacy"
[12]: https://www.usenix.org/conference/usenixsecurity17/technical-sessions/presentation/wang-tianhao?utm_source=chatgpt.com "Locally Differentially Private Protocols for Frequency Estimation"
[13]: https://vldb.org/pvldb/vol14/p2046-cormode.pdf?utm_source=chatgpt.com "[PDF] Frequency Estimation under Local Differential Privacy"
以下のまとめのとおり、**用途やドメインサイズに応じて**直接的な LDP プロトコル（OLH, OUE, HR）だけで十分な場合と、**非常に大規模ドメインや最悪誤差保証が必要な場合**に Count–Min Sketch（CMS）やその拡張版が依然として必要になる場合がある、という結論になります。

> **要点サマリ**
>
> * Optimized Local Hashing (OLH), Optimized Unary Encoding (OUE) などのプロトコルは、クライアント側でワンショットのハッシュ／エンコード＋乱択を行うことで、サーバーが直接頻度を推定でき、CMS を明示的に構築する必要がない ([ウォーリック大学][1], [Usenix][2])。
> * しかし、Pan et al. (2024) はこれらの LDP アルゴリズムがパラメータの異なる「Private Count–Mean Sketch（CMS）」と数学的に同等であり、大規模辞書に対して最悪誤差（MSE, L1, L2）最小化の最適アルゴリズムが CMS であることを示している ([arXiv][3])。
> * 中規模ドメイン（数十～数百程度）では OLH/OUE などを使うだけで十分ですが、**非常に大きなドメイン**や**最悪誤差保証**が求められる場合には CMS が必要となるケースがある ([VLDB][4], [ウォーリック大学][1])。
> * また、PrivSketch や学習型スケッチなどのハイブリッド手法は、**Heavy Hitters を分離しつつ残りを CMS で扱う**ことで、LDP 下でも大規模データに対する精度を確保している ([arXiv][5], [arXiv][6])。

---

## 1. 高度な直接周波数オラクル（CMS不要のケース）

* **Optimized Local Hashing (OLH)**：
  ユーザーはデータ値を一つのハッシュ値に変換し、そのハッシュを確率的に乱択して送信します。サーバーは乱択モデルを逆算して周波数を推定し、Sketch 構築は不要です ([Usenix][2])。
* **Optimized Unary Encoding (OUE)**：
  値をワンホットベクトルに変換し、各ビットを一定確率でフリップして送信。サーバーは各ビットの観測割合を補正するだけで周波数が得られ、Sketch 操作は含まれません ([ウォーリック大学][1])。

---

## 2. Private CMS が裏で最適構造である理由

* **等価性の証明**：Pan et al. (2024) は、OLH や OUE、Hadamard Response など多くの最先端 LDP 周波数推定法が、\*\*パラメータ設定を変えた Private Count–Mean Sketch（CMS）\*\*と同値であると示しました ([arXiv][3])。
* **最悪誤差最小化**：最適化された CMS は、非常に大きな辞書を扱う際の最悪ケース MSE、\$L\_1\$、\$L\_2\$ 損失を理論的かつ経験的に最小化することが証明されています ([arXiv][3])。

---

## 3. ハイブリッド・学習型スケッチの活用例

* **Learned Sketch**：データドメインを頻出アイテム（Heavy Hitters）と残りに分割し、Heavy Hitters は直接推定、残りは CMS で扱う二相フレームワークにより、衝突誤差を低減します ([arXiv][5])。
* **PrivSketch**：背景に Sketch を維持しつつクライアント側で初回デコードを行う「decode-first」ワークフローを組み合わせ、スケッチとノイズ誤差の両方を抑制するプロトコルです ([arXiv][6])。

---

## 4. いつ CMS が必要か

* **小～中規模ドメイン**（数十～数百要素）：OLH, OUE, HR などの直接オラクルのみで十分運用可能です。
* **大～極大規模ドメイン**（数万～数百万要素以上）や **最悪ケース誤差保証** を重視する場合：Private CMS または学習・階層型 Sketch が最適な構造として必要になります ([arXiv][3])。
* **実装上のポイント**：OpenDP や Google Differential Privacy Library、IBM Diffprivlib などの LDP ライブラリでは、これら最適オラクルや Private CMS の実装を内部に隠蔽しており、開発者はプライバシー予算とクエリタイプを設定するだけで利用できます ([VLDB][4])。

---

**結論**：

* 中小規模ドメインなら OLH/OUE 等だけで CMS は不要ですが、非常に大きなドメインや最悪誤差保証を要する場面では、Pan et al. が示すように CMS（またはその最適化版）が依然として理論的に必須です。
* 実際の開発では、上記の LDP ライブラリを使えば「CMS を自前で組む」必要はほとんどありませんが、その裏側で Private CMS が動作しているケースも多い点を押さえておくと理解が深まります。

[1]: https://warwick.ac.uk/fac/sci/dcs/people/u1714078/vldb21_15m.pdf?utm_source=chatgpt.com "[PDF] Frequency Estimation under Local Differential Privacy [Experiments ..."
[2]: https://www.usenix.org/system/files/conference/usenixsecurity17/sec17-wang-tianhao.pdf?utm_source=chatgpt.com "[PDF] Locally Differentially Private Protocols for Frequency Estimation"
[3]: https://arxiv.org/abs/2406.03785?utm_source=chatgpt.com "Count-mean Sketch as an Optimized Framework for Frequency Estimation with Local Differential Privacy"
[4]: https://vldb.org/pvldb/vol14/p2046-cormode.pdf?utm_source=chatgpt.com "[PDF] Frequency Estimation under Local Differential Privacy"
[5]: https://arxiv.org/abs/2211.01138?utm_source=chatgpt.com "Local Differentially Private Frequency Estimation based on Learned Sketches"
[6]: https://arxiv.org/abs/2306.12144?utm_source=chatgpt.com "PrivSketch: A Private Sketch-based Frequency Estimation Protocol for Data Streams"
