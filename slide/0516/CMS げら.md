


---

 # **Count-Min Sketch (CMS)** の数理的仕組み 
 
‐ *N* = ストリーム総件数 
‐ *ε* = 許容相対誤差 
‐ *δ* = 失敗確率 

---

## 1  データ構造

| 深さ | 行数 *d* | $\lceil\ln(1/δ)\rceil$ 行 |
| -- | ------ | ------------------------ |
| 幅  | 列数 *w* | $\lceil e/ε\rceil$ 列     |

*d × w* の整数表を持ち、各行に独立ハッシュを 1 個だけ割り当てます。([dimacs.rutgers.edu][1], [dsf.berkeley.edu][2])

---

## 2  更新

要素が来るたびに各行で

```
表[行, ハッシュ(要素)] += 1
```

を実行します（計 *d* 回）。操作は O(*d*) 時間、メモリは O(*w d*)。([barnasaha.net][3])

---

## 3  クエリ

頻度推定は

```
min_{行} 表[行, ハッシュ(要素)]
```

—つまり *d* 個の値の最小を返すだけ。過小評価は起こらず、過大評価のみ。([dsf.berkeley.edu][2])

---

## 4  誤差保証

$$
\Pr\bigl[\text{推定} \le \text{真値} + εN \bigr] \ge 1-δ.
$$

理由（概略）

1. 1 行での余計な上乗せの期待値は $N/w ≈ εN/e$。
2. マルコフ不等式で「誤差 > εN」の確率を ≤ 1/e に抑制。
3. 行を *d* = ln(1/δ) 回独立に取り、全行で失敗しない確率を $(1-1/e)^d \ge 1-δ$ とする。([dimacs.rutgers.edu][1], [dsf.berkeley.edu][2])

---

## 5  パラメータ設計例

* 例：ε = 0.01, δ = 0.001
  ⇒ *w* ≈ 272, *d* ≈ 7,
  表サイズ 1.9 k カウンタで 99.9 % の確率で ±1 % 誤差以内。([barnasaha.net][3])

---

## 6  拡張の示唆（名称のみ）

* 保守的インクリメント（Conservative Update）で誤差縮小 ([サイエンスダイレクト][4])
* スケッチ同士を足し合わせ可能（線形性）([dimacs.rutgers.edu][1])

---




# Count–Min Sketch（CMS）具体例
以下では、具体的な数値例を使って Count–Min Sketch（CMS）がどのように動作するかをステップごとに示します。




CMS 
①固定サイズの行列（カウンタ）と複数のハッシュ関数を使い、
②ストリーム上の要素を分散してインクリメントし、
③「最小値」を取ることで要素の頻度を推定します。これにより、正確な頻度を数えるには大きなメモリが必要な場合でも、限られたメモリで高速に「およその回数」を得られるしくみです ([ウィキペディア][1]).

---

## 具体例の設定

### 行列とハッシュ関数の準備

* 行数（depth） $d=2$、列数（width） $w=5$ の行列 $C$ を用意 ([ウィキペディア][1]).
* 2 つのハッシュ関数 $h_1,h_2$ は、ここでは簡単化のために次のように定義します：

  * $h_1(x)\equiv (\text{文字数 of }x)\bmod 5$
  * $h_2(x)\equiv (\text{先頭文字の ASCIIコード})\bmod 5$
    （実際にはペアワイズ独立なハッシュ関数を用います） ([Computer Science Stack Exchange][2]).

### カウント対象のストリーム
以下の順序でアイテムが到来すると仮定：
```
apple, banana, apple, orange, banana, apple
```

これは合計6件のイベントです ([GeeksforGeeks][3]).

---

## ステップ1：初期状態

最初の行列はすべてゼロです。

|        | col0 | col1 | col2 | col3 | col4 |
| :----: | :--: | :--: | :--: | :--: | :--: |
| **h1** |   0  |   0  |   0  |   0  |   0  |
| **h2** |   0  |   0  |   0  |   0  |   0  |

この行列は、2×5 の $d\times w$ サイズであり、メモリ使用量はカウンタ数に比例 ([ウィキペディア][1]).

---

## ステップ2：更新操作（Inc）

ストリーム中の各アイテムについて、以下のように行列をインクリメント

1. **apple**

   * $h_1(\text{"apple"})=(5)\bmod5=0$
   * $h_2(\text{"apple"})=(97)\bmod5=2$
     → $C[1,0]++,\;C[2,2]++$

