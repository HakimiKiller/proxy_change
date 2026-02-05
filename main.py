import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QSystemTrayIcon, QMenu, QMessageBox, QFrame, QGraphicsOpacityEffect)
from PySide6.QtCore import Qt, QSize, QUrl
from PySide6.QtGui import QIcon, QAction, QPalette, QColor, QDesktopServices
from proxy_manager import ProxyManager

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class ProxyChangeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("proxy change")
        self.setFixedSize(450, 420)
        
        # Frameless window for custom header
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.old_pos = None
        self.init_ui()
        self.init_tray()
        self.refresh_stats()

    def get_separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Plain)
        line.setStyleSheet("background-color: #ddd; max-height: 1px; margin: 5px 0px;")
        return line

    def init_ui(self):
        # Light theme main container
        self.container = QWidget(self)
        self.container.setObjectName("mainContainer")
        self.container.setFixedSize(450, 420)
        self.container.setStyleSheet("""
            #mainContainer {
                background-color: #f3f3f3;
                border: 1px solid #ccc;
                border-radius: 12px;
            }
            QLabel {
                color: #1a1a1a;
                font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Arial;
            }
            QPushButton#actionBtn {
                background-color: #4CAF50;
                color: white;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton#actionBtn:hover {
                background-color: #45a049;
            }
            QPushButton#resetBtn {
                background-color: #ff4d4f;
                color: white;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
                font-size: 15px;
            }
            QPushButton#resetBtn:hover {
                background-color: #ff7875;
            }
            QLineEdit {
                background-color: #ffffff;
                color: #333;
                border: 1px solid #d9d9d9;
                border-radius: 6px;
                padding: 10px;
                font-size: 16px;
            }
            QLineEdit:focus {
                border: 1px solid #4CAF50;
            }
        """)
        
        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(25, 15, 25, 25)
        main_layout.setSpacing(12)

        # 1. Custom Title Bar
        header_layout = QHBoxLayout()
        title_label = QLabel("Proxy Change")
        title_label.setStyleSheet("font-size: 22px; font-weight: 700; color: #1a1a1a;")
        
        self.github_btn = QPushButton()
        self.github_btn.setFixedSize(32, 32)
        github_icon = QIcon(resource_path("github.svg"))
        self.github_btn.setIcon(github_icon)
        self.github_btn.setIconSize(QSize(24, 24))
        self.github_btn.setCursor(Qt.PointingHandCursor)
        self.github_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
                border-radius: 16px;
            }
        """)
        self.github_btn.clicked.connect(self.open_github)
        
        # Set opacity for github button
        self.github_opacity = QGraphicsOpacityEffect()
        self.github_opacity.setOpacity(0.08)
        self.github_btn.setGraphicsEffect(self.github_opacity)
        
        self.close_btn = QPushButton()
        self.close_btn.setFixedSize(32, 32)
        close_icon = QIcon(resource_path("close.svg"))
        self.close_btn.setIcon(close_icon)
        self.close_btn.setIconSize(QSize(24, 24))
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
                border-radius: 16px;
            }
        """)
        self.close_btn.clicked.connect(self.hide)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.github_btn)
        header_layout.addWidget(self.close_btn)
        main_layout.addLayout(header_layout)

        main_layout.addWidget(self.get_separator())

        # 2. Status Section
        status_header_layout = QHBoxLayout()
        proxy_title = QLabel("当前代理服务器：")
        proxy_title.setStyleSheet("font-size: 18px; font-weight: 600;")
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.setObjectName("actionBtn")
        refresh_btn.setFixedSize(70, 30)
        refresh_btn.clicked.connect(self.refresh_stats)
        
        toggle_btn = QPushButton("切换")
        toggle_btn.setObjectName("actionBtn")
        toggle_btn.setFixedSize(70, 30)
        toggle_btn.clicked.connect(self.toggle_proxy)
        
        status_header_layout.addWidget(proxy_title)
        status_header_layout.addWidget(refresh_btn)
        status_header_layout.addWidget(toggle_btn)
        status_header_layout.addStretch()
        main_layout.addLayout(status_header_layout)

        self.status_text_label = QLabel("状态: OFF\nIP: -\n端口: -")
        self.status_text_label.setStyleSheet("font-size: 15px; margin-left: 5px; line-height: 1.4; color: #666;")
        main_layout.addWidget(self.status_text_label)

        main_layout.addWidget(self.get_separator())

        # 3. Setting Section
        set_header_layout = QHBoxLayout()
        set_title = QLabel("设置代理服务器")
        set_title.setStyleSheet("font-size: 18px; font-weight: 600;")
        
        set_btn = QPushButton("设置")
        set_btn.setObjectName("actionBtn")
        set_btn.setFixedSize(70, 32)
        set_btn.clicked.connect(self.set_proxy)
        
        set_header_layout.addWidget(set_title)
        set_header_layout.addWidget(set_btn)
        set_header_layout.addStretch()
        main_layout.addLayout(set_header_layout)

        input_row_layout = QHBoxLayout()
        input_row_layout.setSpacing(15)
        
        ip_v_layout = QVBoxLayout()
        ip_label = QLabel("IP")
        ip_label.setStyleSheet("font-size: 13px; color: #888; font-weight: 500;")
        ip_v_layout.addWidget(ip_label)
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("127.0.0.1")
        ip_v_layout.addWidget(self.ip_input)
        input_row_layout.addLayout(ip_v_layout)

        port_v_layout = QVBoxLayout()
        port_label = QLabel("Port")
        port_label.setStyleSheet("font-size: 13px; color: #888; font-weight: 500;")
        port_v_layout.addWidget(port_label)
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("7890")
        port_v_layout.addWidget(self.port_input)
        input_row_layout.addLayout(port_v_layout)

        main_layout.addLayout(input_row_layout)

        main_layout.addStretch()
        
        main_layout.addWidget(self.get_separator())

        # 4. Reset Button
        reset_btn = QPushButton("重置代理服务器")
        reset_btn.setObjectName("resetBtn")
        reset_btn.clicked.connect(self.reset_proxy)
        main_layout.addWidget(reset_btn)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        icon = QIcon(resource_path("logo.ico"))
        self.setWindowIcon(icon)
        self.tray_icon.setIcon(icon)
        
        tray_menu = QMenu()
        show_action = QAction("打开主界面", self)
        show_action.triggered.connect(self.showNormal)
        
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        
        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.showNormal()
                self.activateWindow()

    def refresh_stats(self):
        enabled, ip, port = ProxyManager.get_proxy_settings()
        status_str = "ON" if enabled else "OFF"
        self.status_text_label.setText(f"状态: {status_str}\nIP: {ip if ip else '-'}\n端口: {port if port else '-'}")

    def set_proxy(self):
        ip = self.ip_input.text().strip()
        port = self.port_input.text().strip()
        if not ip or not port:
            return
        
        if ProxyManager.set_proxy(ip, port):
            self.refresh_stats()

    def reset_proxy(self):
        if ProxyManager.reset_proxy():
            self.ip_input.clear()
            self.port_input.clear()
            self.refresh_stats()

    def toggle_proxy(self):
        if ProxyManager.toggle_proxy():
            self.refresh_stats()

    def open_github(self):
        QDesktopServices.openUrl(QUrl("https://github.com/HakimiKiller/proxy_change"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    window = ProxyChangeApp()
    window.show()
    
    sys.exit(app.exec())
