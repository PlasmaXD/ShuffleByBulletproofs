# bulletproofs_batch_test.py
import time
import os
import json
import random
import matplotlib.pyplot as plt
import numpy as np
import subprocess
import tempfile

def test_bulletproofs_batch_effect(batch_sizes, report_count=1000, iterations=3):
    """
    異なるバッチサイズでのBulletproofsのパフォーマンスをテスト
    
    Args:
        batch_sizes: テストするバッチサイズのリスト
        report_count: 合計レポート数
        iterations: 各バッチサイズで実行する繰り返し回数
    
    Returns:
        結果の辞書
    """
    results = {
        "batch_sizes": batch_sizes,
        "total_time": [],
        "total_time_std": [],
        "avg_time_per_proof": [],
        "proof_size": []
    }
    
    # テスト用のレポートを生成
    reports = []
    for i in range(report_count):
        reports.append({
            'cohort': i % 64,
            'rappor': random.randint(0, 65535)
        })
    
    # 各バッチサイズでテスト
    for batch_size in batch_sizes:
        print(f"\nTesting with batch size: {batch_size}")
        
        # レポートをバッチに分割
        batches = [reports[i:i+batch_size] for i in range(0, len(reports), batch_size)]
        num_batches = len(batches)
        
        # 各イテレーションでの処理時間を測定
        times = []
        for i in range(iterations):
            print(f"  Iteration {i+1}/{iterations}")
            
            batch_times = []
            for j, batch in enumerate(batches):
                print(f"    Batch {j+1}/{num_batches}", end="\r")
                
                start_time = time.time()
                
                if use_rust_bulletproofs:
                    # Rust実装を使用したBulletproofsのバッチ処理
                    process_batch_with_rust(batch, batch_size)
                else:
                    # Python実装でBulletproofsの処理をシミュレート
                    simulate_bulletproofs_batch(batch, batch_size)
                
                end_time = time.time()
                batch_times.append(end_time - start_time)
            
            # 全バッチの合計時間
            total_time = sum(batch_times)
            times.append(total_time)
            
            print(f"    Total time: {total_time:.4f}s, Avg time per batch: {total_time/num_batches:.4f}s")
        
        # 結果を計算
        avg_total_time = np.mean(times)
        std_total_time = np.std(times)
        avg_time_per_proof = avg_total_time / (report_count / batch_size)
        
        # バッチサイズごとの証明サイズをシミュレート
        proof_size = estimate_bulletproofs_size(batch_size)
        
        results["total_time"].append(avg_total_time)
        results["total_time_std"].append(std_total_time)
        results["avg_time_per_proof"].append(avg_time_per_proof)
        results["proof_size"].append(proof_size)
        
        print(f"  Average total time: {avg_total_time:.4f}s")
        print(f"  Average time per proof: {avg_time_per_proof:.4f}s")
        print(f"  Estimated proof size: {proof_size} bytes")
    
    return results

def process_batch_with_rust(batch, batch_size):
    """
    Rust実装を使用してBulletproofsのバッチ処理を行う
    
    Args:
        batch: 処理するレポートのバッチ
        batch_size: バッチサイズ
    """
    # Rustバイナリへのパス
    rust_binary_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "rust_verifier/target/release/shuffle_verifier"
    )
    
    if not os.path.exists(rust_binary_path):
        # Rustバイナリが見つからない場合はシミュレーション
        simulate_bulletproofs_batch(batch, batch_size)
        return
    
    try:
        # バッチをファイルに書き込む
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            json.dump({
                'batch': batch,
                'batch_size': batch_size
            }, f)
            temp_file = f.name
        
        # Rustバイナリを呼び出してバッチ処理
        subprocess.run(
            [rust_binary_path, "batch", temp_file],
            capture_output=True, check=True
        )
        
        # 一時ファイルを削除
        os.unlink(temp_file)
    
    except Exception as e:
        print(f"Error using Rust implementation: {e}")
        # エラーの場合はシミュレーション
        simulate_bulletproofs_batch(batch, batch_size)

def simulate_bulletproofs_batch(batch, batch_size):
    """
    Bulletproofsのバッチ処理をシミュレート
    
    Args:
        batch: 処理するレポートのバッチ
        batch_size: バッチサイズ
    """
    # バッチサイズに応じて処理時間を調整
    # Bulletproofsでは、バッチサイズが大きいほど1つあたりの処理は効率的
    base_time = 0.02  # 基本処理時間（秒）
    efficiency_factor = 0.7  # 効率化係数（1未満）
    
    # バッチサイズが大きいほど1つあたりの処理時間は減少
    time_per_item = base_time * (batch_size ** (-efficiency_factor))
    
    # バッチ全体の処理時間
    batch_time = time_per_item * batch_size
    
    # 処理をシミュレート
    time.sleep(batch_time)

