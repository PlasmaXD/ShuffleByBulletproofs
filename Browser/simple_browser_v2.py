import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QLineEdit, QVBoxLayout, QWidget, QPushButton, QListWidget, QHBoxLayout
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

HISTORY_FILE = "history.txt"

class SimpleBrowser(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SimpleBrowser with History")
        self.resize(1024, 768)

        # 履歴リスト（メモリ上）
        self.history = []

        # レイアウト
        main_layout = QVBoxLayout(self)
        nav_layout = QHBoxLayout()

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

        # リンククリックやJavaScriptによる遷移を検知してURL更新
        self.web_view.urlChanged.connect(self.on_url_changed)

        # 履歴リストウィジェット（非表示）
        self.history_list = QListWidget(self)
        self.history_list.hide()
        self.history_list.itemDoubleClicked.connect(self.on_history_item_double_clicked)
        main_layout.addWidget(self.history_list)

        # 履歴ファイルから読み込み
        self.load_history_from_file()

        # 初期ページ読み込み
        self.url_bar.setText("https://www.google.com")
        self.load_url()

    def load_url(self):
        """アドレスバーのURLでページを読み込む"""
        url_text = self.url_bar.text().strip()
        if not url_text.startswith(("http://", "https://")):
            url_text = "http://" + url_text
        self.web_view.load(QUrl(url_text))

    def on_url_changed(self, qurl):
        """ページ遷移時にURLバーを更新＆履歴追加"""
        url = qurl.toString()
        # URLバーを書き換え
        self.url_bar.setText(url)

        # 履歴追加
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"{now} {url}"
        # 既に同じ最新エントリがあるなら重複登録を避ける
        if not self.history or self.history[-1] != entry:
            self.history.append(entry)
            self.history_list.addItem(entry)
            self.append_history_to_file(entry)

    def append_history_to_file(self, entry: str):
        """履歴ファイルに1行ずつ追記"""
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(entry + "\n")

    def load_history_from_file(self):
        """起動時に履歴ファイルを読み込み、メモリと表示用リストに登録"""
        if not os.path.exists(HISTORY_FILE):
            return
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    self.history.append(line)
                    self.history_list.addItem(line)

    def show_history(self):
        """履歴リストの表示／非表示をトグル"""
        if self.history_list.isVisible():
            self.history_list.hide()
        else:
            self.history_list.show()

    def on_history_item_double_clicked(self, item):
        """履歴をダブルクリックしたらそのURLを読み込む"""
        # "YYYY-MM-DD HH:MM:SS http://..." なので3番目の要素以降をURLとみなす
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
