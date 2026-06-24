import urllib.request
import json
import ssl
from src.utils.config_manager import ConfigManager
from src.utils.logger import get_logger

logger = get_logger()

class AutoUpdater:
    def __init__(self, current_version="v1.0.0", repo_owner="kwangbeom-park", repo_name="Project06_py_DataOperting"):
        self.current_version = current_version
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.config_manager = ConfigManager()
        configured_repo = self.config_manager.get("github_repo", "").strip()
        if "/" in configured_repo:
            owner, name = configured_repo.split("/", 1)
            if owner.strip() and name.strip():
                self.repo_owner = owner.strip()
                self.repo_name = name.strip()
        
    def check_for_updates(self):
        """
        GitHub Releases에서 최신 버전을 체크합니다.
        
        Returns:
            tuple: (has_update, latest_version, download_url, release_notes)
        """
        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest"
        token = self.config_manager.get("github_token", "").strip()
        
        headers = {
            "User-Agent": "IntegratedDataTool-AutoUpdater"
        }
        if token:
            headers["Authorization"] = f"token {token}"
            
        req = urllib.request.Request(url, headers=headers)
        ctx = ssl.create_default_context()
        
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=5) as response:
                data = json.loads(response.read().decode())
                latest_tag = data.get("tag_name", "v0.0.0")
                
                if self.is_newer_version(self.current_version, latest_tag):
                    assets = data.get("assets", [])
                    download_url = None
                    if assets:
                        download_url = assets[0].get("browser_download_url")
                    else:
                        download_url = data.get("zipball_url")
                        
                    body = data.get("body", "No release notes available.")
                    return True, latest_tag, download_url, body
                    
                return False, latest_tag, None, ""
        except Exception as e:
            logger.error(f"Failed to check updates from GitHub: {e}")
            return False, self.current_version, None, ""
            
    def is_newer_version(self, current, latest):
        """v1.0.0 이나 v20260618 등의 버전을 안전하게 파싱하여 크기 비교"""
        def parse_version(v_str):
            v_clean = v_str.lower().lstrip('v').strip()
            if v_clean.isdigit():
                return (int(v_clean),)
            try:
                return tuple(int(x) for x in v_clean.split('.'))
            except ValueError:
                return (0,)
                
        return parse_version(latest) > parse_version(current)
