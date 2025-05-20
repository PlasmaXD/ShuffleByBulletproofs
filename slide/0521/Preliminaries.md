以下では **VLDPPipeline** の実装論文 ([Cryptology ePrint Archive][1]) および暗号プリミティブの代表的な解説記事・RFC を突き合わせて，「実際に採用された具体的プリミティブ」と「採用理由・特性」を整理します。
### 疑似乱数生成 (PRG from PRF)

**採用プリミティブ**

* **鍵付き BLAKE2s** を PRF として使用し，出力をそのまま擬似乱数（PRG）列に展開。([Cryptology ePrint Archive][1], [国際暗号研究機関][2])

**簡単流れと数式**

1. クライアントとサーバがそれぞれ乱数キー $k_c,\;k_s$ を生成し，Diffie–Hellman 共有鍵と同様に XOR 合成して共通鍵 $k = k_c \oplus k_s$ を決定。([Cryptography Stack Exchange][3])
2. ラウンド識別子 $s_j$ を入力に

   $$
     \rho_{i,j}= \mathrm{BLAKE2s}(k \,\|\, s_j)
   $$

   を計算して LDP ノイズ・シャッフル順のタネを得る。

**用途**

* 各ユーザの LDP ノイズ値生成
* シャッフラーで使う乱順列（再現可能）

**特性と採用メリット**

* **PRF 安全性**が学術的に分析済みで 128 bit 水準を確保([Cryptology ePrint Archive][1])
* 実装が軽量（ハッシュ１種で PRF/CRH を兼用）
* 双方が鍵を出し合うため片方だけで乱数を支配できない

---

### コミットメント

**採用プリミティブ**

* **Pedersen vector commitment** を Baby Jubjub 曲線上で実装([RareSkills][4], [Fellowship of Ethereum Magicians][5])

**用途**

* クライアントの乱数キー $k_c$ を先に「紙袋に封印」し，後で開示しても改竄していないことを保証

**特性と採用メリット**

* **情報理論的ハイディング**で内容完全秘匿，**計算量的バインディング**で改竄不可([ウィキペディア][6])
* **加法ホモモルフィズム**により複数値を一括コミットでき，乱数ベクトルでも効率的([RareSkills][4])
* Jubjub 上の Pedersen は SNARK 回路制約が小さく高速

---

### デジタル署名

**採用プリミティブ**

* **Schnorr 署名**（Baby Jubjub 上，BLAKE2s をチャレンジに使用）([Espresso][7], [Fellowship of Ethereum Magicians][5])

**用途**

* Trusted Enclave が「生データ＋タイムスタンプ」を署名して入力真正性を保証
* サーバが「共有乱数キー構成情報」を署名して改竄不可能にする

**特性と採用メリット**

* 決定論的生成で乱数漏えい事故を回避
* Jubjub 上では小鍵・小署名（64 B）かつ検証が定数時間で SNARK 回路にも適合([Espresso][7])
* 離散対数安全性で 128 bit 相当，EdDSA と互換の実装資産が豊富

---

### NIZK-PK (zk-SNARK)

**採用プリミティブ**

* **Groth16 zk-SNARK**（BLS12-381 pairing）([Medium][8], [Alpen Labs][9])

**用途**

* クライアントが「Pedersen コミット済み $k_c$ と署名付き入力が正しく LDP 処理された」ことを一括で証明
* サーバは 1 回のペアリング検証で真偽判定

**特性と採用メリット**

* 証明サイズが **約 200 B** と定数で通信量が極小([Medium][8])
* 検証はミリ秒級でスループット高，サーバ負荷 5–7 ms/ユーザ程度を実測報告([Alpen Labs][9])
* Trusted setup をセミホーネストなサーバに委ねられるため運用が容易
* 既存ライブラリ（ark-groth16 など）をそのまま利用でき，実装コストが低い

