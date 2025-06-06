import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QLineEdit, QTabWidget,
    QPushButton, QVBoxLayout, QWidget, QLabel, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEngineDownloadItem, QWebEngineSettings
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
from PyQt5.QtGui import QIcon

class WebEngineUrlRequestInterceptor(QWebEngineUrlRequestInterceptor):
    """
    Custom URL request interceptor to modify headers, specifically the Content Security Policy.
    This allows us to enable features like WebAssembly that might be blocked by default.
    """
    def interceptRequest(self, info):
        """Intercepts network requests to modify headers."""
        # Corrected method from httpHeader to requestHeader to get the original CSP header
        original_csp = info.requestHeader(b"Content-Security-Policy")
        if original_csp:
            # Append our required permissions to the existing script-src directive
            new_csp = original_csp.decode('utf-8')
            if 'script-src' in new_csp:
                # Add wasm-unsafe-eval to the existing script-src directive
                new_csp = new_csp.replace("script-src", "script-src 'wasm-unsafe-eval'")
            else:
                # If no script-src, add our own
                new_csp += "; script-src 'self' 'unsafe-inline' 'unsafe-eval' 'wasm-unsafe-eval';"
            info.setHttpHeader(b"Content-Security-Policy", new_csp.encode('utf-8'))
        else:
            # If no CSP exists, create one with the necessary permissions
            info.setHttpHeader(b"Content-Security-Policy", b"script-src 'self' 'unsafe-inline' 'unsafe-eval' 'wasm-unsafe-eval'; object-src 'self';")


