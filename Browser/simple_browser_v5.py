import sys
import os
import random
from datetime import datetime
from collections import Counter

import numpy as np
import matplotlib.pyplot as plt

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLineEdit, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QMessageBox
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

# プロジェクト構成に合わせてパスを追加
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if base_dir not in sys.path:
    sys.path.append(base_dir)

import rappor  # 同一フォルダにおいた RAPPOR 実装
from cms_ldp import CMS_LDP_Client, CMS_LDP_Aggregator
from verifiable_shuffler import VerifiableShuffler

# RAPPORパラメータの初期化
_rappor_params = rappor.Params()
_rappor_params.num_cohorts = 64
_rappor_params.num_hashes = 2
_rappor_params.num_bloombits = 16
_rappor_params.prob_p = 0.5
_rappor_params.prob_q = 0.75
_rappor_params.prob_f = 0.5

def encode_url_rappor(url: str, cohort: int = None) -> dict:
    if cohort is None:
        cohort = random.randint(0, _rappor_params.num_cohorts - 1)
    secret = f"secret_key_{cohort}".encode('utf-8')
    irr_rand = rappor.SecureIrrRand(_rappor_params)
    encoder = rappor.Encoder(_rappor_params, cohort, secret, irr_rand)
    irr_value = encoder.encode(url.encode('utf-8'))
    return {'cohort': cohort, 'irr': irr_value}

HISTORY_FILE     = "history_dummy.txt"
ENC_HISTORY_FILE = "encoded_history_dummy.txt"