[1]: https://eprint.iacr.org/2016/827.pdf?utm_source=chatgpt.com "[PDF] Security Analysis of BLAKE2's Modes of Operation"
[2]: https://www.iacr.org/workshops/fse2017/slides/08-01.pdf?utm_source=chatgpt.com "[PDF] Security Analysis of BLAKE2's Modes of Operation - IACR"
[3]: https://crypto.stackexchange.com/questions/9418/how-random-is-the-shared-secret-in-the-diffie-hellman-key-agreement?utm_source=chatgpt.com "How random is the shared secret in the Diffie Hellman key agreement"
[4]: https://www.rareskills.io/post/pedersen-commitment?utm_source=chatgpt.com "What are Pedersen Commitments and How They Work - RareSkills"
[5]: https://ethereum-magicians.org/t/eip-2494-baby-jubjub-elliptic-curve/3968?utm_source=chatgpt.com "EIP-2494: Baby Jubjub Elliptic Curve - Ethereum Magicians"
[6]: https://en.wikipedia.org/wiki/Commitment_scheme?utm_source=chatgpt.com "Commitment scheme - Wikipedia"
[7]: https://espresso.discourse.group/t/espresso-zk-light-client/23?utm_source=chatgpt.com "Espresso ZK Light Client - Cryptography"
[8]: https://medium.com/%40mehialiabadi/plonk-vs-groth16-50254c157196?utm_source=chatgpt.com "Plonk vs Groth16 - by Mehri Rezaei - Medium"
[9]: https://www.alpenlabs.io/blog/current-state-of-snarks?utm_source=chatgpt.com "Current state of SNARKs - Alpen Labs"

---

## 1  概要まとめ（先に結論）

VLDPPipeline は **128 bit 相当の安全性** と **zk-SNARK 内での計算効率** を両立させるために，

| 用途          | 採用プリミティブ                                           | 主な理由                                                                                                       |
| ----------- | -------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| 署名          | Schnorr（Jubjub 上，Blake2s 派生ハッシュ）                   | 決定論的で乱数漏えいの危険を回避しつつ，EdDSA より回路制約が約 2–2.5 倍少ない ([Cryptology ePrint Archive][1], [Chainlink][2])             |
| コミットメント     | Pedersen **vector** commitment（Jubjub，4 bit ウィンドウ） | 情報理論的ハイディング＋加法ホモモルフィズム，かつ zk-SNARK で効率的 ([Cryptology ePrint Archive][1], [Cryptography Stack Exchange][3]) |
| ハッシュ／CRH    | Blake2s-256                                        | 標準化済み・高速・SNARK での計算量が少ない ([Cryptology ePrint Archive][1], [IETF Datatracker][4])                           |
| PRF         | Blake2s を鍵付きで使用（種 $k=k_c\oplus k_s$）               | 実装容易・同じハッシュを使い回せるためコードベースを縮約 ([Cryptology ePrint Archive][1])                                              |
| NIZK        | Groth16 zk-SNARK                                   | 定数サイズ ≈ 200 B，検証高速；trusted-setup はセミホーネストサーバを前提に許容 ([Cryptology ePrint Archive][1], [Medium][5])           |
| Merkle tree | Blake2s-based                                      | 上記 CRH を再利用して一貫性と実装簡素化を確保 ([Cryptology ePrint Archive][1])                                                 |
| 楕円曲線        | (Baby) Jubjub                                      | SNARK に適した Edwards 型で完全加算則・高速演算 ([Iden3 Documentation][6])                                                 |

---

## 2  乱数生成・PRF の具体

1. **二者協調シード**

   * クライアントが乱数キー $k_c$ を Pedersen でコミット → サーバが乱数キー $k_s$ を署名付きで返却。
   * 双方が $k=k_c\oplus k_s$ を共有し，毎ラウンド固定シード $s_j$ と合わせて

     $$
       \rho_{i,j}= \mathrm{PRF}_{\mathrm{Blake2s}}(k, s_j)
     $$

     を算出して LDP ノイズを生成 ([Cryptology ePrint Archive][1])。
2. **利点**

   * どちらか一方が乱数を支配できず，PRF 出力は公開検証不要。
   * Blake2s は鍵付き MAC として設計されており PRF への流用が安全 ([IETF Datatracker][4])。

