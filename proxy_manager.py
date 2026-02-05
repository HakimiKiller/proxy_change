import winreg
import itertools

class ProxyManager:
    REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"

    @staticmethod
    def get_proxy_settings():
        """Returns (enabled, server_ip, server_port)"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, ProxyManager.REG_PATH, 0, winreg.KEY_READ) as key:
                enabled, _ = winreg.QueryValueEx(key, "ProxyEnable")
                try:
                    server, _ = winreg.QueryValueEx(key, "ProxyServer")
                except FileNotFoundError:
                    server = ""
                
                ip = ""
                port = ""
                if server:
                    if ":" in server:
                        ip, port = server.split(":")
                    else:
                        ip = server
                
                return bool(enabled), ip, port
        except Exception as e:
            print(f"Error reading registry: {e}")
            return False, "", ""

    @staticmethod
    def set_proxy(ip, port):
        """Sets the proxy server and enables it."""
        try:
            proxy_server = f"{ip}:{port}"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, ProxyManager.REG_PATH, 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, proxy_server)
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
            return True
        except Exception as e:
            print(f"Error writing registry: {e}")
            return False

    @staticmethod
    def reset_proxy():
        """Clears the proxy server and disables it."""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, ProxyManager.REG_PATH, 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, "")
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
            return True
        except Exception as e:
            print(f"Error resetting registry: {e}")
            return False
    @staticmethod
    def toggle_proxy():
        """Toggles the proxy enabled status."""
        try:
            enabled, _, _ = ProxyManager.get_proxy_settings()
            new_status = 0 if enabled else 1
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, ProxyManager.REG_PATH, 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, new_status)
            return True
        except Exception as e:
            print(f"Error toggling registry: {e}")
            return False
