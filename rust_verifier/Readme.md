

## 実行方法
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
cargo install bulletproofs curve25519-dalek-ng merlin rand serde serde_json blake3 hex
cd bulletproofs_example
cargo build --release
cp target/release/shuffle_verifier ../
```

## 実行方法v2
```  bash
# 0. ビルド
cargo build --release
alias shuffler=./target/release/rust-shuffler

# 1. Pedersen コミットメント生成
shuffler commit reports.json > commits.json

# 2. シャッフル + 証明生成
#    permutation.json は {"commitments":[...],"permutation":[...]} 形式
shuffler shuffle permutation.json > shuffled.json

# 3. 検証
#    verify.json は {"original_commitments":[...],
#                    "shuffled_commitments":[...],
#                    "proof":"<hex>"} 形式
shuffler verify verify.json
```
## `setup.rs` 
`setup.rs` は **「一度だけパラメータ（params.bin）と検証鍵（vk.bin）を生成して保存しておく専用ツール」** として想定していた補助ファイルです。  
ただし、先ほどお渡しした **`main.rs` は “params.bin が無ければ自動生成”** するように書き換えてあるため、**なくても動きます**。

---

## 使い分け

| パターン | `setup.rs` 必要？ | 理由 |
|---------|----------------|------|
| **手元で試す / CI で都度ビルド** | **不要** | `main.rs` が自動生成するので簡単 |
| **本番でキーを厳格に管理**<br>（生成マシンと検証マシンを分けたい） | **あると便利** | “Trusted setup 専用バイナリ” にして鍵管理ポリシを明確化できる |

---



### ビルドと実行

```bash
# 1. setup だけビルド
rustc src/setup.rs -o setup
./setup
# → params.bin / vk.bin ができる

# 2. 以降は main バイナリを通常通り利用
cargo build --release
```

---

### 結論

- **手軽に試すなら `main.rs` だけで OK**  
  (`params.bin` が無いときだけ自動生成するロジック)
- **鍵生成を分離管理したい場合だけ** `setup.rs` を用意して “Trusted Setup” を別プロセスで行ってください。