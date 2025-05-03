import sys
import os
import random
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLineEdit, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QMessageBox
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

import rappor  # 同一フォルダに置いた RAPPOR 実装
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

HISTORY_FILE = "history.txt"

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

        # 履歴リスト
        self.history = []
        self.history_list = QListWidget(self)
        self.history_list.hide()
        self.history_list.itemDoubleClicked.connect(self.on_history_item_double_clicked)
        main_layout.addWidget(self.history_list)

        # 履歴ファイル読み込み
        self.load_history_from_file()

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
        self.url_bar.setText(url)
        # RAPPOR エンコード＆保存
        dp = encode_url_rappor(url)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"{now} cohort={dp['cohort']} irr={dp['irr']}"
        if not self.history or self.history[-1] != entry:
            self.history.append(entry)
            self.history_list.addItem(entry)
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(entry + "\n")
        # LDP(CMS) ingest
        rec = self.lpd_client.privatize(url)
        self.lpd_aggregator.ingest(rec)

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

    def load_history_from_file(self):
        if not os.path.exists(HISTORY_FILE):
            return
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(' ', 2)
                if len(parts) < 3:
                    continue
                self.history.append(line)
                self.history_list.addItem(line)

    # ボタン処理
    def on_commit(self):
        reports = []
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split(' ', 2)
                if len(parts) == 3:
                    reports.append({"url": parts[2]})
        commitments = self.shuffler.commit_reports(reports)
        QMessageBox.information(self, "Commit", f"{len(commitments)} 件コミット生成")

    def on_shuffle(self):
        reports = []
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
        unique_urls = set()
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split(' ', 2)
                if len(parts) == 3:
                    unique_urls.add(parts[2])
                    rec = self.lpd_client.privatize(parts[2])
                    self.lpd_aggregator.ingest(rec)
        text = ""
        for url in unique_urls:
            est = self.lpd_aggregator.estimate_url(url)
            text += f"{url}: {est:.1f}\n"
        QMessageBox.information(self, "集計結果", text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    browser = SimpleBrowser()
    browser.show()
    sys.exit(app.exec_())
