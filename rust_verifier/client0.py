import rappor  # rappor.pyをインポート

# RAPPORパラメータの設定
params_obj = rappor.Params()
params_obj.num_cohorts = 64      # コホート数
params_obj.num_hashes = 2        # ハッシュ関数数
params_obj.num_bloombits = 16    # ブルームフィルタのビット数
params_obj.prob_p = 0.5          # 永続的ランダム応答の確率
params_obj.prob_q = 0.75         # 瞬間的ランダム応答の確率
params_obj.prob_f = 0.5          # 偽陽性率

# エンコーダーの初期化（1回だけ行う）
cohort = 0  # または適切なコホート番号
secret = "secret_key".encode('utf-8')  # 文字列をUTF-8でエンコードしてバイト型に変換
irr_rand = rappor.SecureIrrRand(params_obj)
encoder = rappor.Encoder(params_obj, cohort, secret, irr_rand)

# ユーザーの値をエンコード
value = "value_to_encode".encode('utf-8')  # 文字列をバイト列にエンコード
encoded_value = encoder.encode(value)  # これだけで完了します

# サーバーに送信するデータ
report = {
    'cohort': cohort,
    'rappor': encoded_value  # rappor_bitsではなくencoded_valueを使用
}

# レポートの表示（確認用）
print("Report:", report)