---

## 3  デジタル署名（Schnorr）

* **用途**

  1. Trusted Enclave が生データ + タイムスタンプを署名 → 「入力真正性」を証明。
  2. サーバが $(pk_i, cm_{k_c}, k_s)$ に署名 → 「乱数キーが改竄されていない」ことをクライアントへ示す。

* **理由**

  * Edwards 系（Jubjub）での Schnorr は定数時間演算かつ回路制約が小さく，zk-SNARK に好適 ([Cryptology ePrint Archive][1], [Cryptology ePrint Archive][7])。
  * 決定論的生成ゆえ秘密乱数 $r$ 漏えいリスクを排除 ([Chainlink][2])。

---

## 4  コミットメント（Pedersen vector）

* **構造** $C = g^{m}\, h^{r}$ を Jubjub 上でベクトル拡張。
* **特性**

  * **情報理論的ハイディング**：開示前に内容が一切判別不可。
  * **計算量的バインディング**：離散対数困難性に帰着。
  * **加法ホモモルフィズム**：複数キーを一括コミットでき，乱数ベクトル処理で効率 ([Cryptography Stack Exchange][3], [ZKDocs][8])。
* **使い所** クライアントの秘密キー $k_c$ をコミットし，サーバは開示前にバインディングだけを信頼。

---

## 5  NIZK 証明（Groth16）

* **選択理由**

  * 証明サイズが定数 ≈ 200 B，通信量 200–485 B/クライアントに収まる ([Cryptology ePrint Archive][1], [Medium][5])。
  * 検証はミリ秒級で，サーバ負荷 5–7 ms/クライアント ([Cryptology ePrint Archive][1])。
  * Trusted Setup はサーバを semi-honest と仮定し，trapdoor をクライアントと共有しないため現実的 ([Cryptology ePrint Archive][1])。

---

## 6  曲線とライブラリ

* **Baby/Jubjub**

  * BLS12-381 上のサブグループで，完全加算則により回路最適化が容易 ([Iden3 Documentation][6])。
  * Arkworks のガジェットをそのまま利用し，Pedersen・Schnorr・SNARK すべて同曲線で統一 ([Cryptology ePrint Archive][1])。

---

## 7  まとめ

VLDPPipeline は **“可証性・プライバシ・性能”** という３要件を満たすために，

* **Schnorr + Pedersen + Blake2s + Groth16** という「SNARK 向け実績と実装容易性が高い組合せ」を採用。
* 乱数は **クライアントとサーバの XOR 合成鍵 + Blake2s-PRF** で生成し，
* NIZK には **Groth16** を使って常に短い証明を提供。

これにより，128 bit 安全性を保ったまま **クライアント 2 秒以下・サーバ検証 7 ms 以下** のスループットを実現しています ([Cryptology ePrint Archive][1])。

[1]: https://eprint.iacr.org/2024/1042.pdf "Efficient Verifiable Differential Privacy with Input Authenticity in the Local and Shuffle Model"
[2]: https://chain.link/education-hub/schnorr-signature?utm_source=chatgpt.com "What Is a Schnorr Signature? - Chainlink"
[3]: https://crypto.stackexchange.com/questions/9704/why-is-the-pedersen-commitment-computationally-binding?utm_source=chatgpt.com "Why is the Pedersen commitment computationally binding?"
[4]: https://datatracker.ietf.org/doc/html/rfc7693.html?utm_source=chatgpt.com "RFC 7693 - The BLAKE2 Cryptographic Hash and Message ..."
[5]: https://medium.com/%40aannkkiittaa/zk-snarks-explained-the-power-of-groth16-7790311e5f22?utm_source=chatgpt.com "zk-SNARKs Explained: The Power of Groth16 - Medium"
[6]: https://iden3-docs.readthedocs.io/en/latest/iden3_repos/research/publications/zkproof-standards-workshop-2/baby-jubjub/baby-jubjub.html?utm_source=chatgpt.com "Baby Jubjub — iden3 0.1 documentation"
[7]: https://eprint.iacr.org/2013/418.pdf?utm_source=chatgpt.com "[PDF] On Tight Security Proofs for Schnorr Signatures"
[8]: https://www.zkdocs.com/docs/zkdocs/commitments/pedersen/?utm_source=chatgpt.com "Pedersen Commitments - ZKDocs"

