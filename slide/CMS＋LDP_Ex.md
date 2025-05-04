<!-- ---
marp: true
theme: default
mermaid: true
paginate: true
title: Bulletproofs シャッフラー発表資料
author: Your Name
date: 2025-03-07
style: |
  /* スライド全体の背景色と文字色 */
  section {
    background-color: #f5f5f5;
    color: #333333;
  }
  
  /* Mermaid 図内の文字色や背景色を調整 */
  .mermaid {
    /* Mermaid 図自体のスタイルをここで調整可能 */
    color: #333333;
        # transform: scale(0.7);

  }

  .mermaid .node text,
  .mermaid .edgeLabel text {
    font-size: 14px;
  }
--- -->


# Count–Min Sketch（CMS）具体的
以下では、具体的な数値例を使って Count–Min Sketch（CMS）がどのように動作するかをステップごとに示します。

---
思考時間: 6 秒


以下では、具体的な数値例を使って Count–Min Sketch（CMS）がどのように動作するかを示します。まず要点をまとめ、その後ステップごとに詳しく説明します。

CMS は、①固定サイズの行列（カウンタ）と複数のハッシュ関数を使い、②ストリーム上の要素を分散してインクリメントし、③「最小値」を取ることで要素の頻度を推定します。これにより、正確な頻度を数えるには大きなメモリが必要な場合でも、限られたメモリで高速に「およその回数」を得られるしくみです ([ウィキペディア][1]).

---

## 具体例の設定

### 行列とハッシュ関数の準備

* 行数（depth） $d=2$、列数（width） $w=5$ の行列 $C$ を用意します ([ウィキペディア][1]).
* 2 つのハッシュ関数 $h_1,h_2$ は、ここでは簡単化のために次のように定義します：

  * $h_1(x)\equiv (\text{文字数 of }x)\bmod 5$
  * $h_2(x)\equiv (\text{先頭文字の ASCIIコード})\bmod 5$
    （実際にはペアワイズ独立なハッシュ関数を用います） ([Computer Science Stack Exchange][2]).

### カウント対象のストリーム

以下の順序でアイテムが到来すると仮定します：

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

この行列は、2×5 の $d\times w$ サイズであり、メモリ使用量はカウンタ数に比例します ([ウィキペディア][1]).

---

## ステップ2：更新操作（Inc）

ストリーム中の各アイテムについて、以下のように行列をインクリメントします ([ウィキペディア][1]):

1. **apple**

   * $h_1(\text{"apple"})=(5)\bmod5=0$
   * $h_2(\text{"apple"})=(97)\bmod5=2$
     → $C[1,0]++,\;C[2,2]++$

2. **banana**

   * $h_1(\text{"banana"})=(6)\bmod5=1$
   * $h_2(\text{"banana"})=(98)\bmod5=3$
     → $C[1,1]++,\;C[2,3]++$

3. 以下同様に **apple, orange, banana, apple** を順に処理します。

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

## なぜ過大評価だけ？

* ハッシュ衝突により他要素のインクリメントが混ざると **セルの値が大きく** なるが、
* 最小値を取ることで「衝突で余計にカウントされた分」はできるだけ除外する仕組みです ([Redis][7]).
* 結果として、推定値 $\hat f(x)$ は真値 $f(x)$ を下回らず、かつ $f(x)+\epsilon N$ を超えない保証があります（$\epsilon$, $N$ は誤差率とストリームサイズ） ([ウィキペディア][1]).

---

## まとめ

* **小さな行列**＋**複数ハッシュ** で、
* 更新も問い合わせも $O(d)$ 時間、
* 推定時に **最小値** を取ることで衝突誤差を抑制しつつ、
* 低メモリで大規模ストリームの近似頻度集計が可能です ([homes.cs.washington.edu][8]).

この具体例により、CMS の動作原理がイメージしやすくなるかと思います。パラメータの選び方や実装の詳細など、さらに気になる点があればお知らせください！

[1]: https://en.wikipedia.org/wiki/Count%E2%80%93min_sketch?utm_source=chatgpt.com "Count–min sketch"
[2]: https://cs.stackexchange.com/questions/166937/what-is-the-proper-way-to-calculate-dimensions-of-count-min-sketch?utm_source=chatgpt.com "What is the proper way to calculate dimensions of count min sketch"
[3]: https://www.geeksforgeeks.org/count-min-sketch-in-java-with-examples/?utm_source=chatgpt.com "Count-Min Sketch Data Structure with Implementation | GeeksforGeeks"
[4]: https://medium.com/%40amirziai/count-min-sketch-4b0ab93bb37a?utm_source=chatgpt.com "Count-min sketch - Medium"
[5]: https://medium.com/%40rrinlondon/count-min-sketch-5bf22743798a?utm_source=chatgpt.com "Count Min Sketch - Medium"
[6]: https://florian.github.io/count-min-sketch/?utm_source=chatgpt.com "Count-Min Sketch"
[7]: https://redis.io/blog/count-min-sketch-the-art-and-science-of-estimating-stuff/?utm_source=chatgpt.com "Count-Min Sketch: The Art and Science of Estimating Stuff | Redis"
[8]: https://homes.cs.washington.edu/~jrl/cse422wi24/notes/heavy-hitters.pdf?utm_source=chatgpt.com "[PDF] Lecture #2: Heavy hitters and the count-min sketch"
