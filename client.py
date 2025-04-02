import rappor  # rappor.pyをインポート
import requests  # HTTPリクエスト用
import json
import random
import time

"""
RAPPOR (Randomized Aggregatable Privacy-Preserving Ordinal Response) クライアントの実装例

このスクリプトは、RAPPORプライバシー保護メカニズムを使用してデータをエンコードし、
シャッフラーを経由してサーバーに送信するクライアント実装です。

RAPPOR は、プライバシーを保護しながら統計データを収集するための差分プライバシーに基づくシステムです。
このクライアントは、個人のデータを収集サーバーに送信する前にローカルで匿名化します。

主な機能:
- RAPPORパラメータの設定
- エンコーダーの初期化
- ユーザー値のエンコード
- シャッフラーへのレポート送信

要件:
- rappor パッケージがインストールされていること
- requests パッケージがインストールされていること
"""

def encode_and_send_value(value, cohort=None):
    """
    値をエンコードしてシャッフラーに送信する関数
    
    Args:
        value: エンコードする値（文字列）
        cohort: コホート番号（Noneの場合はランダムに選択）
    """
    # RAPPORパラメータの設定
    params_obj = rappor.Params()
    params_obj.num_cohorts = 64      # コホート数
    params_obj.num_hashes = 2        # ハッシュ関数数
    params_obj.num_bloombits = 16    # ブルームフィルタのビット数
    params_obj.prob_p = 0.5          # 永続的ランダム応答の確率
    params_obj.prob_q = 0.75         # 瞬間的ランダム応答の確率
    params_obj.prob_f = 0.5          # 偽陽性率

    # コホートの選択（指定がなければランダム）
    if cohort is None:
        cohort = random.randint(0, params_obj.num_cohorts - 1)
    
    # エンコーダーの初期化
    secret = f"secret_key_{cohort}".encode('utf-8')  # 文字列をUTF-8でエンコードしてバイト型に変換
    irr_rand = rappor.SecureIrrRand(params_obj)
    encoder = rappor.Encoder(params_obj, cohort, secret, irr_rand)

    # ユーザーの値をエンコード
    value_bytes = value.encode('utf-8')  # 文字列をバイト列にエンコード
    encoded_value = encoder.encode(value_bytes)

    # サーバーに送信するデータ
    report = {
        'cohort': cohort,
        'rappor': encoded_value
    }

    # シャッフラーにレポートを送信
    try:
        # シャッフラーのURLを指定
        shuffler_url = "http://localhost:5001/submit"
        
        # レポートをJSON形式で送信
        response = requests.post(
            shuffler_url,
            json=report,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"レポート送信結果: {response.status_code}")
        if response.status_code == 200:
            print(f"  成功: {response.json().get('message', '')}")
        else:
            print(f"  エラー: {response.text}")
            
    except Exception as e:
        print(f"送信エラー: {e}")

if __name__ == "__main__":
    # テスト用の値のリスト
    test_values = ["value1", "value2", "value3", "value4", "value5"]
    
    # ランダムに値を選択してエンコード・送信
    selected_value = random.choice(test_values)
    print(f"選択された値: {selected_value}")
    
    # 値をエンコードしてシャッフラーに送信
    encode_and_send_value(selected_value)