以下では **VLDPPipeline** を構成する暗号プリミティブを「乱数生成」「デジタル署名」「コミットメント」「NIZK 証明」の４グループに分け，代表的な方式ごとの特性・典型用途を比較しながら，最後に本論文の**脅威モデル**とその意図を整理します。

---

## 乱数生成方式の比較

| 区分            | 代表方式                                | 主要特性                                                 | 典型用途・導入例                             |
| ------------- | ----------------------------------- | ---------------------------------------------------- | ------------------------------------ |
| **協調型（対話あり）** | **Diffie–Hellman 共有シード**            | ➀双方向の指数演算で共通シークレットを生成<br>➁外部観測者には予測不能だが当事者同士は再現可     | TLS の前段で“乱数種”を共有し，PFS を確保            |
|               | **Commit-and-Reveal コインフリップ**       | 各参加者がビットをコミット→同時公開．一方が細工すると検証で失敗するが，途中放棄（abort）耐性は弱い | 公平な抽選・ゲームサーバーの乱択など                   |
| **一方向・検証可能**  | **VRF（Verifiable Random Function）** | 出力と同時に「正しく計算した」証明が付く．非対話・公開検証可能                      | Algorand ではステーク重み抽選に VRF 出力を採用       |
|               | **drand ビーコン**                      | t-of-n BLS しきい値署名で各ラウンドのビット列を共同生成．公開値は誰でも検証可能・偏り不可   | Filecoin／NIST RandBeacon などの公共乱数サービス |

**ポイント**

* VLDPPipeline では「サーバー＋クライアントで共同生成したシード」を使い，クライアントが一方的にノイズを仕込めないようにする設計が自然です。
* 公開検証が要らない局面では DH 共有シードが最も軽量，一方で公開乱数を回収したい場合は VRF や drand のような“証明付き”が好まれます。

---

## デジタル署名方式の比較

| 方式                  | 安全根拠                           | サイズ/速度                                    | 代表的な実利用             |                                   |                  |
| ------------------- | ------------------------------ | ----------------------------------------- | ------------------- | --------------------------------- | ---------------- |
| **ECDSA**           | 楕円曲線版 DSA                      | 秘密鍵 32 B，署名 64–72 B．ハードウェア実装多数            | Bitcoin トランザクション認可  |                                   |                  |
| **EdDSA (Ed25519)** | Twist-safe Edwards 曲線＋RFC 8032 | 署名 64 B／検証が高速・定数時間．署名が**決定論的**で乱数漏えいリスク低減 | Signal／OpenSSH キーペア |                                   |                  |
| **ElGamal 署名**      | 離散対数問題                         | 署名 2 ×                                    | p                   | ，ランダム性必須．メッセージ可分性（homomorphic）を持つ | 古典的学術例；現代システムでは稀 |

**選択指針**

* VLDPPipeline が求めるのは「入力が本物か」を高速で検証することなので，小鍵・高速検証の ECDSA／EdDSA が現実的です。TEE 内に秘密鍵を封じ込めれば鍵漏えい耐性も強化できます。

---

## コミットメント方式

| 方式           | Hiding               | Binding         | メリット                         | 代表利用例                               |
| ------------ | -------------------- | --------------- | ---------------------------- | ----------------------------------- |
| **ハッシュ系**    | 計算量的                 | 計算量的            | 実装がハッシュだけで簡単                 | Git オブジェクト ID など                    |
| **Pedersen** | **情報理論的**に隠蔽，計算量的に束縛 | 離散対数仮定の下で二重開示不可 | パラメータ固定で何度でも開示できる／加法ホモモルフィズム | Bulletproofs の値コミット，Coin-flip の下位部品 |