2. **banana**

   * $h_1(\text{"banana"})=(6)\bmod5=1$
   * $h_2(\text{"banana"})=(98)\bmod5=3$
     → $C[1,1]++,\;C[2,3]++$

3. 以下同様に **apple, orange, banana, apple** を順に処理します。
---
最終的に得られる行列は例えば下記のようになります（数値は例示） ([Medium][4]):

|        | col0 | col1 | col2 | col3 | col4 |
| :----: | :--: | :--: | :--: | :--: | :--: |
| **h1** |   3  |   2  |   0  |   1  |   0  |
| **h2** |   0  |   1  |   4  |   1  |   0  |

* 行1（h1）は文字数ベース、行2（h2）は先頭文字 ASCII ベースで分散カウントしています ([Medium][5]).
* 同じアイテムは必ず同じセルがインクリメントされるため、一貫性があります ([florian.github.io][6]).

---

## ステップ3：問い合わせ操作（Count）

たとえば「banana の回数」は次のように推定します ([ウィキペディア][1]):

1. 行1（h1）→ col1 = 2
2. 行2（h2）→ col3 = 1

→ **推定値** = $\min\{2,1\}=1$

実際の banana の真値は 2 回ですが、CMS は過大評価のみを許容し、過小評価は起こしません。したがって最小値で見積もることで誤差を抑えられます ([ウィキペディア][1]).

---



[1]: https://dimacs.rutgers.edu/~graham/pubs/papers/cmencyc.pdf?utm_source=chatgpt.com "[PDF] Count-Min Sketch - DIMACS (Rutgers)"
[2]: https://dsf.berkeley.edu/cs286/papers/countmin-latin2004.pdf?utm_source=chatgpt.com "[PDF] An Improved Data Stream Summary: The Count-Min Sketch and its ..."
[3]: https://barnasaha.net/wp-content/uploads/2016/01/lec3-haritha-1.pdf?utm_source=chatgpt.com "[PDF] Lecture 2 Overview 1 Introduction 2 Count-Min Sketch - Barna Saha"
[4]: https://www.sciencedirect.com/science/article/pii/S1389128622003607?utm_source=chatgpt.com "Analyzing Count Min Sketch with Conservative Updates"



以下では、Count–Min Sketch（CMS）の数理的仕組みを、大学教授への進捗発表に適した学術的な観点から整理して説明します。まず概要を述べ、その後にデータ構造、更新・クエリ操作、誤差保証の証明スケッチ、パラメータ設計の考え方、そして応用的拡張について解説します。

## 要約

Count–Min Sketch は、ストリーム中の要素頻度 $\{a_i\}$ をメモリ $\mathcal{O}(\tfrac{1}{\varepsilon}\ln\tfrac{1}{\delta})$ に抑えて近似記録する確率的データ構造である ([ウィキペディア][1])。
各要素の更新は $d$ 個のハッシュ関数によるインクリメント操作で行い、クエリはその最小値を取ることで「過大評価のみ」を許容し、

$$
\Pr\bigl[\tilde a_i \le a_i + \varepsilon N\bigr] \ge 1 - \delta
$$

という一方向の誤差保証を得る ([cs.umass.edu][2], [ウィキペディア][1])。
誤差保証はマルコフ不等式とハッシュの独立性から導かれ、要素数 $N$ に対し許容誤差 $\varepsilon N$、失敗確率 $\delta$ を制御するパラメータ設計が可能である ([dimacs.rutgers.edu][3], [homes.cs.washington.edu][4])。

---

## データ構造

### テーブルとハッシュ関数

* **行数** $d = \lceil \ln(1/\delta)\rceil$
* **列数** $w = \lceil e/\varepsilon\rceil$
  の整数テーブル $C\in\mathbb{Z}^{d\times w}$ を用意する ([ウィキペディア][1])。
  各行 $i$ に対し、ペアワイズ独立なハッシュ関数 $h_i: \mathcal{U}\to\{1,\dots,w\}$ を割り当てる ([dimacs.rutgers.edu][5])。

### メモリと時間複雑度

* メモリ：$\displaystyle O\!\Bigl(\tfrac1\varepsilon\ln\tfrac1\delta\Bigr)$
* 更新・クエリ時間：$\displaystyle O(\ln\tfrac1\delta)$
  で、ストリーム処理におけるサブリニア空間を実現する ([dsf.berkeley.edu][6])。

---

## 更新操作とクエリ

### 更新（ストリーム到着時）

要素 $x$ が到来したら、すべての行 $i$ について

