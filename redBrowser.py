from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtWebEngineWidgets import *


class MyWebBrowser():
    def __init__(self):
        
        self.window = QWidget() # Create a window
        self.window.setWindowTitle("ReD Browser")    # Set the window title
        

        self.layout = QVBoxLayout() # Create a layout
        self.horizontal = QHBoxLayout() # Create a horizontal layout

        self.layout = QVBoxLayout() # Create a layout
        self.horizontal = QHBoxLayout() # Create a horizontal layout

        self.url_bar = QTextEdit() # Create a text edit box
        self.url_bar.setMaximumHeight(30) # Set the maximum height of the text edit box

        self.go_button = QPushButton("Go") # Create a button 
        self.go_button.setMinimumHeight(30) # Set the maximum height of the button

        self.back_button = QPushButton("back") 
        self.back_button.setMinimumHeight(30)

        
        self.forward_button = QPushButton(">")    
        self.forward_button.setMinimumHeight(30)

        self.reload_button = QPushButton("Reload")
        self.reload_button.setMinimumHeight(30)

        self.horizontal.addWidget(self.back_button) # Add the back button to the horizontal layout
        self.horizontal.addWidget(self.forward_button) 
        self.horizontal.addWidget(self.reload_button)
        self.horizontal.addWidget(self.url_bar) 
        self.horizontal.addWidget(self.go_button)

        self.browser = QWebEngineView() # Create a web browser

        self.go_button.clicked.connect(lambda: self.navigate(self.url_bar.toPlainText())) # Connect the go button to the navigate function
        self.back_button.clicked.connect(self.browser.back) # Connect the back button to the back function
        self.reload_button.clicked.connect(self.browser.reload) # Connect the reload button to the reload function
        self.forward_button.clicked.connect(self.browser.forward) # Connect the forward button to the forward function


        self.layout.addLayout(self.horizontal) # Add the horizontal layout to the main layout
        self.layout.addWidget(self.browser) # Add the web browser to the main layout

        self.browser.setUrl(QUrl("https://www.google.com")) # Set the default url

        self.window.setLayout(self.layout) # Set the layout of the window
        self.window.show() # Show the window
    
    def navigate(self, url):
        if not url.startswith("http"):
            url = "http://" + url
            self.url_bar.setText(url)
        self.browser.setUrl(QUrl(url))

app = QApplication([])
window = MyWebBrowser()
app.exec_()
         