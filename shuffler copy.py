# shuffler.py
from flask import Flask, request, jsonify
import requests
import random
import time
import json
import os
import threading

app = Flask(__name__)

# レポートのバッファ
report_buffer = []
buffer_lock = threading.Lock()

# シャッフラーの設定
BATCH_SIZE = 10  # バッチサイズ（実際の実装ではより大きな値を使用）
SERVER_URL = "http://localhost:5000/report"  # 分析サーバーのURL
SHUFFLE_INTERVAL = 60  # シャッフル間隔（秒）

@app.route('/submit', methods=['POST'])
def receive_report():
    """クライアントからレポートを受信"""
    try:
        report_data = request.json
        
        # 必須フィールドの検証
        if 'cohort' not in report_data or 'rappor' not in report_data:
            return jsonify({"error": "Missing required fields"}), 400
        
        # レポートをバッファに追加
        with buffer_lock:
            report_buffer.append(report_data)
            current_size = len(report_buffer)
        
        return jsonify({
            "status": "success", 
            "message": f"Report added to buffer (current size: {current_size})"
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def shuffle_and_forward():
    """バッファ内のレポートをシャッフルして転送"""
    while True:
        time.sleep(SHUFFLE_INTERVAL)
        
        with buffer_lock:
            if len(report_buffer) == 0:
                continue
                
            # バッファからレポートを取得
            reports_to_shuffle = report_buffer.copy()
            report_buffer.clear()
        
        # レポートをシャッフル
        random.shuffle(reports_to_shuffle)
        
        print(f"Shuffling and forwarding {len(reports_to_shuffle)} reports")
        
        # シャッフルされたレポートを分析サーバーに転送
        for report in reports_to_shuffle:
            try:
                response = requests.post(
                    SERVER_URL,
                    json=report,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    print(f"Error forwarding report: {response.text}")
            except Exception as e:
                print(f"Exception forwarding report: {e}")

if __name__ == '__main__':
    # シャッフルスレッドを開始
    shuffle_thread = threading.Thread(target=shuffle_and_forward, daemon=True)
    shuffle_thread.start()
    
    # シャッフラーサーバーを起動
    app.run(host='0.0.0.0', port=5001)
