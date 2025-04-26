import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QLineEdit, QVBoxLayout, QWidget,
    QPushButton, QListWidget, QHBoxLayout
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

HISTORY_FILE = "history.txt"

class SimpleBrowser(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SimpleBrowser with History")
        self.resize(1024, 768)

        self.history = []

        # 全体レイアウト
        main_layout = QVBoxLayout(self)
        nav_layout = QHBoxLayout()

        # 戻るボタン
        self.back_btn = QPushButton("← 戻る", self)
        self.back_btn.setEnabled(False)
        self.back_btn.clicked.connect(self.on_back)
        nav_layout.addWidget(self.back_btn)

        # 進むボタン
        self.forward_btn = QPushButton("進む →", self)
        self.forward_btn.setEnabled(False)
        self.forward_btn.clicked.connect(self.on_forward)
        nav_layout.addWidget(self.forward_btn)

        # アドレスバー
        self.url_bar = QLineEdit(self)
        self.url_bar.returnPressed.connect(self.load_url)
        nav_layout.addWidget(self.url_bar)

        # 履歴表示ボタン
        show_history_btn = QPushButton("履歴表示", self)
        show_history_btn.clicked.connect(self.show_history)
        nav_layout.addWidget(show_history_btn)

        main_layout.addLayout(nav_layout)

        # Web表示エリア
        self.web_view = QWebEngineView(self)
        main_layout.addWidget(self.web_view)

        # ページ遷移を監視
        self.web_view.urlChanged.connect(self.on_url_changed)
        self.web_view.loadFinished.connect(self.update_nav_buttons)

        # 履歴リストウィジェット
        self.history_list = QListWidget(self)
        self.history_list.hide()
        self.history_list.itemDoubleClicked.connect(self.on_history_item_double_clicked)
        main_layout.addWidget(self.history_list)

        self.load_history_from_file()

        # 初期ページ
        self.url_bar.setText("https://www.google.com")
        self.load_url()

    def load_url(self):
        url_text = self.url_bar.text().strip()
        if not url_text.startswith(("http://", "https://")):
            url_text = "http://" + url_text
        self.web_view.load(QUrl(url_text))

    def on_url_changed(self, qurl):
        url = qurl.toString()
        self.url_bar.setText(url)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"{now} {url}"
        if not self.history or self.history[-1] != entry:
            self.history.append(entry)
            self.history_list.addItem(entry)
            self.append_history_to_file(entry)

    def update_nav_buttons(self):
        """戻る／進むボタンの有効・無効を切り替え"""
        self.back_btn .setEnabled(self.web_view.history().canGoBack())
        self.forward_btn.setEnabled(self.web_view.history().canGoForward())

    def on_back(self):
        if self.web_view.history().canGoBack():
            self.web_view.back()

    def on_forward(self):
        if self.web_view.history().canGoForward():
            self.web_view.forward()

    def append_history_to_file(self, entry: str):
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(entry + "\n")

    def load_history_from_file(self):
        if not os.path.exists(HISTORY_FILE):
            return
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    self.history.append(line)
                    self.history_list.addItem(line)

    def show_history(self):
        if self.history_list.isVisible():
            self.history_list.hide()
        else:
            self.history_list.show()

    def on_history_item_double_clicked(self, item):
        parts = item.text().split(" ", 2)
        if len(parts) == 3:
            url = parts[2]
            self.url_bar.setText(url)
            self.load_url()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    browser = SimpleBrowser()
    browser.show()
    sys.exit(app.exec_())
