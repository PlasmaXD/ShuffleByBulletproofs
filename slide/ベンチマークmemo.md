  
```bash
Finished bench profile [optimized] target(s) in 0.06s
     Running unittests src/lib.rs (target/release/deps/rust_verifier2-85c262e3bd119b7f)

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/main.rs (target/release/deps/rust_verifier2-c06cb9d883868ec0)

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running benches/shuffle_bench.rs (target/release/deps/shuffle_bench-ee3bdde994ea4545)
Benchmarking shuffle/sum_preservation/100: Collecting 100 samples in estimated 8shuffle/sum_preservation/100
                        time:   [850.65 µs 851.04 µs 851.52 µs]
                        thrpt:  [117.44 Kelem/s 117.50 Kelem/s 117.56 Kelem/s]
Found 14 outliers among 100 measurements (14.00%)
  1 (1.00%) low mild
  6 (6.00%) high mild
  7 (7.00%) high severe
Benchmarking shuffle/permutation/100: Collecting 100 samples in estimated 5.0004shuffle/permutation/100 time:   [189.21 ns 189.32 ns 189.43 ns]
                        thrpt:  [527.89 Melem/s 528.22 Melem/s 528.53 Melem/s]
Found 5 outliers among 100 measurements (5.00%)
  4 (4.00%) high mild
  1 (1.00%) high severe
Benchmarking shuffle/sum_preservation/1000: Collecting 100 samples in estimated shuffle/sum_preservation/1000
                        time:   [8.5057 ms 8.5097 ms 8.5144 ms]
                        thrpt:  [117.45 Kelem/s 117.51 Kelem/s 117.57 Kelem/s]
Found 10 outliers among 100 measurements (10.00%)
  2 (2.00%) high mild
  8 (8.00%) high severe
Benchmarking shuffle/permutation/1000: Collecting 100 samples in estimated 5.000shuffle/permutation/1000
                        time:   [1.7406 µs 1.7452 µs 1.7508 µs]
                        thrpt:  [571.17 Melem/s 572.99 Melem/s 574.51 Melem/s]
Found 1 outliers among 100 measurements (1.00%)
  1 (1.00%) high mild
Benchmarking shuffle/sum_preservation/10000: Warming up for 3.0000 s
Warning: Unable to complete 100 samples in 5.0s. You may wish to increase target time to 8.5s, or reduce sample count to 50.
Benchmarking shuffle/sum_preservation/10000: Collecting 100 samples in estimatedshuffle/sum_preservation/10000
                        time:   [85.126 ms 85.228 ms 85.364 ms]
                        thrpt:  [117.15 Kelem/s 117.33 Kelem/s 117.47 Kelem/s]
Found 16 outliers among 100 measurements (16.00%)
  9 (9.00%) high mild
  7 (7.00%) high severe
Benchmarking shuffle/permutation/10000: Collecting 100 samples in estimated 5.13shuffle/permutation/10000
                        time:   [34.985 µs 34.996 µs 35.009 µs]
                        thrpt:  [285.64 Melem/s 285.75 Melem/s 285.84 Melem/s]
Found 11 outliers among 100 measurements (11.00%)
  1 (1.00%) low mild
  5 (5.00%) high mild
  5 (5.00%) high severe

```

