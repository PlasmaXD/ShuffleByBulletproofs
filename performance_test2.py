import time
import random
import numpy as np
import matplotlib.pyplot as plt

def compare_zkp_implementations(num_reports_list, iterations=5):
    results = {
        "num_reports": num_reports_list,
        "without_zkp": [],
        "with_zkp": [],
        "bulletproofs_zkp": []
    }
    
    for num_reports in num_reports_list:
        reports = [{'cohort': i % 64, 'rappor': random.randint(0, 65535)} for i in range(num_reports)]
        
        # ZKPなしの処理時間
        times_without_zkp = []
        for _ in range(iterations):
            start_time = time.time()
            shuffled_reports = reports.copy()
            random.shuffle(shuffled_reports)
            times_without_zkp.append(time.time() - start_time)
            
        # シミュレートされたZKPの処理時間
        times_with_zkp = []
        for _ in range(iterations):
            start_time = time.time()
            shuffled_reports = reports.copy()
            random.shuffle(shuffled_reports)
            # ZKP処理のシミュレーション
            time.sleep(0.01)
            times_with_zkp.append(time.time() - start_time)
            
        # Bulletproofs ZKPの処理時間
        times_bulletproofs = []
        for _ in range(iterations):
            start_time = time.time()
            shuffled_reports = reports.copy()
            random.shuffle(shuffled_reports)
            # Bulletproofs処理のシミュレーション
            time.sleep(0.02)
            times_bulletproofs.append(time.time() - start_time)
            
        # 結果を記録
        results["without_zkp"].append(np.mean(times_without_zkp))
        results["with_zkp"].append(np.mean(times_with_zkp))
        results["bulletproofs_zkp"].append(np.mean(times_bulletproofs))
    
    return results

# 様々なレポート数でテスト
num_reports_list = [10, 50, 100, 500, 1000]
results = compare_zkp_implementations(num_reports_list)

# 結果をプロット
plt.figure(figsize=(10, 6))
plt.plot(results["num_reports"], results["without_zkp"], marker="o", label="Without ZKP")
plt.plot(results["num_reports"], results["with_zkp"], marker="s", label="With ZKP (Simulated)")
plt.plot(results["num_reports"], results["bulletproofs_zkp"], marker="^", label="With ZKP (Bulletproofs)")

plt.xlabel("Number of Reports")
plt.ylabel("Processing Time (seconds)")
plt.title("Performance Comparison: ZKP vs Bulletproofs")
plt.legend()
plt.grid(True)
plt.savefig("zkp_performance_comparison.png")
plt.show()
