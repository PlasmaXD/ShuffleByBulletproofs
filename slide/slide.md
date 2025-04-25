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


# Bulletproofs を用いたシャッフラーのコード概要

- Rust で実装したサンプルコードの紹介  
- ペデンコミットメントとレンジプルーフの生成  
- コミットメントのシャッフルとその準同型性の検証  
- 今後の応用展開について


---

# コードの主要機能

- **コミットメント生成**  
  各値に対し、ランダムなブラインディングを用いてペデンコミットメントを計算  
  $$
  C = rH + vG
  $$

- **レンジプルーフ生成※**  
  秘密の値が 0 ～ $2^{64}-1$ の範囲内にあることをゼロ知識で証明
  (※「コミットした秘密値が事前に指定した区間内にある」ことをゼロ知識で証明する技術)

- **シャッフル処理**  
  複数のコミットメントをランダムに並び替え、全体の合計が保存される（加法的性質）

---


#### 処理フロー図

<pre class="mermaid">
%%{init: {'theme': 'neutral', 'fontSize': 14}}%%

sequenceDiagram
    participant App as アプリ
    participant Gen as コミット生成
    participant Shuffle as シャッフル処理
    participant Sum as 合計計算

    App->>Gen: 各値のコミットメントを生成する
    Gen-->>App: コミットメントリストを返す
    App->>Sum: コミットメントリストの合計を計算（original sum）
    App->>Shuffle: コミットメントリストをシャッフルする
    Shuffle-->>App: シャッフル済みリストを返す
    App->>Sum: シャッフル済みリストの合計を計算（shuffled sum）
    App->>App: original sum と shuffled sum を比較
    App->>App: 結果を出力
</pre>


- **加法的性質の検証**  
  シャッフル前後で合計が同じであれば、シャッフル処理に問題はないと確認

---

# 今後の展開

- **検証可能なシャッフル証明の統合**  
  出力が入力の順序変更であることをゼロ知識証明で保証

- **大規模ミキシングプロトコルの構築**  
  Bulletproofs の集約機能を活かし、複数の取引に対する証明を効率的に管理

- **セキュリティとプライバシーの強化**

---

# まとめ

- Bulletproofs を活用することで、  
  - ペデンコミットメントに基づくレンジプルーフが生成可能  
  - 秘密の値の範囲を非対話型ゼロ知識で証明  
  - コミットメントの加法性を利用してシャッフルの正当性を検証

- 今回のサンプルコードは、これらの基礎処理（コミットメント生成、シャッフル、合計検証）を実装



---
# 補足
1. **レンジプルーフ（Range Proof）**  
2. **合計一致（Sum Preservation）の妥当性**  
3. **Pedersenコミットメントの意味・意義**
---

## 概要まとめ

