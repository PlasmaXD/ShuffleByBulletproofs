from flask import Flask, request, jsonify
import csv
import os
import json
import datetime

"""
RAPPOR サーバー実装

このスクリプトは、シャッフラーからRAPPORレポートを受信し、
分析のために保存するサーバー実装です。

主な機能:
- レポート受信エンドポイントの提供
- 受信したレポートの検証
- レポートのCSVファイルへの保存
"""

app = Flask(__name__)

# レポートを保存するディレクトリ
REPORTS_DIR = "_reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

@app.route('/report', methods=['POST'])
def receive_report():
    """
    シャッフラーからのレポートを受信するエンドポイント
    """
    try:
        report_data = request.json
        
        # 必須フィールドの検証
        if 'cohort' not in report_data or 'rappor' not in report_data:
            return jsonify({"error": "Missing required fields"}), 400
        
        # レポートをCSVファイルに追加
        with open(os.path.join(REPORTS_DIR, "reports.csv"), "a") as f:
            writer = csv.writer(f)
            writer.writerow([report_data['cohort'], report_data['rappor']])
        
        # 受信時刻を記録（オプション）
        timestamp = datetime.datetime.now().isoformat()
        
        return jsonify({
            "status": "success", 
            "timestamp": timestamp
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def server_status():
    """
    サーバーのステータスを返すエンドポイント
    """
    try:
        # レポート数を取得
        report_count = 0
        if os.path.exists(os.path.join(REPORTS_DIR, "reports.csv")):
            with open(os.path.join(REPORTS_DIR, "reports.csv"), "r") as f:
                report_count = sum(1 for line in f) - 1  # ヘッダー行を除く
        
        return jsonify({
            "status": "running",
            "report_count": report_count,
            "timestamp": datetime.datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # CSVファイルのヘッダーを作成
    if not os.path.exists(os.path.join(REPORTS_DIR, "reports.csv")):
        with open(os.path.join(REPORTS_DIR, "reports.csv"), "w") as f:
            writer = csv.writer(f)
            writer.writerow(["cohort", "rappor"])
    
    print(f"サーバーを起動しています... (レポート保存先: {os.path.abspath(REPORTS_DIR)})")
    app.run(host='0.0.0.0', port=5000)
