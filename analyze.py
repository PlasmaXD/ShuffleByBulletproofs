import csv
import os
import ast
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter

REPORTS_DIR = "_reports"

def analyze_reports():
    # レポートの読み込み
    reports = []
    try:
        with open(os.path.join(REPORTS_DIR, "reports.csv"), "r") as f:
            reader = csv.reader(f)
            next(reader)  # ヘッダーをスキップ
            for row in reader:
                if len(row) >= 2:  # 行に十分な要素があることを確認
                    reports.append((int(row[0]), int(row[1])))
        print(f"読み込まれたレポート数: {len(reports)}")
    except Exception as e:
        print(f"レポートの読み込み中にエラーが発生しました: {e}")
        return
    
    # マッピングの読み込み
    mapping = []
    try:
        with open(os.path.join(REPORTS_DIR, "mapping.csv"), "r") as f:
            reader = csv.reader(f)
            next(reader)  # ヘッダーをスキップ
            for row in reader:
                if len(row) >= 3:  # 行に十分な要素があることを確認
                    try:
                        # ブルーム値を整数として解析
                        bloom_value = int(row[2])
                        mapping.append((row[0], int(row[1]), bloom_value))
                    except ValueError:
                        # 文字列が整数でない場合、リスト形式として解析を試みる
                        try:
                            bloom_list = ast.literal_eval(row[2])
                            if isinstance(bloom_list, list):
                                # リストの場合、整数に変換（ビットマスクとして）
                                bloom_int = 0
                                for bit in bloom_list:
                                    bloom_int |= (1 << bit)
                                mapping.append((row[0], int(row[1]), bloom_int))
                        except:
                            print(f"マッピング行の解析に失敗しました: {row}")
        print(f"読み込まれたマッピング数: {len(mapping)}")
    except Exception as e:
        print(f"マッピングの読み込み中にエラーが発生しました: {e}")
        return
    
    # デバッグ情報
    print("レポートの例:")
    for i, (cohort, rappor) in enumerate(reports[:5]):
        print(f"  {i}: コホート={cohort}, RAPPOR値={rappor} (2進数: {bin(rappor)})")
    
    print("マッピングの例:")
    for i, (value, cohort, bloom) in enumerate(mapping[:5]):
        print(f"  {i}: 値='{value}', コホート={cohort}, ブルーム値={bloom} (2進数: {bin(bloom)})")
    
    # コホートごとにレポートをグループ化
    cohort_reports = {}
    for cohort, rappor in reports:
        if cohort not in cohort_reports:
            cohort_reports[cohort] = []
        cohort_reports[cohort].append(rappor)
    
    # 各コホートで最も頻繁に報告された値を見つける
    cohort_counts = {}
    for cohort, rappor_list in cohort_reports.items():
        counter = Counter(rappor_list)
        cohort_counts[cohort] = counter
    
    # マッピングと照合して最も可能性の高い値を見つける
    value_matches = []
    for value, cohort, bloom in mapping:
        if cohort in cohort_counts:
            for rappor_value, count in cohort_counts[cohort].items():
                # ビットマスクの比較: ブルームフィルタのビットパターンが一致するか確認
                # RAPPORでは、ランダム化によりビットが変わる可能性があるため、完全一致ではなく
                # ビットの重なりの度合いで判断する
                bit_overlap = bin(bloom & rappor_value).count('1')
                bloom_bits = bin(bloom).count('1')
                
                # 一定以上の重なりがある場合にマッチとみなす
                # ここでは、ブルームフィルタのビットの50%以上が一致する場合にマッチとする
                if bloom_bits > 0 and bit_overlap >= bloom_bits * 0.5:
                    match_strength = bit_overlap / bloom_bits  # 一致度
                    value_matches.append((value, count * match_strength))
    
    # 値ごとに集計
    value_totals = {}
    for value, count in value_matches:
        if value not in value_totals:
            value_totals[value] = 0
        value_totals[value] += count
    
    # 結果の表示
    print("\n分析結果:")
    if not value_totals:
        print("  マッチする値が見つかりませんでした。")
    else:
        for value, count in sorted(value_totals.items(), key=lambda x: x[1], reverse=True):
            print(f"  {value}: {count:.2f}")
    
    # 結果のプロット
    if value_totals:
        plt.figure(figsize=(10, 6))
        plt.bar(value_totals.keys(), value_totals.values())
        plt.title("RAPPOR Analysis Results")
        plt.xlabel("Values")
        plt.ylabel("Count")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(REPORTS_DIR, "results.pdf"))
        print(f"結果プロットを保存しました: {os.path.join(REPORTS_DIR, 'results.pdf')}")
    
    # 結果をCSVに保存
    with open(os.path.join(REPORTS_DIR, "results.csv"), "w") as f:
        writer = csv.writer(f)
        writer.writerow(["value", "count"])
        for value, count in sorted(value_totals.items(), key=lambda x: x[1], reverse=True):
            writer.writerow([value, count])
    print(f"結果を保存しました: {os.path.join(REPORTS_DIR, 'results.csv')}")

if __name__ == "__main__":
    analyze_reports()
