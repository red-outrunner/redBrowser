import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QLineEdit, QTabWidget,
    QPushButton, QVBoxLayout, QWidget, QLabel, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEngineDownloadItem
from PyQt5.QtGui import QIcon


class WebBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 Web Browser")
        self.setGeometry(100, 100, 1200, 800)

        self.history_file = "browser_history.json"
        self.bookmarks_file = "bookmarks.json"
        self.load_history()
        self.load_bookmarks()

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)

        self.add_new_tab()

        self.nav_toolbar = QToolBar("Navigation")
        self.addToolBar(Qt.TopToolBarArea, self.nav_toolbar)

        self.back_button = QPushButton("← Back")
        self.back_button.clicked.connect(self.navigate_back)
        self.nav_toolbar.addWidget(self.back_button)

        self.forward_button = QPushButton("→ Forward")
        self.forward_button.clicked.connect(self.navigate_forward)
        self.nav_toolbar.addWidget(self.forward_button)

        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.clicked.connect(self.refresh_page)
        self.nav_toolbar.addWidget(self.refresh_button)

        self.download_button = QPushButton("⬇️ Download")
        self.download_button.clicked.connect(self.open_downloads_tab)
        self.nav_toolbar.addWidget(self.download_button)

        self.address_bar = QLineEdit()
        self.address_bar.returnPressed.connect(self.load_url)
        self.nav_toolbar.addWidget(self.address_bar)

        self.settings_menu = self.menuBar().addMenu("Settings")
        self.save_history_action = self.settings_menu.addAction("Save History")
        self.save_history_action.triggered.connect(self.save_history)

        self.save_bookmarks_action = self.settings_menu.addAction("Save Bookmarks")
        self.save_bookmarks_action.triggered.connect(self.save_bookmarks)

        self.clear_history_action = self.settings_menu.addAction("Clear History")
        self.clear_history_action.triggered.connect(self.clear_history)

        self.clear_bookmarks_action = self.settings_menu.addAction("Clear Bookmarks")
        self.clear_bookmarks_action.triggered.connect(self.clear_bookmarks)

        self.download_manager = {}

    def open_downloads_tab(self):
        self.add_new_tab("chrome://downloads/")

    def add_new_tab(self, url="https://www.google.com"):
        tab = QWidget()
        layout = QVBoxLayout()
        web_view = QWebEngineView()
        web_view.load(QUrl(url))
        web_view.titleChanged.connect(lambda title: self.tabs.setTabText(self.tabs.indexOf(tab), title))
        web_view.urlChanged.connect(self.update_address_bar)
        web_view.loadFinished.connect(self.on_load_finished)

        profile = QWebEngineProfile.defaultProfile()
        profile.downloadRequested.connect(self.handle_download)

        layout.addWidget(web_view)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "New Tab")
        self.tabs.setCurrentWidget(tab)

    def close_tab(self, index):
        self.tabs.removeTab(index)

    def load_url(self):
        url = self.address_bar.text()
        if not url.startswith("http"):
            url = "https://" + url
        current_tab = self.tabs.currentWidget()
        web_view = current_tab.findChild(QWebEngineView)
        web_view.load(QUrl(url))

    def update_address_bar(self, url):
        self.address_bar.setText(url.toString())

    def navigate_back(self):
        current_tab = self.tabs.currentWidget()
        web_view = current_tab.findChild(QWebEngineView)
        web_view.back()

    def navigate_forward(self):
        current_tab = self.tabs.currentWidget()
        web_view = current_tab.findChild(QWebEngineView)
        web_view.forward()

    def refresh_page(self):
        current_tab = self.tabs.currentWidget()
        web_view = current_tab.findChild(QWebEngineView)
        web_view.reload()

    def on_load_finished(self, ok):
        if ok:
            current_tab = self.tabs.currentWidget()
            web_view = current_tab.findChild(QWebEngineView)
            url = web_view.url().toString()
            self.add_to_history(url)

    def add_to_history(self, url):
        if url not in self.history:
            self.history.append(url)
            self.save_history()

    def save_history(self):
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f)
        except Exception as e:
            print(f"Error saving history: {e}")

    def load_history(self):
        self.history = []
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
            except Exception as e:
                print(f"Error loading history: {e}")

    def save_bookmarks(self):
        try:
            with open(self.bookmarks_file, 'w') as f:
                json.dump(self.bookmarks, f)
        except Exception as e:
            print(f"Error saving bookmarks: {e}")

    def load_bookmarks(self):
        self.bookmarks = {}
        if os.path.exists(self.bookmarks_file):
            try:
                with open(self.bookmarks_file, 'r') as f:
                    self.bookmarks = json.load(f)
            except Exception as e:
                print(f"Error loading bookmarks: {e}")

    def handle_download(self, download):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", download.suggestedFileName())
        if file_path:
            download.setPath(file_path)
            download.accept()
            self.download_manager[download.suggestedFileName()] = download
            download.finished.connect(lambda: self.download_finished(download))
            download.downloadProgress.connect(self.download_progress)

    def download_progress(self, bytes_received, bytes_total):
        if bytes_total > 0:
            percent = (bytes_received / bytes_total) * 100
            print(f"Download Progress: {percent:.2f}%")

    def download_finished(self, download):
        if download.state() == QWebEngineDownloadItem.DownloadCompleted:
            QMessageBox.information(self, "Download Complete", f"File saved to: {download.path()}")
        elif download.state() == QWebEngineDownloadItem.DownloadInterrupted:
            QMessageBox.warning(self, "Download Failed", "The download was interrupted.")

    def clear_history(self):
        self.history = []
        self.save_history()
        QMessageBox.information(self, "History Cleared", "Browsing history has been cleared.")

    def clear_bookmarks(self):
        self.bookmarks = {}
        self.save_bookmarks()
        QMessageBox.information(self, "Bookmarks Cleared", "Bookmarks have been cleared.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    browser = WebBrowser()
    browser.show()
    sys.exit(app.exec_())