- **レンジプルーフ**は「コミットした秘密値が事前に指定した区間内にある」ことをゼロ知識で証明する技術です  ([[PDF] SoK: Zero-Knowledge Range Proofs - Cryptology ePrint Archive](https://eprint.iacr.org/2024/430.pdf?utm_source=chatgpt.com))。  
- **合計一致の妥当性**は、シャッフル／再ランダム化されたコミットメント列の総和が元の総和と等しいことを証明し、改竄の不在を担保します  ([[PDF] New Algorithms and Analyses for Sum- Preserving Encryption - IACR](https://iacr.org/submit/files/slides/2022/asiacrypt/asiacrypt2022/217/slides.pdf?utm_source=chatgpt.com), [[PDF] Proof of a shuffle for lattice-based cryptography](https://eprint.iacr.org/2017/900.pdf?utm_source=chatgpt.com))。  
- **Pedersenコミットメント**は、値を隠しつつ後で開示・検証でき、加法同型性を持つコミットメント方式で、隠蔽性と結合性を同時に実現します  ([Pedersen Commitmentを添えて - Zenn](https://zenn.dev/noplan_inc/articles/0ea904a1b31f04?utm_source=chatgpt.com), [Why is the Pedersen commitment perfectly hiding?](https://crypto.stackexchange.com/questions/54439/why-is-the-pedersen-commitment-perfectly-hiding?utm_source=chatgpt.com))。

---

## 1. レンジプルーフとは？

### 定義  
レンジプルーフは、ある秘密値 $v$ があらかじめ決められた整数区間 $[a, b]$ 内にあることを、値そのものを一切漏らさずに証明するゼロ知識証明の一種です  ([[PDF] SoK: Zero-Knowledge Range Proofs - Cryptology ePrint Archive](https://eprint.iacr.org/2024/430.pdf?utm_source=chatgpt.com))。

### 主な用途  
- 暗号資産トランザクションで「送金額が負になっていない」ことを示す  
- 匿名認証で「年齢が成人以上」であることを証明する  
- 差分プライバシー付きレポートで「ノイズを混ぜた後の値が閾値以下」であることを保証する  ([Cryptographic Range Proofs: From Damgård to Bulletproofs - Medium](https://medium.com/asecuritysite-when-bob-met-alice/cryptographic-range-proofs-from-damg%C3%A5rd-to-bulletproofs-90ff221b2551?utm_source=chatgpt.com))。

### 技術的背景  
- 最初期は Bit-by-bit 証明など多くの対話型プロトコルが提案された後、Bulletproofs のような非対話型・短証明化技術が登場し、高効率化が進んでいます  ([論文翻訳: Bulletproofs: Short Proofs for Confidential Transactions ...](https://hazm.at/mox/security/zero-knowledge-proof/bulletproofs-short-proofs-for-confidential-transactions-and-more/index.html?utm_source=chatgpt.com))。

---

## 2. 合計一致の妥当性（Sum Preservation）

### なぜ「合計」を証明するのか？  
- シャッフルや再ランダム化で「要素の追加・削除・改竄」がないことを担保するため、全コミットメントの総和が不変であることを証明します  ([[PDF] New Algorithms and Analyses for Sum- Preserving Encryption - IACR](https://iacr.org/submit/files/slides/2022/asiacrypt/asiacrypt2022/217/slides.pdf?utm_source=chatgpt.com))。  
- コミットメントは加法同型性を持つため、コミットメント同士を足せば元の値の和に相当し、総和一致が証明できれば個々の値も改竄されていないとみなせます  ([Pedersen Commitments | ZKDocs](https://www.zkdocs.com/docs/zkdocs/commitments/pedersen/?utm_source=chatgpt.com))。

### 証明方式のポイント  
1. **Permutation**: 出力集合が入力集合の順序違いであること  
2. **Re-randomization**: 新しい乱数で再ブラインドしているが値は変わらないこと  
3. **Sum Preservation**: 全てのコミットメントの和が同じであること  ([[PDF] Proof of a shuffle for lattice-based cryptography](https://eprint.iacr.org/2017/900.pdf?utm_source=chatgpt.com), [Commitments - Mina book](https://o1-labs.github.io/proof-systems/fundamentals/zkbook_commitment.html?utm_source=chatgpt.com))。

### 効率性のメリット  
- 個別要素の比較より総和だけを証明するほうが、Bulletproofs 等で生成・検証コストを大幅に削減できます  ([ビットコミットメント｜【ブロックチェーン】ZKP(ゼロ知識 ... - Zenn](https://zenn.dev/joeee/books/6f600be4fd9623/viewer/1a1456?utm_source=chatgpt.com))。

---

## 3. Pedersenコミットメントの意味

### 基本構造  

$$ 
C = rH + vG
 $$
  
- $G, H$：公開された群のジェネレータ  
- $v$：秘密値  
- $r$：ランダムブラインディング因子

### 主な特性  
1. **隠蔽性（Hiding）**  
   ランダム $r$ により、$C$ からは $v$ が一切わからない（完全隠蔽）  ([Why is the Pedersen commitment perfectly hiding?](https://crypto.stackexchange.com/questions/54439/why-is-the-pedersen-commitment-perfectly-hiding?utm_source=chatgpt.com))。  
2. **結合性（Binding）**  
   一度生成されたコミットメントは変更不可能。異なる $(v',r')$ で同じ $C$ を作ることは離散対数問題の困難性に帰着  ([Pedersen Commitments | ZKDocs](https://www.zkdocs.com/docs/zkdocs/commitments/pedersen/?utm_source=chatgpt.com))。  
3. **加法同型性（Homomorphism）**  
   $\displaystyle C(v_1)\!+\!C(v_2)=C(v_1+v_2)$ が成り立ち、合計一致証明などに活用できる  ([Pedersen Commitmentを添えて - Zenn](https://zenn.dev/noplan_inc/articles/0ea904a1b31f04?utm_source=chatgpt.com))。
---

## 3. Pedersenコミットメントの意義

### 実践的意義  
- **差分プライバシー＋ゼロ知識証明** の組み合わせで、データを隠しつつ正当性を証明できる  
- **シャッフラー** や **ミックスネット**、匿名投票システムなど幅広い応用で基礎技術として採用  
- Bulletproofs をはじめとする新世代 ZKP の多くが Pedersen コミットメントを前提とし、高速・短証明を実現しています  ([論文翻訳: Bulletproofs: Short Proofs for Confidential Transactions ...](https://hazm.at/mox/security/zero-knowledge-proof/bulletproofs-short-proofs-for-confidential-transactions-and-more/index.html?utm_source=chatgpt.com))。

---

以上が各要素の詳細解説です。レンジプルーフと合計一致証明は、Pedersenコミットメントの隠蔽性・結合性・加法同型性を組み合わせることで「プライバシー保護」と「整合性担保」を両立するための中核技術です。





<script type="module">
import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.esm.min.mjs';
mermaid.initialize({ 
  startOnLoad: true,
  theme: 'neutral',
  fontSize: 14
});
</script>