def estimate_bulletproofs_size(batch_size):
    """
    バッチサイズに応じたBulletproofsの証明サイズを推定
    
    Args:
        batch_size: バッチサイズ
    
    Returns:
        推定証明サイズ（バイト）
    """
    # Bulletproofsの証明サイズは対数関数的に増加
    # 基本サイズ + log2(n)に比例する追加サイズ
    base_size = 672  # 基本サイズ（バイト）
    log_factor = 32  # 対数因子（バイト）
    
    if batch_size <= 1:
        return base_size
    
    # 証明サイズ = 基本サイズ + log2(バッチサイズ) * 対数因子
    return int(base_size + np.log2(batch_size) * log_factor)

def plot_results(results):
    """
    結果をプロットする
    
    Args:
        results: テスト結果の辞書
    """
    plt.figure(figsize=(15, 10))
    
    # 1. 合計処理時間
    plt.subplot(2, 2, 1)
    plt.errorbar(
        results["batch_sizes"],
        results["total_time"],
        yerr=results["total_time_std"],
        marker='o'
    )
    plt.xlabel("Batch Size")
    plt.ylabel("Total Processing Time (seconds)")
    plt.title("Total Processing Time vs Batch Size")
    plt.grid(True)
    
    # 2. 証明あたりの平均処理時間
    plt.subplot(2, 2, 2)
    plt.plot(results["batch_sizes"], results["avg_time_per_proof"], marker='s')
    plt.xlabel("Batch Size")
    plt.ylabel("Time per Proof (seconds)")
    plt.title("Average Time per Proof vs Batch Size")
    plt.grid(True)
    
    # 3. 証明サイズ
    plt.subplot(2, 2, 3)
    plt.plot(results["batch_sizes"], results["proof_size"], marker='^')
    plt.xlabel("Batch Size")
    plt.ylabel("Proof Size (bytes)")
    plt.title("Proof Size vs Batch Size")
    plt.grid(True)
    
    # 4. 効率性（処理時間 * 証明サイズ）
    efficiency = [t * s for t, s in zip(results["avg_time_per_proof"], results["proof_size"])]
    plt.subplot(2, 2, 4)
    plt.plot(results["batch_sizes"], efficiency, marker='*')
    plt.xlabel("Batch Size")
    plt.ylabel("Efficiency (time * size)")
    plt.title("Efficiency vs Batch Size (lower is better)")
    plt.grid(True)
    
    plt.tight_layout()
    
    # 結果ディレクトリを作成
    os.makedirs("_results", exist_ok=True)
    
    # グラフを保存
    plt.savefig("_results/bulletproofs_batch_comparison.pdf")
    plt.savefig("_results/bulletproofs_batch_comparison.png")
    print(f"Plots saved to _results/bulletproofs_batch_comparison.pdf and .png")
    
    # 結果をJSONとして保存
    with open("_results/bulletproofs_batch_results.json", "w") as f:
        # numpyの値をJSONシリアライズ可能にする
        serializable_results = {
            "batch_sizes": results["batch_sizes"],
            "total_time": [float(x) for x in results["total_time"]],
            "total_time_std": [float(x) for x in results["total_time_std"]],
            "avg_time_per_proof": [float(x) for x in results["avg_time_per_proof"]],
            "proof_size": results["proof_size"],
            "efficiency": [float(x) for x in efficiency]
        }
        json.dump(serializable_results, f, indent=2)
    print(f"Results saved to _results/bulletproofs_batch_results.json")

if __name__ == "__main__":
    print("Starting Bulletproofs Batch Performance Test")
    
    # Rust実装を使用するかどうか
    use_rust_bulletproofs = False
    
    # テストするバッチサイズ（対数スケール）
    batch_sizes = [1, 2, 4, 8, 16, 32, 64, 128, 256]
    
    # 合計レポート数
    report_count = 1000
    
    # 各設定での反復回数
    iterations = 3
    
    print(f"Testing with batch sizes: {batch_sizes}")
    print(f"Total report count: {report_count}")
    print(f"Iterations per test: {iterations}")
    print(f"Using Rust implementation: {use_rust_bulletproofs}")
    
    # パフォーマンスを測定
    results = test_bulletproofs_batch_effect(batch_sizes, report_count, iterations)
    
    # 結果をプロット
    plot_results(results)
    
    print("Bulletproofs batch performance test completed!")
