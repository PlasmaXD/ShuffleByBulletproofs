# performance_test.py
import time
import os
import json
import random
import matplotlib.pyplot as plt
import numpy as np
from verifiable_shuffler import VerifiableShuffler

def measure_performance(num_reports_list, iterations=5):
    """
    様々なレポート数でZKPありとなしの処理時間を比較する
    
    Args:
        num_reports_list: テストするレポート数のリスト
        iterations: 各設定で実行する反復回数
    
    Returns:
        結果の辞書
    """
    results = {
        "num_reports": num_reports_list,
        "without_zkp": [],
        "without_zkp_std": [],
        "with_zkp": [],
        "with_zkp_std": []
    }
    
    # ZKP検証用のインスタンスを作成
    verifiable_shuffler = VerifiableShuffler(use_rust_implementation=False)
    
    for num_reports in num_reports_list:
        print(f"\nTesting with {num_reports} reports...")
        
        # テスト用レポートを生成
        reports = []
        for i in range(num_reports):
            reports.append({
                'cohort': i % 64,
                'rappor': random.randint(0, 65535)
            })
        
        # ZKPなしの処理時間を測定
        times_without_zkp = []
        for i in range(iterations):
            print(f"  Without ZKP - Iteration {i+1}/{iterations}", end="\r")
            start_time = time.time()
            
            # 通常のシャッフル処理
            shuffled_reports = reports.copy()
            random.shuffle(shuffled_reports)
            
            end_time = time.time()
            times_without_zkp.append(end_time - start_time)
        
        # ZKPありの処理時間を測定
        times_with_zkp = []
        for i in range(iterations):
            print(f"  With ZKP - Iteration {i+1}/{iterations}   ", end="\r")
            start_time = time.time()
            
            # ZKPを使用したシャッフル処理
            verifiable_shuffler.commit_reports(reports)
            shuffled_reports = verifiable_shuffler.shuffle_commitments(reports)
            verification_result = verifiable_shuffler.verify_shuffle()
            
            end_time = time.time()
            times_with_zkp.append(end_time - start_time)
        
        # 結果を保存
        results["without_zkp"].append(np.mean(times_without_zkp))
        results["without_zkp_std"].append(np.std(times_without_zkp))
        results["with_zkp"].append(np.mean(times_with_zkp))
        results["with_zkp_std"].append(np.std(times_with_zkp))
        
        print(f"\nReports: {num_reports}, Without ZKP: {np.mean(times_without_zkp):.4f}s, With ZKP: {np.mean(times_with_zkp):.4f}s")
    
    return results

def plot_results(results):
    """結果をグラフにプロットする"""
    plt.figure(figsize=(12, 10))
    
    # 処理時間のプロット
    plt.subplot(2, 1, 1)
    plt.errorbar(
        results["num_reports"], 
        results["without_zkp"], 
        yerr=results["without_zkp_std"],
        marker='o', 
        label="Without ZKP"
    )
    plt.errorbar(
        results["num_reports"], 
        results["with_zkp"], 
        yerr=results["with_zkp_std"],
        marker='s', 
        label="With ZKP"
    )
    plt.xlabel("Number of Reports")
    plt.ylabel("Processing Time (seconds)")
    plt.title("ZKP Performance Comparison")
    plt.legend()
    plt.grid(True)
    
    # オーバーヘッド比率のプロット
    plt.subplot(2, 1, 2)
    overhead_ratio = [zkp/no_zkp for zkp, no_zkp in zip(results["with_zkp"], results["without_zkp"])]
    plt.plot(results["num_reports"], overhead_ratio, marker='o')
    plt.xlabel("Number of Reports")
    plt.ylabel("ZKP Overhead Ratio")
    plt.title("ZKP Overhead Ratio (higher means more overhead)")
    plt.grid(True)
    
    plt.tight_layout()
    
    # 結果ディレクトリを作成
    os.makedirs("_results", exist_ok=True)
    
    # グラフを保存
    plt.savefig("_results/zkp_performance_comparison.pdf")
    plt.savefig("_results/zkp_performance_comparison.png")
    print(f"Plots saved to _results/zkp_performance_comparison.pdf and .png")
    
    # 結果をJSONとして保存
    with open("_results/zkp_performance_results.json", "w") as f:
        # numpyの値をJSONシリアライズ可能にする
        serializable_results = {
            "num_reports": results["num_reports"],
            "without_zkp": [float(x) for x in results["without_zkp"]],
            "without_zkp_std": [float(x) for x in results["without_zkp_std"]],
            "with_zkp": [float(x) for x in results["with_zkp"]],
            "with_zkp_std": [float(x) for x in results["with_zkp_std"]],
            "overhead_ratio": overhead_ratio
        }
        json.dump(serializable_results, f, indent=2)
    print(f"Results saved to _results/zkp_performance_results.json")

if __name__ == "__main__":
    print("Starting ZKP Performance Test")
    
    # テストするレポート数の設定
    # 小さな値から始めて、徐々に大きくする
    num_reports_list = [10, 50, 100, 250, 500, 1000]
    
    # 各設定での反復回数
    iterations = 5
    
    print(f"Testing with report counts: {num_reports_list}")
    print(f"Iterations per test: {iterations}")
    
    # パフォーマンスを測定
    results = measure_performance(num_reports_list, iterations)
    
    # 結果をプロット
    plot_results(results)
    
    print("Performance test completed!")