## 概要  
`cargo bench` を実行すると、まずCargoが「ベンチマーク可能なターゲット」（libも含む）に含まれるユニットテストとベンチを一括して実行します。この例ではユニットテストが定義されていないため、最初の２つのセクションは「0 tests」となっています  ([benches" runs unit tests · Issue #6454 · rust-lang/cargo - GitHub](https://github.com/rust-lang/cargo/issues/6454?utm_source=chatgpt.com))。続いて `benches/shuffle_bench.rs` が Criterion.rs のカスタムハーネスで実行され、`shuffle_sum_preservation` と `shuffle_permutation` のベンチマークが走ります  ([bheisler/criterion.rs: Statistics-driven benchmarking library for Rust](https://github.com/bheisler/criterion.rs?utm_source=chatgpt.com))。  

## ベンチ結果の読み方  

### Benchmarking shuffle/sum_preservation/100  
- **time**: `[850.65 µs  851.04 µs  851.52 µs]` は“最速・平均・最遅”を 99% 信頼区間で示した実行時間です  ([Command-Line Output - Criterion.rs Documentation](https://bheisler.github.io/criterion.rs/book/user_guide/command_line_output.html?utm_source=chatgpt.com))。  
- **thrpt**: `[117.44 Kelem/s  117.50 Kelem/s  117.56 Kelem/s]` は「要素（element）あたりのスループット」で、1秒間に約11.7万要素を処理できることを表します  ([Advanced Configuration - Criterion.rs Documentation](https://bheisler.github.io/criterion.rs/book/user_guide/advanced_configuration.html?utm_source=chatgpt.com))。  

### Benchmarking shuffle/permutation/100  
- **time**: `[189.21 ns  189.32 ns  189.43 ns]` は単純な置換（コピー）処理のみの実行時間で、約0.19マイクロ秒と極めて高速です  ([Benchmarking With Inputs - Criterion.rs Documentation](https://bheisler.github.io/criterion.rs/book/user_guide/benchmarking_with_inputs.html?utm_source=chatgpt.com))。  
- **thrpt**: `[527.89 Melem/s  528.22 Melem/s  528.53 Melem/s]` は 5.2億要素／秒を超えるスループットで、コピーコストしか含まないため非常に高性能であることを示します  ([C++: The most important complexities - Sandor Dargo's Blog](https://www.sandordargo.com/blog/2023/11/15/most-important-complexities?utm_source=chatgpt.com))。  

## 規模依存性  
- `/1000` や `/10000` セクションでは入力サイズ N を変えて同様の計測を行っています。  
- `sum_preservation` は内部で全コミットメントの復号＋加算を行うため **O(N)** の処理時間増加が見られ、N が 10 倍になると時間もほぼ 10 倍になります  ([What is the most effective way of iterating a std::vector and why?](https://stackoverflow.com/questions/55606153/what-is-the-most-effective-way-of-iterating-a-stdvector-and-why?utm_source=chatgpt.com))。  
- `permutation` は単純なインデックスコピーのみ（こちらも **O(N)**）ですが、要素あたりのコストが非常に小さいため、スループットは N の増加にあまり影響されず高速を維持します  ([C++: The most important complexities - Sandor Dargo's Blog](https://www.sandordargo.com/blog/2023/11/15/most-important-complexities?utm_source=chatgpt.com))。  

## 外れ値検出  
- **Found 14 outliers among 100 measurements (14.00%)** は、Tukey 箱ひげ法に基づき統計的に異常と判断されたサンプルの割合です  ([tukey.rs - criterion/stats/univariate/outliers - Docs.rs](https://docs.rs/criterion/latest/src/criterion/stats/univariate/outliers/tukey.rs.html?utm_source=chatgpt.com))。  
- **high mild** / **high severe** の分類は、「内側フェンス」「外側フェンス」をそれぞれ超えたデータポイントで、CPUスケジューリングやメモリ割り込みによる遅延が原因となることがあります  ([Command-Line Output - Criterion.rs Documentation](https://bheisler.github.io/criterion.rs/book/user_guide/command_line_output.html?utm_source=chatgpt.com))。  
- 外れ値が一定以上ある場合は、他プロセスの干渉や電源管理設定など **ベンチ環境の安定性** を確認・調整する必要があります  ([Why does Criterion produce inconsistent output with subsequent runs?](https://stackoverflow.com/questions/74136113/why-does-criterion-produce-inconsistent-output-with-subsequent-runs?utm_source=chatgpt.com))。  

---

以上が出力結果の解釈です。`sum_preservation` は暗号演算を伴う分だけ遅く、`permutation` はコピーのみのため高速、という性能差が数値として明確に示されています。ベンチマーク結果を活用して、利用ケースに応じた最適化や設計判断を行ってください。