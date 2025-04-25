---
marp: true
theme: default
paginate: true
---

# シャッフラーにおける証明方式の比較

---

## 概要

ブラウザ側で差分プライバシー(DP)乱数化を行うシステムにおけるシャッフラーは、  ユーザレポートの**並べ替え**によって匿名化を強化します。  

シャッフラーの正当性を担保する証明方式には、  
1.  **Sum Preservation証明**  :コミットメントの**合計が不変**であることを示す
2.  **Permutation証明**  :出力列が入力列の**完全な置換**であることを示す
---
- **Sum Preservation**  
  - 加法同型性で「総和が変わらない」ことを高速に検証  
  - 同じ和でも異なる集合になり得る → 改竄を見逃す恐れ  
  <!-- ([Distributed Differential Privacy via Shuffling](https://www.iacr.org/archive/eurocrypt2019/114760269/114760269.pdf?utm_source=chatgpt.com), [Pedersen commitments and addition](https://crypto.stackexchange.com/questions/40306/pedersen-commitments-and-addition?utm_source=chatgpt.com))   -->

- **Permutation証明**  
  - 多重集合の同一性をゼロ知識で保証  
  - 強い担保だが高コスト  
  ([Bulletproofs: Short Proofs for Confidential Transactions and More](https://eprint.iacr.org/2017/1066.pdf?utm_source=chatgpt.com), [Efficient Zero-Knowledge Argument for Correctness of a Shuffle](https://www0.cs.ucl.ac.uk/staff/J.Groth/MinimalShuffle.pdf?utm_source=chatgpt.com))  

---

## 1. Sum Preservation証明

### 定義と仕組み

- Pedersenコミットメント  
  $$C_i = r_i H + v_i G$$  
- 加法同型性により  
  $$\sum_i C_i = C\bigl(\sum_i v_i,\sum_i r_i\bigr)$$  
- **証明**：入出力コミットメント列の総和一致を非対話型ZKPで示す  ([論文](https://www.iacr.org/archive/eurocrypt2019/114760269/114760269.pdf?utm_source=chatgpt.com))  

### 限界

- 例：\{1,3\} と \{2,2\} は同じ合計4 → 改竄か置き換えか判別不可   ([論文](https://www.vldb.org/pvldb/vol13/p3545-wang.pdf?utm_source=chatgpt.com))  
- 追加・削除・不正操作を完全には防げない

---

## 2. Permutation(並べ替え)証明

### 定義と仕組み

- 入力列 \(\{C_i\}\) と出力列 \(\{C'_j\}\) が同一多重集合であることを保証  
- ランダムチャレンジ \(z\) に対し：  
  $$\prod_i (C_i - z) = \prod_j (C'_j - z)$$  
  をゼロ知識で証明  
  ([MinimalShuffle](https://www0.cs.ucl.ac.uk/staff/J.Groth/MinimalShuffle.pdf?utm_source=chatgpt.com), [Bulletproofs](https://eprint.iacr.org/2017/1066.pdf?utm_source=chatgpt.com))

### 利点

- **完全性**：並べ替え以外の改竄を一切許さない  
  ([Distributed Differential Privacy via Shuffling](https://www.iacr.org/archive/eurocrypt2019/114760269/114760269.pdf?utm_source=chatgpt.com))  
- **応用例**：選挙集計、金融ソルベンシー証明など  
  ([PROCHLO: Strong Privacy for Analytics in the Crowd](https://research.google.com/pubs/archive/46411.pdf?utm_source=chatgpt.com), [Scalable and Differentially Private Distributed Aggregation](https://arxiv.org/abs/1906.08320?utm_source=chatgpt.com))

---

## 3. DPシャッフルモデルでの選択基準

### プライバシー重視

- LDP乱数化自体が強力 → シャッフラーは匿名化(Linkability遮断)を担う  
  ([Private Summation in the Multi-Message Shuffle Model](https://arxiv.org/pdf/2002.00817?utm_source=chatgpt.com))  
- 集計精度重視なら **Sum Preservation** の軽量性を活かす  
  ([A Shuffling Framework for Local Differential Privacy](https://arxiv.org/abs/2106.06603?utm_source=chatgpt.com))

### インテグリティ重視

- 改竄防止や不正レポート検知には **Permutation証明** を推奨  
  ([Bulletproofs](https://eprint.iacr.org/2017/1066.pdf?utm_source=chatgpt.com), [MinimalShuffle](https://www0.cs.ucl.ac.uk/staff/J.Groth/MinimalShuffle.pdf?utm_source=chatgpt.com))  
- PROCHLOなどでは両立実装例として採用

---

## まとめ

- **Sum Preservation**  
  - 証明コスト低、集計用途に適するが改竄検出は不可  
- **Permutation証明**  
  - 証明コスト高、完全一致保証で改竄リスク排除  
- **使い分け**：  
  - プライバシー重視 → Sum Preservation  
  - インテグリティ重視 → Permutation  
