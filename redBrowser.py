from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtWebEngineWidgets import *
import json
import os
from datetime import datetime

class MyWebBrowser():
    def __init__(self):
        # Initialize storage files
        self.bookmarks_file = "bookmarks.json"
        self.history_file = "history.json"
        self.load_storage()
        
        self.window = QWidget()
        self.window.setWindowTitle("ReD Browser")
        
        # Main layouts
        self.layout = QVBoxLayout()
        self.horizontal = QHBoxLayout()
        
        # Navigation elements
        self.url_bar = QTextEdit()
        self.url_bar.setMaximumHeight(30)
        self.go_button = QPushButton("Go")
        self.go_button.setMinimumHeight(30)
        self.back_button = QPushButton("<__")
        self.back_button.setMinimumHeight(30)
        self.forward_button = QPushButton("__>")
        self.forward_button.setMinimumHeight(30)
        self.reload_button = QPushButton("Reload")
        self.reload_button.setMinimumHeight(30)
        
        # Bookmark and History buttons
        self.bookmark_button = QPushButton("⭐")
        self.bookmark_button.setMinimumHeight(30)
        self.history_button = QPushButton("📜")
        self.history_button.setMinimumHeight(30)
        
        # Add widgets to horizontal layout
        self.horizontal.addWidget(self.back_button)
        self.horizontal.addWidget(self.forward_button)
        self.horizontal.addWidget(self.reload_button)
        self.horizontal.addWidget(self.url_bar)
        self.horizontal.addWidget(self.bookmark_button)
        self.horizontal.addWidget(self.history_button)
        self.horizontal.addWidget(self.go_button)
        
        # Browser widget
        self.browser = QWebEngineView()
        
        # Connect signals
        self.go_button.clicked.connect(lambda: self.navigate(self.url_bar.toPlainText()))
        self.back_button.clicked.connect(self.browser.back)
        self.reload_button.clicked.connect(self.browser.reload)
        self.forward_button.clicked.connect(self.browser.forward)
        self.bookmark_button.clicked.connect(self.toggle_bookmark)
        self.history_button.clicked.connect(self.show_history)
        self.browser.urlChanged.connect(self.update_url)
        
        # Set up layout
        self.layout.addLayout(self.horizontal)
        self.layout.addWidget(self.browser)
        
        # Set default URL
        self.browser.setUrl(QUrl("https://www.google.com"))
        self.window.setLayout(self.layout)
        self.window.show()

    def load_storage(self):
        # Load bookmarks
        if os.path.exists(self.bookmarks_file):
            with open(self.bookmarks_file, 'r') as f:
                self.bookmarks = json.load(f)
        else:
            self.bookmarks = []
            
        # Load history
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as f:
                self.history = json.load(f)
        else:
            self.history = []

    def save_storage(self):
        # Save bookmarks
        with open(self.bookmarks_file, 'w') as f:
            json.dump(self.bookmarks, f)
            
        # Save history
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f)

    def navigate(self, url):
        if not url.startswith("http"):
            url = "https://" + url
            self.url_bar.setText(url)
        self.browser.setUrl(QUrl(url))
        
        # Add to history
        self.history.append({
            'url': url,
            'title': self.browser.page().title(),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        self.save_storage()

    def update_url(self, url):
        self.url_bar.setText(url.toString())
        
    def toggle_bookmark(self):
        current_url = self.browser.url().toString()
        current_title = self.browser.page().title()
        
        # Check if already bookmarked
        for bookmark in self.bookmarks:
            if bookmark['url'] == current_url:
                self.bookmarks.remove(bookmark)
                self.bookmark_button.setText("⭐")
                self.save_storage()
                return
                
        # Add new bookmark
        self.bookmarks.append({
            'url': current_url,
            'title': current_title
        })
        self.bookmark_button.setText("★")
        self.save_storage()

    def show_history(self):
        dialog = QDialog(self.window)
        dialog.setWindowTitle("History & Bookmarks")
        layout = QVBoxLayout()
        
        # Tabs for History and Bookmarks
        tabs = QTabWidget()
        
        # History tab
        history_widget = QWidget()
        history_layout = QVBoxLayout()
        history_list = QListWidget()
        
        for entry in reversed(self.history[-50:]):  # Show last 50 entries
            item = QListWidgetItem(f"{entry['timestamp']} - {entry['title']}\n{entry['url']}")
            history_list.addItem(item)
            
        history_layout.addWidget(history_list)
        history_widget.setLayout(history_layout)
        
        # Bookmarks tab
        bookmarks_widget = QWidget()
        bookmarks_layout = QVBoxLayout()
        bookmarks_list = QListWidget()
        
        for bookmark in self.bookmarks:
            item = QListWidgetItem(f"{bookmark['title']}\n{bookmark['url']}")
            bookmarks_list.addItem(item)
            
        bookmarks_layout.addWidget(bookmarks_list)
        bookmarks_widget.setLayout(bookmarks_layout)
        
        # Add tabs
        tabs.addTab(history_widget, "History")
        tabs.addTab(bookmarks_widget, "Bookmarks")
        
        layout.addWidget(tabs)
        dialog.setLayout(layout)
        dialog.exec_()

app = QApplication([])
window = MyWebBrowser()
app.exec_()
