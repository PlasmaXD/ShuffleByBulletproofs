---
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
---
# **Count–Min Sketch × Local DP Simplifying explanation**

以下、専門用語をできるだけかみくだいた説明です.

## 要点まとめ

Count–Min Sketch（CMS）は「大きなデータの中で、あるもの（例：URLや単語）が何回出てくるか」を効率よく近似する仕組みです.
ローカル差分プライバシ（LDP）は「各ユーザーが自分のデータにノイズを加えて送る」ことで、サーバー側に生のデータを渡さずに統計を取る方法です.
この二つを組み合わせると、ユーザーのプライバシを守りつつ、大量のデータから頻度集計を行えます.

---

# 1. Count–Min Sketch（CMS）
1. **箱を並べた表** を想像してください（行が $d$ 列が $w$）.
2. データ（たとえば URL）が来るたびに、いくつかのハッシュ関数で行と列の番号を決めてその箱に「＋1」を足します.
3. 箱が小さいので衝突（別の URL と同じ箱に入ること）がありますが、すべての行で一番小さい数字を見ることで「本当は少なくてもこのくらいはあった」という上限付きの推定値が得られます.

   * 真の回数よりは少し大きい数字になりますが、大量データでも高速・省メモリで動きます ([ウィキペディア][1]).

---

# 2. ローカル差分プライバシ（LDP） 

1. ユーザーの本当の値（例：特定の URL を見たかどうか）に**ノイズ**を混ぜます.
2. ノイズ混ぜには「ランダム化応答」という仕組みを使い、真なら高い確率で「1」、偽なら低い確率で「1」を返すようにします.
3. こうするとサーバーは各ユーザーの本当の値を知らずに済み（プライバシ保護）、統計的に合計を集めるとノイズが打ち消されてだいたい正しい結果が得られます ([ウィキペディア][2]).

---

## 3. CMS × LDP の組み合わせ

1. **クライアント側**

   * URL が来たら、CMS のハッシュで決まる $d$ 箇所だけ「本当は1」の場所にノイズ付きでビット（0か1）を作る.
   * このビット列だけをサーバーに送信.
2. **サーバー側**

   * 受け取ったビットを CMS の対応する箱に足し合わせる.
   * 一定数（$N$ 人分）集めたあと、本来の確率 $q,p$ を使って「ざっくりどれくらい真値があったか」を逆計算.
   * 最後に「各行の逆計算結果の中でいちばん小さい値」を取ると、CMS の性質で過大評価が抑えられます ([ウィキペディア][1]).

---

# 4. 具体例

### 4.1 Apple iOS の絵文字統計

Apple は「Private Count Mean Sketch」を用いてユーザーの絵文字使用頻度を収集し、ε-LDP を実現しています ([arXiv][5])。

### 4.2 大規模ログ・IoT データ

ストリーミングトラフィックや IoT データの頻度解析にも CMS×LDP が応用され始めています ([サイエンスダイレクト][6])。

---

## 5. なぜ便利？

* **メモリ小さめ**：CMS は固定サイズの表だけ.
* **プライバシ保護**：生データはユーザー端末でノイズ化.
* **高速**：更新・集計ともに $O(d)$ でできるので、大量データに強い.

このようにして、大規模なデータ分析をしながらも、個人のプライバシをしっかり守れる仕組みが「CMS × LDP」です.

[1]: https://en.wikipedia.org/wiki/Count%E2%80%93min_sketch?utm_source=chatgpt.com "Count–min sketch"
[2]: https://en.wikipedia.org/wiki/Local_differential_privacy?utm_source=chatgpt.com "Local differential privacy"
[3]: https://www.wired.com/beyond-the-beyond/2017/12/web-semantics-local-differential-privacy?utm_source=chatgpt.com "Web Semantics: local differential privacy"


[5]: https://arxiv.org/pdf/2205.08397?utm_source=chatgpt.com "[PDF] Improved Utility Analysis of Private CountSketch - arXiv"
[6]: https://www.sciencedirect.com/science/article/abs/pii/S0020025523012525?utm_source=chatgpt.com "Local differentially private frequency estimation based on learned ..."
[7]: https://redis.io/blog/count-min-sketch-the-art-and-science-of-estimating-stuff/?utm_source=chatgpt.com "Count-Min Sketch: The Art and Science of Estimating Stuff | Redis"
[8]: https://arxiv.org/pdf/2205.09873?utm_source=chatgpt.com "[PDF] Differentially Private Linear Sketches - arXiv"