class SimpleBrowser(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SimpleBrowser with RAPPOR, LDP & Shuffler")
        self.resize(1024, 768)

        # LDP(CMS) クライアント／アグリゲータ
        WIDTH, DEPTH = 128, 4
        P, Q = 0.5, 0.75
        self.lpd_client     = CMS_LDP_Client(width=WIDTH, depth=DEPTH, prob_p=P, prob_q=Q)
        self.lpd_aggregator = CMS_LDP_Aggregator(width=WIDTH, depth=DEPTH, prob_p=P, prob_q=Q)
        # シャッフラー
        self.shuffler = VerifiableShuffler(use_rust_implementation=True)

        # レイアウト
        main_layout = QVBoxLayout(self)
        nav_layout  = QHBoxLayout()

        # 戻る／進むボタン
        self.back_btn = QPushButton("← 戻る", self)
        self.back_btn.setEnabled(False)
        self.back_btn.clicked.connect(self.on_back)
        nav_layout.addWidget(self.back_btn)

        self.forward_btn = QPushButton("進む →", self)
        self.forward_btn.setEnabled(False)
        self.forward_btn.clicked.connect(self.on_forward)
        nav_layout.addWidget(self.forward_btn)

        # アドレスバー
        self.url_bar = QLineEdit(self)
        self.url_bar.returnPressed.connect(self.load_url)
        nav_layout.addWidget(self.url_bar)

        # 履歴表示ボタン
        hist_btn = QPushButton("履歴表示", self)
        hist_btn.clicked.connect(self.show_history)
        nav_layout.addWidget(hist_btn)

        # コミット／シャッフル／検証／集計ボタン
        self.commit_btn    = QPushButton("Commit", self)
        self.commit_btn.clicked.connect(self.on_commit)
        nav_layout.addWidget(self.commit_btn)

        self.shuffle_btn   = QPushButton("Shuffle", self)
        self.shuffle_btn.clicked.connect(self.on_shuffle)
        nav_layout.addWidget(self.shuffle_btn)

        self.verify_btn    = QPushButton("Verify", self)
        self.verify_btn.clicked.connect(self.on_verify)
        nav_layout.addWidget(self.verify_btn)

        self.aggregate_btn = QPushButton("集計", self)
        self.aggregate_btn.clicked.connect(self.on_aggregate)
        nav_layout.addWidget(self.aggregate_btn)

        main_layout.addLayout(nav_layout)

        # Web 表示
        self.web_view = QWebEngineView(self)
        main_layout.addWidget(self.web_view)
        self.web_view.urlChanged.connect(self.on_url_changed)
        self.web_view.loadFinished.connect(self.update_nav_buttons)

        # GUI 履歴リスト
        self.history = []
        self.history_list = QListWidget(self)
        self.history_list.hide()
        self.history_list.itemDoubleClicked.connect(self.on_history_item_double_clicked)
        main_layout.addWidget(self.history_list)

        # 履歴ファイル読み込み
        self.load_history_files()

        # 初期ページ
        self.url_bar.setText("https://www.google.com")
        self.load_url()

    def load_url(self):
        url_text = self.url_bar.text().strip()
        if not url_text.startswith(("http://","https://")):
            url_text = "http://" + url_text
        self.web_view.load(QUrl(url_text))

    def on_url_changed(self, qurl):
        url = qurl.toString()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # (A) 生の URL を history.txt に追記
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(f"{now} {url}\n")

        # (B) RAPPOR で encode した結果を encoded_history.txt に追記
        dp = encode_url_rappor(url)
        with open(ENC_HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(f"{now} cohort={dp['cohort']} irr={dp['irr']}\n")

        # (C) CMS＋LDP ingest はこれまでどおり URL で
        rec = self.lpd_client.privatize(url)
        self.lpd_aggregator.ingest(rec)

        # GUI 上の履歴リストにも生 URL を追加
        entry = f"{now} {url}"
        self.history.append(entry)
        self.history_list.addItem(entry)

    def update_nav_buttons(self):
        self.back_btn.setEnabled(self.web_view.history().canGoBack())
        self.forward_btn.setEnabled(self.web_view.history().canGoForward())

    def on_back(self):
        if self.web_view.history().canGoBack():
            self.web_view.back()

    def on_forward(self):
        if self.web_view.history().canGoForward():
            self.web_view.forward()

    def show_history(self):
        if self.history_list.isVisible():
            self.history_list.hide()
        else:
            self.history_list.show()

    def on_history_item_double_clicked(self, item):
        parts = item.text().split(' ', 2)
        if len(parts) == 3:
            url = parts[2]
            self.url_bar.setText(url)
            self.load_url()

    def load_history_files(self):
        # history.txt 読み込み
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    entry = line.strip()
                    if not entry: continue
                    self.history.append(entry)
                    self.history_list.addItem(entry)
        # encoded_history.txt がなければ空ファイル作成
        if not os.path.exists(ENC_HISTORY_FILE):
            open(ENC_HISTORY_FILE, 'w', encoding='utf-8').close()

    def on_commit(self):
        reports = []
        if os.path.exists(ENC_HISTORY_FILE):
            with open(ENC_HISTORY_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split(" ", 2)
                    if len(parts) != 3:
                        continue
                    # parts[2] は "cohort=xx irr=yyyy"
                    c_part, i_part = parts[2].split()
                    cohort = int(c_part.split("=")[1])
                    irr    = int(i_part.split("=")[1])
                    # Rust 実装では reports 中身は不要
                    reports.append({})
        commitments = self.shuffler.commit_reports(reports)
        QMessageBox.information(self, "Commit", f"{len(commitments)} 件コミット生成")

    def on_shuffle(self):
        reports = []
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split(' ', 2)
                    if len(parts) == 3:
                        reports.append({"url": parts[2]})
        self.shuffler.shuffle_commitments(reports)
        QMessageBox.information(self, "Shuffle", "レポートをシャッフルしました")

    def on_verify(self):
        valid = self.shuffler.verify_shuffle()
        if valid:
            QMessageBox.information(self, "Verify", "シャッフル検証に成功しました")
        else:
            QMessageBox.critical(self, "Verify", "シャッフル検証に失敗しました")

    def on_aggregate(self):
        # １) スケッチをリセット（必要なら毎回新規集計できるように）
        WIDTH, DEPTH = 128, 4
        P, Q = 0.5, 0.75
        self.lpd_aggregator = CMS_LDP_Aggregator(width=WIDTH, depth=DEPTH, prob_p=P, prob_q=Q)

        # ２) ファイルから全アクセスを読み込んで ingest
        true_cnt = Counter()
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split(' ', 2)
                    if len(parts) != 3:
                        continue
                    url = parts[2]
                    true_cnt[url] += 1

                    # ← **ここでスケッチにレコードを登録**
                    rec = self.lpd_client.privatize(url)
                    self.lpd_aggregator.ingest(rec)

        # ３) 真の出現回数と推定値を計算
        urls      = list(true_cnt.keys())
        true_vals = [true_cnt[u]                       for u in urls]
        est_cnt   = [self.lpd_aggregator.estimate_url(u) for u in urls]

        # ４) MAE / MAPE を計算・表示
        errors = [abs(e - t) for e, t in zip(est_cnt, true_vals)]
        mae  = np.mean(errors)
        mape = np.mean([err/t for err, t in zip(errors, true_vals) if t > 0])

        text = ""
        for u, e, t in zip(urls, est_cnt, true_vals):
            text += f"{u}: 推定={e:.1f}, 真={t}\n"
        text += f"\nMAE={mae:.2f}, MAPE={mape*100:.2f}%"
        QMessageBox.information(self, "集計結果と評価", text)

        # ５) グラフ表示
        x = np.arange(len(urls))
        plt.figure()
        plt.bar(x - 0.2, true_vals, 0.4, label='True')
        plt.bar(x + 0.2, est_cnt,   0.4, label='Estimate')
        plt.xticks(x, urls, rotation=45, ha='right')
        plt.legend()
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    browser = SimpleBrowser()
    browser.show()
    sys.exit(app.exec_())
