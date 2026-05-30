"""環境チェックスクリプト: 必要な依存関係と認証情報の確認."""
import importlib
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def check_python_packages():
    """必要なPythonパッケージの存在確認."""
    required = {
        "playwright": "playwright",
        "gspread": "gspread",
        "google.oauth2.service_account": "google-auth",
    }
    missing = []
    for module, package in required.items():
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(package)
    return missing


def _get_cdp_url() -> str:
    """CDPのURLを取得（x_scheduler._get_cdp_url と同じロジック）."""
    import platform

    env_url = os.environ.get("CHROME_CDP_URL", "")
    if env_url:
        return env_url

    if platform.system() == "Windows":
        user_data = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
    elif platform.system() == "Darwin":
        user_data = os.path.expanduser("~/Library/Application Support/Google/Chrome")
    else:
        user_data = os.path.expanduser("~/.config/google-chrome")

    port_file = Path(user_data) / "DevToolsActivePort"
    if port_file.exists():
        port = port_file.read_text().splitlines()[0].strip()
        return f"http://localhost:{port}"

    return "http://localhost:9222"


def check_chrome_cdp_connection() -> tuple[bool, str]:
    """Chrome CDPへの接続確認."""
    cdp_url = _get_cdp_url()
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(cdp_url, timeout=5000)
            browser.close()
        return True, cdp_url
    except Exception as e:
        return False, f"{cdp_url} への接続失敗: {e}"


def check_env_vars():
    """必要な環境変数の確認."""
    recommended = ["GOOGLE_SERVICE_ACCOUNT_KEY_PATH", "SPREADSHEET_ID", "CHROME_CDP_URL"]
    missing_recommended = [v for v in recommended if not os.environ.get(v)]
    return missing_recommended


def check_google_credentials():
    """Googleサービスアカウント鍵ファイルの確認."""
    key_path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY_PATH", "./credentials.json")
    if not os.path.exists(key_path):
        return False, key_path
    return True, key_path


def main():
    print("=" * 50)
    print("X Batch Poster - 環境チェック")
    print("=" * 50)
    errors = []

    # 1. Pythonパッケージ
    print("\n[1/3] Pythonパッケージ...")
    missing_packages = check_python_packages()
    if missing_packages:
        errors.append(f"pip install {' '.join(missing_packages)}")
        print(f"  ✗ 不足: {', '.join(missing_packages)}")
    else:
        print("  ✓ すべてインストール済み")

    # 2. Chrome CDP接続
    print("\n[2/3] Chrome CDP接続...")
    if not missing_packages or "playwright" not in " ".join(missing_packages):
        ok, detail = check_chrome_cdp_connection()
        if ok:
            print(f"  ✓ 接続成功: {detail}")
        else:
            errors.append(
                "Chrome をリモートデバッグポート付きで起動してください:\n"
                r'     "C:\Program Files\Google\Chrome\Application\chrome.exe"'
                " --remote-debugging-port=9222"
            )
            print(f"  ✗ {detail}")
            print(
                "  → Chrome を --remote-debugging-port=9222 付きで起動し、"
                "X.com にログインしてください"
            )
        # 推奨環境変数
        missing_rec = check_env_vars()
        if missing_rec:
            filtered = [v for v in missing_rec if v != "CHROME_CDP_URL"]
            if "CHROME_CDP_URL" in missing_rec:
                print("  △ CHROME_CDP_URL 未設定（DevToolsActivePort から自動検出します）")
            if filtered:
                print(f"  △ 推奨: {', '.join(filtered)}（コマンド引数で指定も可）")
    else:
        print("  - スキップ（playwright 未インストール）")

    # 3. Google認証情報
    print("\n[3/3] Google認証情報...")
    exists, path = check_google_credentials()
    if exists:
        print(f"  ✓ 鍵ファイル: {path}")
    else:
        errors.append(f"Googleサービスアカウント鍵ファイルを配置: {path}")
        print(f"  ✗ 鍵ファイルが見つからない: {path}")

    # サマリー
    print("\n" + "=" * 50)
    if errors:
        print("✗ 以下を修正してください:")
        for i, e in enumerate(errors, 1):
            print(f"  {i}. {e}")
        sys.exit(1)
    else:
        print("✓ すべてのチェックに合格しました")
        sys.exit(0)


if __name__ == "__main__":
    main()
