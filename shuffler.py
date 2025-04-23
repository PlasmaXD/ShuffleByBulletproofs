# shuffler.py 
from flask import Flask, request, jsonify
import requests
import random
import time
import json
import os
import threading
import hashlib
import datetime
from verifiable_shuffler import VerifiableShuffler  # 新たに追加

app = Flask(__name__)

# レポートのバッファ
report_buffer = []
buffer_lock = threading.Lock()

# シャッフルログ（検証用）
shuffle_log = []
log_lock = threading.Lock()

# シャッフラーの設定
BATCH_SIZE = 10  # バッチサイズ
SERVER_URL = "http://localhost:5000/report"  # 分析サーバーのURL
SHUFFLE_INTERVAL = 30  # シャッフル間隔（秒）
SHUFFLE_LOG_DIR = "_shuffle_logs"
ENABLE_ZKP = True  # ゼロ知識証明を有効にするフラグ
USE_RUST_ZKP = True  # Rust実装を使用するフラグ

os.makedirs(SHUFFLE_LOG_DIR, exist_ok=True)

# VerifiableShufflerのインスタンスを作成
verifiable_shuffler = VerifiableShuffler(use_rust_implementation=USE_RUST_ZKP)

@app.route('/submit', methods=['POST'])
def receive_report():
    """クライアントからレポートを受信するエンドポイント"""
    try:
        report_data = request.json
        
        # 必須フィールドの検証
        if 'cohort' not in report_data or 'rappor' not in report_data:
            return jsonify({"error": "Missing required fields"}), 400
        
        # レポートをバッファに追加
        with buffer_lock:
            report_buffer.append(report_data)
            current_size = len(report_buffer)
        
        # バッチサイズに達したらシャッフルをトリガー
        if current_size >= BATCH_SIZE:
            # 非同期でシャッフルを実行
            shuffle_thread = threading.Thread(target=shuffle_and_forward)
            shuffle_thread.daemon = True
            shuffle_thread.start()
        
        return jsonify({
            "status": "success", 
            "message": f"Report added to buffer (current size: {current_size})"
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def shuffle_and_forward():
    """バッファ内のレポートをシャッフルして転送する関数"""
    with buffer_lock:
        if len(report_buffer) == 0:
            return
            
        # バッファからレポートを取得
        reports_to_shuffle = report_buffer.copy()
        report_buffer.clear()
    
    print(f"Shuffling and forwarding {len(reports_to_shuffle)} reports")
    
    # シャッフル処理
    if ENABLE_ZKP:
        # ゼロ知識証明を使用したシャッフル
        try:
            # レポートのコミットメントを生成
            verifiable_shuffler.commit_reports(reports_to_shuffle)
            
            # レポートをシャッフルして証明を生成
            shuffled_reports = verifiable_shuffler.shuffle_commitments(reports_to_shuffle)
            
            # シャッフルを検証
            verification_result = verifiable_shuffler.verify_shuffle()
            
            if verification_result:
                print("Shuffle verification successful")
                
                # 検証データを保存
                verification_data = verifiable_shuffler.get_verification_data()
                timestamp = datetime.datetime.now().isoformat().replace(':', '-')
                log_path = os.path.join(SHUFFLE_LOG_DIR, f"shuffle_proof_{timestamp}.json")
                
                with open(log_path, 'w') as f:
                    json.dump({
                        'timestamp': timestamp,
                        'report_count': len(reports_to_shuffle),
                        'verification_result': verification_result,
                        'verification_data': verification_data
                    }, f, indent=2)
                
                # シャッフルされたレポートを使用
                reports_to_shuffle = shuffled_reports
            else:
                print("Shuffle verification failed, using original order")
                # 検証に失敗した場合は元の順序を使用（または別の対応）
        except Exception as e:
            print(f"Error during verifiable shuffle: {e}")
            # エラーが発生した場合は通常のシャッフル処理を続行
            random.shuffle(reports_to_shuffle)
    else:
        # 通常のシャッフル処理
        random.shuffle(reports_to_shuffle)
    
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

@app.route('/status', methods=['GET'])
def shuffler_status():
    """シャッフラーのステータスを返すエンドポイント"""
    with buffer_lock:
        current_size = len(report_buffer)
    
    with log_lock:
        shuffle_count = len(shuffle_log)
    
    # 検証ログの数を取得
    verification_logs = [f for f in os.listdir(SHUFFLE_LOG_DIR) if f.startswith('shuffle_proof_')]
    
    return jsonify({
        "status": "running",
        "buffer_size": current_size,
        "shuffle_count": shuffle_count,
        "verification_logs_count": len(verification_logs),
        "batch_size": BATCH_SIZE,
        "shuffle_interval": SHUFFLE_INTERVAL,
        "zkp_enabled": ENABLE_ZKP,
        "rust_zkp": USE_RUST_ZKP,
        "timestamp": datetime.datetime.now().isoformat()
    }), 200

@app.route('/verifications', methods=['GET'])
def list_verifications():
    """検証ログのリストを返すエンドポイント"""
    verification_logs = []
    
    for filename in os.listdir(SHUFFLE_LOG_DIR):
        if filename.startswith('shuffle_proof_'):
            try:
                with open(os.path.join(SHUFFLE_LOG_DIR, filename), 'r') as f:
                    log_data = json.load(f)
                    verification_logs.append({
                        'filename': filename,
                        'timestamp': log_data.get('timestamp'),
                        'report_count': log_data.get('report_count'),
                        'verification_result': log_data.get('verification_result')
                    })
            except Exception as e:
                print(f"Error reading verification log {filename}: {e}")
    
    return jsonify({
        "verifications": sorted(verification_logs, key=lambda x: x.get('timestamp', ''), reverse=True)
    }), 200

if __name__ == '__main__':
    # 定期的なシャッフルを行うスレッドを開始
    def periodic_shuffle():
        while True:
            time.sleep(SHUFFLE_INTERVAL)
            with buffer_lock:
                if len(report_buffer) > 0:
                    print(f"Periodic shuffle triggered ({len(report_buffer)} reports in buffer)")
                    shuffle_thread = threading.Thread(target=shuffle_and_forward)
                    shuffle_thread.daemon = True
                    shuffle_thread.start()
    
    # 定期的なシャッフルスレッドを開始
    periodic_thread = threading.Thread(target=periodic_shuffle, daemon=True)
    periodic_thread.start()
    
    print(f"Starting shuffler on port 5001 (ZKP enabled: {ENABLE_ZKP}, Rust ZKP: {USE_RUST_ZKP})")
    app.run(host='0.0.0.0', port=5001)
