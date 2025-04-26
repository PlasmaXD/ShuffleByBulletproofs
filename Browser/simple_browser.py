import sys
from PyQt5.QtWidgets import QApplication, QLineEdit, QVBoxLayout, QWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

class SimpleBrowser(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SimpleBrowser")
        self.resize(1024, 768)

        # レイアウト
        layout = QVBoxLayout(self)

        # アドレスバー
        self.url_bar = QLineEdit(self)
        self.url_bar.returnPressed.connect(self.load_url)
        layout.addWidget(self.url_bar)

        # Web表示エリア
        self.web_view = QWebEngineView(self)
        layout.addWidget(self.web_view)

        # 初期ページ
        self.url_bar.setText("https://www.google.com")
        self.load_url()

    def load_url(self):
        url_text = self.url_bar.text()
        if not url_text.startswith(("http://", "https://")):
            url_text = "http://" + url_text
        self.web_view.load(QUrl(url_text))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    browser = SimpleBrowser()
    browser.show()
    sys.exit(app.exec_())
