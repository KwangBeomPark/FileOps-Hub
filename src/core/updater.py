import urllib.request
import json
import ssl
import os
from src.utils.config_manager import ConfigManager
from src.utils.logger import get_logger

logger = get_logger()


class RedirectWithoutAuth(urllib.request.HTTPRedirectHandler):
    """
    GitHub Release 다운로드 시 AWS S3 등으로 리다이렉트되는 경우
    기존 Authorization 헤더를 제거하여 400 Bad Request 에러를 방지하는 핸들러.
    """
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new_req = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new_req:
            orig_host = req.host
            new_host = new_req.host
            if orig_host != new_host and 'Authorization' in new_req.headers:
                new_req.remove_header('Authorization')
        return new_req


class AutoUpdater:
    def __init__(self, current_version="v1.1.2", repo_owner="KwangBeomPark", repo_name="FileOps-Hub"):
        self.current_version = current_version
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.last_error = ""
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
        self.last_error = ""
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
                        # 1. 우선적으로 'setup'이 이름에 들어가고 .exe로 끝나는 파일 탐색
                        for asset in assets:
                            name = asset.get("name", "").lower()
                            if "setup" in name and name.endswith(".exe"):
                                download_url = asset.get("browser_download_url")
                                break
                        # 2. 없으면 .exe 확장자를 가진 임의의 파일 탐색
                        if not download_url:
                            for asset in assets:
                                name = asset.get("name", "").lower()
                                if name.endswith(".exe"):
                                    download_url = asset.get("browser_download_url")
                                    break
                        # 3. 그것도 없으면 첫 번째 자산 다운로드
                        if not download_url:
                            download_url = assets[0].get("browser_download_url")
                    else:
                        download_url = data.get("zipball_url")
                        
                    body = data.get("body", "No release notes available.")
                    return True, latest_tag, download_url, body
                    
                return False, latest_tag, None, ""
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Failed to check updates from GitHub: {e}")
            return False, self.current_version, None, ""
            
    def download_file(self, url, dest_path, progress_callback=None):
        """
        주어진 URL에서 파일을 다운로드하고 진행률 콜백을 호출합니다.
        
        Args:
            url (str): 다운로드할 URL
            dest_path (str): 저장할 로컬 파일 경로
            progress_callback (callable): (downloaded_bytes, total_bytes)를 인자로 받는 콜백 함수
        """
        # --- 방어 코드 1: HTTPS 프로토콜 강제 검증 ---
        if not url.startswith("https://"):
            raise ValueError("보안을 위해 HTTPS 프로토콜을 사용하는 업데이트 URL만 허용됩니다.")
            
        # --- 방어 코드 2: 다운로드 도메인 검증 ---
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        allowed_domains = ["github.com", "api.github.com", "codeload.github.com", "objects.githubusercontent.com", "github-releases.githubusercontent.com"]
        domain_ok = False
        for domain in allowed_domains:
            if parsed_url.netloc == domain or parsed_url.netloc.endswith("." + domain):
                domain_ok = True
                break
        if not domain_ok:
            raise ValueError(f"신뢰할 수 없는 다운로드 도메인입니다: {parsed_url.netloc}")

        token = self.config_manager.get("github_token", "").strip()
        headers = {
            "User-Agent": "IntegratedDataTool-AutoUpdater"
        }
        if token:
            headers["Authorization"] = f"token {token}"
            
        req = urllib.request.Request(url, headers=headers)
        ctx = ssl.create_default_context()
        
        # 리다이렉트 대응 빌드 오프너 생성
        opener = urllib.request.build_opener(RedirectWithoutAuth(), urllib.request.HTTPSHandler(context=ctx))
        
        try:
            with opener.open(req, timeout=15) as response:
                total_size = int(response.info().get('Content-Length', 0))
                downloaded = 0
                chunk_size = 16384  # 16KB 단위 청크 다운로드
                
                with open(dest_path, 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            try:
                                progress_callback(downloaded, total_size)
                            except Exception as cb_err:
                                logger.error(f"Progress callback error: {cb_err}")
                
                # --- 방어 코드 3: 다운로드 완료 후 크기 검증 (불완전 다운로드 방지) ---
                if total_size > 0 and downloaded != total_size:
                    raise IOError(f"불완전한 다운로드 감지: {downloaded}/{total_size} bytes 수신됨.")
                    
            return True
        except Exception as e:
            logger.error(f"Failed to download file from {url} to {dest_path}: {e}")
            if os.path.exists(dest_path):
                try:
                    os.remove(dest_path)
                except Exception:
                    pass
            raise e

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