$$
j = h_i(x),\quad C[i,j]\;\mathrel{+}=1
$$

とする ([ウィキペディア][1])。

### 点クエリ（頻度推定）

要素 $x$ の頻度推定 $\tilde a_x$ は、該当セルの最小値を取る：

$$
\tilde a_x \;=\;\min_{1\le i\le d} C[i,\,h_i(x)].
$$

これにより衝突による過大評価のみが生じ、過小評価は起こらない ([ウィキペディア][1], [Computer Science][7])。

---

## 誤差保証の証明スケッチ

### 一方向誤差の導出

1. **衝突による過大評価**
   任意の行 $i$ で、異なる要素が同じハッシュ値を持つとカウントが上乗せされる。その期待値は $\tfrac{N}{w}$ である ([homes.cs.washington.edu][4])。
2. **マルコフ不等式によるバウンド**
   $\Pr\bigl[C[i,h_i(x)] > a_x + \varepsilon N\bigr] \le \tfrac{E[C[i,h_i(x)] - a_x]}{\varepsilon N} \le \tfrac1e$ となる ([dimacs.rutgers.edu][3])。
3. **独立性による高確率保証**
   各行のハッシュは独立なので、失敗確率を $\delta$ に下げるために $d=\lceil\ln(1/\delta)\rceil$ 行用意し、全行で正しく推定できる確率を
   $\bigl(1 - \tfrac1e\bigr)^d \ge 1 - \delta$ とできる ([dimacs.rutgers.edu][3], [cs368-stanford.github.io][8])。

---

## パラメータ設計

* **許容誤差** $\varepsilon$：全体要素数 $N$ に対する相対誤差
* **失敗確率** $\delta$：保証が外れる確率
  これらに応じて $w\approx e/\varepsilon$、$d\approx\ln(1/\delta)$ を設定し、必要メモリと推定精度をトレードオフする ([ウィキペディア][1], [webdocs.cs.ualberta.ca][9])。

---

## 応用的拡張

### Conservative Update

最小推定値を用いてセルを条件付きインクリメントし、過大評価をさらに抑える手法 ([webdocs.cs.ualberta.ca][9])。

### 内積推定

二つの CMS の対応セルの積の最小値を取ることで、ヒストグラムの内積を $\hat{a\cdot b}$ として推定できる ([ウィキペディア][1])。

### マージ可能性

CMS は線形スケッチであるため、分散環境で部分スケッチを合算しても同一の結果を得られる ([ウィキペディア][1])。

---

以上が、Count–Min Sketch の数理的背景と主要な特性の概要です。これらをベースに、ストリーミングアルゴリズムへの応用やデータベース集計への導入を検討すると良いでしょう。

[1]: https://en.wikipedia.org/wiki/Count%E2%80%93min_sketch?utm_source=chatgpt.com "Count–min sketch"
[2]: https://www.cs.umass.edu/~mcgregor/711S18/countmin.pdf?utm_source=chatgpt.com "[PDF] An Improved Data Stream Summary: The Count-Min Sketch and its ..."
[3]: https://dimacs.rutgers.edu/~graham/pubs/papers/encalgs-cm.pdf?utm_source=chatgpt.com "[PDF] Count-Min Sketch - DIMACS (Rutgers)"
[4]: https://homes.cs.washington.edu/~jrl/cse422wi24/notes/heavy-hitters.pdf?utm_source=chatgpt.com "[PDF] Lecture #2: Heavy hitters and the count-min sketch"
[5]: https://dimacs.rutgers.edu/~graham/pubs/papers/cmencyc.pdf?utm_source=chatgpt.com "[PDF] Count-Min Sketch - DIMACS (Rutgers)"
[6]: https://dsf.berkeley.edu/cs286/papers/countmin-latin2004.pdf?utm_source=chatgpt.com "[PDF] An Improved Data Stream Summary: The Count-Min Sketch and its ..."
[7]: https://cs.stanford.edu/~rishig/courses/ref/l12b.pdf?utm_source=chatgpt.com "[PDF] CS 167 Paper Report"
[8]: https://cs368-stanford.github.io/spring2022/lectures/lec8.pdf?utm_source=chatgpt.com "[PDF] Lecture 8: CR-PRECIS and Count Sketch - GitHub Pages"
[9]: https://webdocs.cs.ualberta.ca/~drafiei/papers/cmm.pdf?utm_source=chatgpt.com "[PDF] New Estimation Algorithms for Streaming Data: Count-min Can Do ..."