Pedersen は「後で開示できるが改竄不能」という特性が強く，公平な乱数生成や範囲証明で重宝されます。

---

## NIZK 証明方式

| 方式                      | trusted setup | 証明サイズ           | 検証コスト         | 主な採用例                      |
| ----------------------- | ------------- | --------------- | ------------- | -------------------------- |
| **Σ-プロトコル＋Fiat–Shamir** | 不要            | 証明＝公開鍵＋2スカラーで線形 | 非対話化後も軽量      | Schnorr 署名，Discrete-log 証明 |
| **Groth16 zk-SNARK**    | **要**（電気的に固定） | 〜200 B で一定      | 検証ms級と極小      | Zcash Sapling 取引           |
| **Bulletproofs**        | 不要            | 証明長 O(log n)    | 検証 O(n)；バッチ化可 | 暗号通貨の機密送金／レンジ証明            |

**使い分けの目安**

* 「証明は短く／検証は激速／セットアップも許容」の場合は Groth16。
* 「公開鍵生成者を絶対に信用できない」環境では Bulletproofs や Σ-系を採用し，証明サイズ増は許容する。

---

## 脅威モデルの整理と意図

### 役割ごとの前提

| アクター       | 想定                                   | なぜその設定か                              |
| ---------- | ------------------------------------ | ------------------------------------ |
| **クライアント** | 完全に**悪意的**・相互に共謀可                    | 少数の不正者でも統計を歪め得るため，最悪ケースを想定           |
| **サーバー**   | **セミホーネスト**（手順通りだが推測は行う）             | 大規模集計役を単純化し，TEE＋署名/NIZK による検証で安全性を担保 |
| **シャッフラー** | **honest-but-curious**（Mixnet ノード相当） | 出力経路を隠してプライバシー増幅を狙うが，データ改竄はしない前提     |
| **ネットワーク** | 盗聴可能・改竄不可能 (TLS 等)                   | 暗号チャネルは敷設済みと仮定                       |

### 補足：Mixnet と Trusted Enclave

* **Mixnet** は複数のプロキシ（ミックス）がメッセージをシャッフルして次ホップへ送る匿名通信網で，送信元と送信先のリンクを切断する。VLDPPipeline ではシャッフラーを１段の mix と見なす設計。
* **Trusted Execution Environment (例 Intel SGX)** は CPU 内に暗号化されたエンクレーブを設け，OS さえ触れない形で鍵と生データを保持・計算できる。入力真正性の署名鍵をここに格納し，外部ロジックを悪意的にしても鍵漏えいを防ぎます。

### このモデルから言えること

1. **入力改竄**：TEE 署名検証で排除。
2. **出力改竄**：NIZK 検証で排除。
3. **識別リスク**：シャッフラー（Mixnet 相当）＋LDP ノイズで (ε, δ)-DP を維持。
4. **セットアップ信頼**：Groth16 等の trusted setup を採るか否かは，社会的信頼度と性能要件で選択。

---

## まとめ

* **乱数生成**は DH や VRF／drand など“誰が乱数を支配しない”プロトコルを選ぶと公平性が高い。
* **署名方式**は鍵管理と検証コストで EdDSA/ECDSA が主流，ElGamal は同態性が必要なニッチ用途向け。
* **コミットメント**は Pedersen が「強い隠蔽＋開示可能」で多目的に使える。
* **NIZK**は「サイズ／検証／信頼」の三者トレードオフ：Groth16（速いが setup 必須）と Bulletproofs（setup 不要だが検証線形）が両極にあり，Σ-系はシンプル実装向け。
* VLDPPipeline の脅威モデルは「悪意クライアント＋好奇心サーバ＋honest シャッフラー」を想定し，TEE と mixnet で“真正性・匿名性・検証可能性”を同時に満たすよう構成されている。

これでご要望の「方式ごとの特性比較」と「脅威モデルの背景説明」を網羅しました。追加の深掘りや数式レベルの詳細が必要であればお知らせください！