class WebBrowser(QMainWindow):
    """
    A simple web browser built with PyQt5.
    Features include tabbing, navigation, history, bookmarks, and a download manager.
    """
    def __init__(self):
        """Initializes the browser window and its components."""
        super().__init__()
        self.setWindowTitle("PyQt5 Web Browser")
        self.setGeometry(100, 100, 1200, 800)

        # File paths for storing history and bookmarks
        self.history_file = "browser_history.json"
        self.bookmarks_file = "bookmarks.json"
        
        # Load existing history and bookmarks
        self.load_history()
        self.load_bookmarks()

        # Main tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)
        
        # Set up the custom URL request interceptor for the default profile
        self.profile = QWebEngineProfile.defaultProfile()
        self.interceptor = WebEngineUrlRequestInterceptor()
        self.profile.setUrlRequestInterceptor(self.interceptor)

        # Set a modern user agent
        self.profile.setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")

        # Add the initial tab
        self.add_new_tab()

        # Navigation toolbar
        self.nav_toolbar = QToolBar("Navigation")
        self.addToolBar(Qt.TopToolBarArea, self.nav_toolbar)

        # Navigation buttons
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

        # Address bar
        self.address_bar = QLineEdit()
        self.address_bar.returnPressed.connect(self.load_url)
        self.nav_toolbar.addWidget(self.address_bar)

        # Settings menu
        self.settings_menu = self.menuBar().addMenu("Settings")
        self.save_history_action = self.settings_menu.addAction("Save History")
        self.save_history_action.triggered.connect(self.save_history)

        self.save_bookmarks_action = self.settings_menu.addAction("Save Bookmarks")
        self.save_bookmarks_action.triggered.connect(self.save_bookmarks)

        self.clear_history_action = self.settings_menu.addAction("Clear History")
        self.clear_history_action.triggered.connect(self.clear_history)

        self.clear_bookmarks_action = self.settings_menu.addAction("Clear Bookmarks")
        self.clear_bookmarks_action.triggered.connect(self.clear_bookmarks)

        # Dictionary to manage download items
        self.download_manager = {}

    def open_downloads_tab(self):
        """Creates and opens a new tab to display the list of downloads."""
        downloads_html = ""
        if not self.download_manager:
            downloads_html = "<tr><td colspan='3'>No downloads yet.</td></tr>"
        else:
            # Generate table rows for each download
            for filename, download_item in self.download_manager.items():
                state_map = {
                    QWebEngineDownloadItem.DownloadRequested: "Requested",
                    QWebEngineDownloadItem.DownloadInProgress: "In Progress",
                    QWebEngineDownloadItem.DownloadCompleted: "Completed",
                    QWebEngineDownloadItem.DownloadCancelled: "Cancelled",
                    QWebEngineDownloadItem.DownloadInterrupted: "Interrupted"
                }
                status = state_map.get(download_item.state(), "Unknown")
                path = download_item.path()
                downloads_html += f"<tr><td>{filename}</td><td>{status}</td><td>{path}</td></tr>"

        # Full HTML content for the downloads page
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Downloads</title>
            <style>
                body {{ font-family: sans-serif; padding: 20px; }}
                h1 {{ color: #333; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f0f0f0; }}
            </style>
        </head>
        <body>
            <h1>Downloads</h1>
            <table id="downloads-table">
                <thead>
                    <tr>
                        <th>File Name</th>
                        <th>Status</th>
                        <th>Save Location</th>
                    </tr>
                </thead>
                <tbody>
                    {downloads_html}
                </tbody>
            </table>
        </body>
        </html>
        """
        self.add_new_tab(html_content=html_content, title="Downloads")

    def add_new_tab(self, url="https://www.google.com", html_content=None, title="New Tab"):
        """Adds a new tab to the browser, either with a URL or with custom HTML content."""
        tab = QWidget()
        layout = QVBoxLayout()
        web_view = QWebEngineView()
        web_view.setPage(web_view.page()) # Associate the view with the default profile

        # --- JAVASCRIPT AND MODERN WEB FEATURES FIX ---
        settings = web_view.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.XSSAuditingEnabled, True)
        settings.setAttribute(QWebEngineSettings.ScrollAnimatorEnabled, True)
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, True)
        settings.setAttribute(QWebEngineSettings.DnsPrefetchEnabled, True)
        settings.setAttribute(QWebEngineSettings.HyperlinkAuditingEnabled, True)

        # ---------------------------------------------

        if html_content:
            web_view.setHtml(html_content, QUrl("about:blank"))
        else:
            web_view.load(QUrl(url))
        
        web_view.titleChanged.connect(lambda new_title: self.tabs.setTabText(self.tabs.indexOf(tab), title if title != "New Tab" else new_title))
        web_view.urlChanged.connect(self.update_address_bar)
        web_view.loadFinished.connect(self.on_load_finished)

        self.profile.downloadRequested.connect(self.handle_download)

        layout.addWidget(web_view)
        tab.setLayout(layout)
        self.tabs.addTab(tab, title)
        self.tabs.setCurrentWidget(tab)

    def close_tab(self, index):
        """Closes the tab at the given index."""
        self.tabs.removeTab(index)

    def load_url(self):
        """Loads the URL from the address bar into the current tab."""
        url = self.address_bar.text()
        if not url.startswith("http"):
            url = "https://" + url
        current_tab = self.tabs.currentWidget()
        web_view = current_tab.findChild(QWebEngineView)
        web_view.load(QUrl(url))

    def update_address_bar(self, url):
        """Updates the address bar with the URL of the current page."""
        self.address_bar.setText(url.toString())

    def navigate_back(self):
        """Navigates to the previous page in the current tab's history."""
        current_tab = self.tabs.currentWidget()
        web_view = current_tab.findChild(QWebEngineView)
        web_view.back()

    def navigate_forward(self):
        """Navigates to the next page in the current tab's history."""
        current_tab = self.tabs.currentWidget()
        web_view = current_tab.findChild(QWebEngineView)
        web_view.forward()

    def refresh_page(self):
        """Refreshes the current page."""
        current_tab = self.tabs.currentWidget()
        web_view = current_tab.findChild(QWebEngineView)
        web_view.reload()

    def on_load_finished(self, ok):
        """Adds the URL to history when a page finishes loading."""
        if ok:
            current_tab = self.tabs.currentWidget()
            web_view = current_tab.findChild(QWebEngineView)
            url = web_view.url().toString()
            if not url.startswith("about:"):
                self.add_to_history(url)

    def add_to_history(self, url):
        """Adds a URL to the browsing history."""
        if url not in self.history:
            self.history.append(url)
            self.save_history()

    def save_history(self):
        """Saves the current browsing history to a JSON file."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f)
        except Exception as e:
            print(f"Error saving history: {e}")

    def load_history(self):
        """Loads browsing history from a JSON file."""
        self.history = []
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
            except Exception as e:
                print(f"Error loading history: {e}")

    def save_bookmarks(self):
        """Saves bookmarks to a JSON file."""
        try:
            with open(self.bookmarks_file, 'w') as f:
                json.dump(self.bookmarks, f)
        except Exception as e:
            print(f"Error saving bookmarks: {e}")

    def load_bookmarks(self):
        """Loads bookmarks from a JSON file."""
        self.bookmarks = {}
        if os.path.exists(self.bookmarks_file):
            try:
                with open(self.bookmarks_file, 'r') as f:
                    self.bookmarks = json.load(f)
            except Exception as e:
                print(f"Error loading bookmarks: {e}")

    def handle_download(self, download):
        """Handles a requested download by opening a save file dialog."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", download.suggestedFileName())
        if file_path:
            download.setPath(file_path)
            download.accept()
            self.download_manager[download.suggestedFileName()] = download
            download.finished.connect(lambda: self.download_finished(download))
            download.downloadProgress.connect(self.download_progress)

    def download_progress(self, bytes_received, bytes_total):
        """Prints the download progress to the console."""
        if bytes_total > 0:
            percent = (bytes_received / bytes_total) * 100
            print(f"Download Progress: {percent:.2f}%")

    def download_finished(self, download):
        """Shows a message box when a download is complete or has failed."""
        if download.state() == QWebEngineDownloadItem.DownloadCompleted:
            QMessageBox.information(self, "Download Complete", f"File saved to: {download.path()}")
        elif download.state() == QWebEngineDownloadItem.DownloadInterrupted:
            QMessageBox.warning(self, "Download Failed", "The download was interrupted.")

    def clear_history(self):
        """Clears the browsing history."""
        self.history = []
        self.save_history()
        QMessageBox.information(self, "History Cleared", "Browsing history has been cleared.")

    def clear_bookmarks(self):
        """Clears all saved bookmarks."""
        self.bookmarks = {}
        self.save_bookmarks()
        QMessageBox.information(self, "Bookmarks Cleared", "Bookmarks have been cleared.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    browser = WebBrowser()
    browser.show()
    sys.exit(app.exec_())
