# Bulletproofs の全体の流れ

### 1. Pedersen コミットメントの生成

秘密値 $v$ とランダムな blinding 値 $r$ を用いて、Pedersen コミットメント $C$ を作成します。

$$
C = v \cdot H + r \cdot G.
$$

ここで、$G$ と $H$ は公開のグループ生成元です。

---

### 2. ビット分解と補助ベクトルの定義

- **ビット分解:**  
  $v$ を2進数で分解し、ビット列ベクトル $\mathbf{a} = (a_1, a_2, \dots, a_n)$ を生成します。  
  重みベクトルを $\mathbf{w} = (1, 2, \dots, 2^{n-1})$ とすると、
  
  $$
  v = \langle \mathbf{a}, \mathbf{w} \rangle = \sum_{i=1}^n 2^{i-1} a_i.
  $$

- **補助ベクトル:**  
  各 $a_i \in \{0,1\}$ であることを確認するため、  
  $$
  \mathbf{b} = \mathbf{a} - \mathbf{1},
  $$
  と定義します。これにより、各 $a_i$ について
  $$
  a_i(a_i - 1) = 0
  $$
  が成立し、正しくビットであることが保証されます。

---

### 3. 内積論証の再帰的プロトコル

内積論証では、ベクトル $\mathbf{a}$ と $\mathbf{b}$ の内積（例えば、$\langle \mathbf{a}, \mathbf{b} \rangle = 0$）が正しいことを、短い証明に圧縮して示します。ここでは、再帰的な圧縮ステップを用います。

1. **ベクトルの分割:**  
   $$
   \mathbf{a} = (\mathbf{a_L}, \mathbf{a_R}), \quad \mathbf{b} = (\mathbf{b_L}, \mathbf{b_R}).
   $$

2. **補助コミットメントの生成:**  
   分割したベクトルに対して、以下のコミットメント $L$ と $R$ を計算します。
   $$
   L = \mathrm{Com}(\mathbf{a_L}, \mathbf{b_R}), \quad R = \mathrm{Com}(\mathbf{a_R}, \mathbf{b_L}).
   $$
   ここで、$\mathrm{Com}(\cdot,\cdot)$ は例えばペダースコミットメントなどを意味します。

3. **チャレンジ値の生成（Fiat–Shamir ヒューリスティック）:**  
   補助コミットメント $L, R$ を使い、次のようにチャレンジ $x$ を計算します。
   $$
   x = H(L, R),
   $$
   ここで $H$ は暗号学的ハッシュ関数です。

4. **ベクトルの圧縮:**  
   チャレンジ $x$ を用いて、新たな圧縮ベクトルを定義します。
   $$
   \mathbf{a'} = \mathbf{a_L} + x \cdot \mathbf{a_R}, \quad \mathbf{b'} = \mathbf{b_L} + x^{-1} \cdot \mathbf{b_R}.
   $$
   このとき、内積は以下のように保存されます。
   $$
   \langle \mathbf{a'}, \mathbf{b'} \rangle = \langle \mathbf{a_L}, \mathbf{b_L} \rangle + \langle \mathbf{a_R}, \mathbf{b_R} \rangle.
   $$

5. **コミットメントの更新:**  
   元のコミットメント $P$（最初は $P = C$ など）も、同様に圧縮に対応して更新されます。
   $$
   P' = L^{x^2} \cdot P \cdot R^{x^{-2}}.
   $$

6. **再帰:**  
   この圧縮ステップを、ベクトルの次元が 1 になるまで繰り返します。最終的には、スカラー値 $a'$ と $b'$ が得られ、検証では
   $$
   P = g^{a'} h^{b'}
   $$
   および $a' \cdot b' = c$（内積）が成立することをチェックします。

---

### 4. 全体の証明と検証

- **証明の生成:**  
  証明は、各再帰ラウンドで生成される補助コミットメント $(L_1, R_1), (L_2, R_2), \dots, (L_k, R_k)$ と、最終的なスカラー値 $a', b'$ から構成されます。

- **検証:**  
  検証者は、公開情報と証明から各ラウンドの $x_i = H(L_i, R_i)$ を再計算し、圧縮されたコミットメントが正しく更新されているか、
  $$
  P \stackrel{?}{=} \left( \prod_{i=1}^{k} L_i^{x_i^2} \cdot R_i^{x_i^{-2}} \right) \cdot g^{a'} h^{b'},
  $$
  そして内積の最終検証 $a' \cdot b' = c$ を確認します。

---

### 5. まとめ

Bulletproofs の全体の流れは、以下のような数式群で表現できます。

1. **Pedersen コミットメント:**
   $$
   C = v \cdot H + r \cdot G.
   $$
2. **ビット分解:**
   $$
   v = \langle \mathbf{a}, \mathbf{w} \rangle, \quad \mathbf{w} = (1,2,\dots,2^{n-1}).
   $$
3. **補助ベクトル:**
   $$
   \mathbf{b} = \mathbf{a} - \mathbf{1}.
   $$
4. **内積論証（再帰的プロトコル）:**
   $$
   \begin{aligned}
   &\text{分割: } \mathbf{a} = (\mathbf{a_L}, \mathbf{a_R}),\quad \mathbf{b} = (\mathbf{b_L}, \mathbf{b_R}).\\[1mm]
   &\text{補助コミットメント: } L = \mathrm{Com}(\mathbf{a_L}, \mathbf{b_R}),\quad R = \mathrm{Com}(\mathbf{a_R}, \mathbf{b_L}).\\[1mm]
   &\text{チャレンジ: } x = H(L, R).\\[1mm]
   &\text{圧縮: } \mathbf{a'} = \mathbf{a_L} + x \cdot \mathbf{a_R},\quad \mathbf{b'} = \mathbf{b_L} + x^{-1} \cdot \mathbf{b_R}.\\[1mm]
   &\text{コミットメント更新: } P' = L^{x^2} \cdot P \cdot R^{x^{-2}}.\\[1mm]
   &\text{再帰し、最終的に } a',\, b' \text{（スカラー）を得る。}
   \end{aligned}
   $$
5. **検証:**
   $$
   P \stackrel{?}{=} \left( \prod_{i=1}^{k} L_i^{x_i^2} \cdot R_i^{x_i^{-2}} \right) \cdot g^{a'} h^{b'}, \quad a' \cdot b' = c.
   $$

