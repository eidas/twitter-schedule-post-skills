"""環境チェックスクリプト: 必要な依存関係と認証情報の確認."""
import importlib
import os
import sys


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


def check_playwright_browsers():
    """Playwrightブラウザのインストール確認."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch(headless=True).close()
        return True
    except Exception:
        return False


def check_env_vars():
    """必要な環境変数の確認."""
    required = ["X_EMAIL", "X_PASSWORD"]
    recommended = ["GOOGLE_SERVICE_ACCOUNT_KEY_PATH", "SPREADSHEET_ID"]

    missing_required = [v for v in required if not os.environ.get(v)]
    missing_recommended = [v for v in recommended if not os.environ.get(v)]
    return missing_required, missing_recommended


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
    print("\n[1/4] Pythonパッケージ...")
    missing_packages = check_python_packages()
    if missing_packages:
        errors.append(f"pip install {' '.join(missing_packages)}")
        print(f"  ✗ 不足: {', '.join(missing_packages)}")
    else:
        print("  ✓ すべてインストール済み")

    # 2. Playwrightブラウザ
    print("\n[2/4] Playwrightブラウザ...")
    if not missing_packages or "playwright" not in " ".join(missing_packages):
        if check_playwright_browsers():
            print("  ✓ Chromiumインストール済み")
        else:
            errors.append("playwright install chromium")
            print("  ✗ Chromium未インストール → playwright install chromium")
    else:
        print("  - スキップ（playwright未インストール）")

    # 3. 環境変数
    print("\n[3/4] 環境変数...")
    missing_req, missing_rec = check_env_vars()
    if missing_req:
        errors.append(f"環境変数を設定: {', '.join(missing_req)}")
        print(f"  ✗ 必須: {', '.join(missing_req)}")
    else:
        print("  ✓ 必須変数はすべて設定済み")
    if missing_rec:
        print(f"  △ 推奨: {', '.join(missing_rec)}（コマンド引数で指定も可）")

    # 4. Google認証情報
    print("\n[4/4] Google認証情報...")
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
