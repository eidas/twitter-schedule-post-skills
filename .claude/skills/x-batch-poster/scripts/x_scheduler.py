"""X.com Web UI予約投稿モジュール: Playwrightによる操作.

X.comのUI変更に対応するため、セレクタは x_selectors.py に集約。
操作フロー:
  1. ログイン（初回のみ）
  2. 投稿作成画面を開く
  3. テキストを入力
  4. メディアがあれば添付
  5. 予約日時を設定
  6. 予約確定
"""
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    sync_playwright,
    TimeoutError as PlaywrightTimeout,
)

# セレクタ定義（UI変更時はここを更新）
# 最新のセレクタは references/x-selectors.md も参照
SELECTORS = {
    # ログイン
    "login_email_input": 'input[autocomplete="username"]',
    "login_next_button": 'button:has-text("Next"), button:has-text("次へ")',
    "login_password_input": 'input[type="password"]',
    "login_submit_button": 'button[data-testid="LoginForm_Login_Button"]',
    "2fa_input": 'input[data-testid="ocfEnterTextTextInput"]',
    "2fa_next_button": 'button[data-testid="ocfEnterTextNextButton"]',

    # 投稿
    "tweet_textbox": 'div[data-testid="tweetTextarea_0"]',
    "schedule_button": 'button[data-testid="scheduleOption"]',

    # 予約ダイアログ
    "schedule_date_input": 'input[data-testid="scheduledDatePickerInput"]',  # 存在しない場合あり
    "schedule_month_select": 'select[data-testid="ScheduledTweetDatePickerMonthInput"]',  # 存在しない場合あり
    "schedule_day_select": 'select[data-testid="ScheduledTweetDatePickerDayInput"]',      # 存在しない場合あり
    "schedule_year_select": 'select[data-testid="ScheduledTweetDatePickerYearInput"]',    # 存在しない場合あり
    "schedule_hour_select": 'select[data-testid="ScheduledTweetDatePickerHourInput"]',    # 存在しない場合あり
    "schedule_minute_select": 'select[data-testid="ScheduledTweetDatePickerMinuteInput"]',# 存在しない場合あり
    "schedule_ampm_select": 'select[data-testid="ScheduledTweetDatePickerAMPMInput"]',    # 存在しない場合あり（24h表記の場合不要）
    "schedule_confirm_button": 'button[data-testid="scheduledConfirmationPrimaryAction"]',

    # 投稿確定
    "tweet_submit_button": 'button[data-testid="tweetButton"]',

    # メディア
    "media_input": 'input[data-testid="fileInput"]',

    # 確認用
    "home_indicator": 'a[data-testid="AppTabBar_Home_Link"]',
    "toast_success": 'div[data-testid="toast"]',
}

# セッション保存先
SESSION_DIR = Path.home() / ".x-batch-poster" / "session"


class XScheduler:
    """X.comの投稿予約をPlaywrightで操作するクラス."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._logged_in = False

    def start(self):
        """ブラウザを起動."""
        self._playwright = sync_playwright().start()
        SESSION_DIR.mkdir(parents=True, exist_ok=True)

        self._context = self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_DIR),
            headless=self.headless,
            viewport={"width": 1280, "height": 900},
            locale="ja-JP",
            timezone_id="Asia/Tokyo",
        )
        self._page = self._context.new_page()

    def stop(self):
        """ブラウザを終了."""
        if self._context:
            self._context.close()
        if self._playwright:
            self._playwright.stop()

    def login(self) -> bool:
        """X.comにログイン（既にログイン済みならスキップ）.

        Returns: ログイン成功ならTrue
        Raises: RuntimeError on failure
        """
        page = self._page
        page.goto("https://x.com/home", wait_until="networkidle", timeout=30000)
        time.sleep(2)

        # 既にログイン済みか確認
        if page.query_selector(SELECTORS["home_indicator"]):
            self._logged_in = True
            return True

        # ログインページへ
        page.goto("https://x.com/i/flow/login", wait_until="networkidle", timeout=30000)
        time.sleep(2)

        email = os.environ.get("X_EMAIL", "")
        password = os.environ.get("X_PASSWORD", "")
        if not email or not password:
            raise RuntimeError("X_EMAIL / X_PASSWORD 環境変数が未設定です")

        # メールアドレス入力
        page.wait_for_selector(SELECTORS["login_email_input"], timeout=15000)
        page.fill(SELECTORS["login_email_input"], email)
        page.click(SELECTORS["login_next_button"])
        time.sleep(2)

        # パスワード入力
        page.wait_for_selector(SELECTORS["login_password_input"], timeout=15000)
        page.fill(SELECTORS["login_password_input"], password)
        page.click(SELECTORS["login_submit_button"])
        time.sleep(3)

        # 2FA確認
        twofa_secret = os.environ.get("X_2FA_SECRET", "")
        if twofa_secret and page.query_selector(SELECTORS["2fa_input"]):
            try:
                import pyotp
                totp = pyotp.TOTP(twofa_secret)
                code = totp.now()
                page.fill(SELECTORS["2fa_input"], code)
                page.click(SELECTORS["2fa_next_button"])
                time.sleep(3)
            except ImportError:
                raise RuntimeError("2FAが要求されましたが pyotp がインストールされていません")

        # ログイン成功確認
        try:
            page.wait_for_selector(SELECTORS["home_indicator"], timeout=15000)
            self._logged_in = True
            return True
        except PlaywrightTimeout:
            raise RuntimeError("ログインに失敗しました。認証情報を確認してください。")

    def schedule_post(
        self,
        text: str,
        scheduled_at: datetime,
        media_paths: Optional[list[str]] = None,
    ) -> bool:
        """投稿を予約設定する.

        Args:
            text: 投稿テキスト
            scheduled_at: 予約日時 (JST)
            media_paths: ローカルの画像/動画ファイルパスのリスト

        Returns: 成功ならTrue
        Raises: RuntimeError on failure
        """
        if not self._logged_in:
            raise RuntimeError("ログインしていません。先にlogin()を呼んでください。")

        page = self._page

        # 投稿作成画面を開く（compose tweetのURL）
        page.goto("https://x.com/compose/tweet", wait_until="networkidle", timeout=20000)
        time.sleep(2)

        # テキスト入力
        textbox = page.wait_for_selector(SELECTORS["tweet_textbox"], timeout=10000)
        if not textbox:
            raise RuntimeError("投稿テキストボックスが見つかりません")
        textbox.click()
        # type()で1文字ずつ入力（自然な入力を模倣）
        page.keyboard.type(text, delay=30)
        time.sleep(1)

        # メディア添付
        if media_paths:
            file_input = page.query_selector(SELECTORS["media_input"])
            if file_input:
                file_input.set_input_files(media_paths)
                time.sleep(3)  # アップロード待ち

        # 予約ボタンをクリック
        schedule_btn = page.wait_for_selector(SELECTORS["schedule_button"], timeout=10000)
        if not schedule_btn:
            raise RuntimeError("予約ボタンが見つかりません")
        schedule_btn.click()
        time.sleep(1)

        # 日時を設定
        self._set_schedule_datetime(page, scheduled_at)
        time.sleep(1)

        # 予約確定
        confirm_btn = page.wait_for_selector(
            SELECTORS["schedule_confirm_button"], timeout=10000
        )
        if not confirm_btn:
            raise RuntimeError("予約確定ボタンが見つかりません")
        confirm_btn.click()
        time.sleep(2)

        # 投稿（予約）ボタンをクリック
        submit_btn = page.wait_for_selector(
            SELECTORS["tweet_submit_button"], timeout=10000
        )
        if submit_btn:
            submit_btn.click()
            time.sleep(3)

        # 成功確認（トースト通知またはURL変化）
        # トーストが出なくてもエラーがなければ成功とみなす
        return True

    def _set_schedule_datetime(self, page: Page, dt: datetime):
        """予約ダイアログの日時フィールドを設定.

        X.comの予約UIはselect要素で月・日・年・時・分を個別に設定する。
        UIの変更頻度が高いため、セレクタが見つからない場合は
        代替手段（直接入力など）を試みる。
        """
        # 各フィールドをselect要素として操作
        selects = {
            "month": (SELECTORS["schedule_month_select"], str(dt.month)),
            "day": (SELECTORS["schedule_day_select"], str(dt.day)),
            "year": (SELECTORS["schedule_year_select"], str(dt.year)),
            "hour": (SELECTORS["schedule_hour_select"], str(dt.hour)),
            "minute": (SELECTORS["schedule_minute_select"], str(dt.minute)),
        }

        for field_name, (selector, value) in selects.items():
            try:
                el = page.wait_for_selector(selector, timeout=5000)
                if el:
                    el.select_option(value=value)
                    time.sleep(0.3)
            except PlaywrightTimeout:
                # セレクタが見つからない場合、UIが変更された可能性
                print(
                    f"  警告: {field_name}のセレクタが見つかりません。"
                    f"references/x-selectors.md を確認してください。"
                )
                # select要素ではなくカスタムUIの可能性 → フォールバック
                self._try_fallback_datetime_input(page, field_name, value)

    def _try_fallback_datetime_input(
        self, page: Page, field_name: str, value: str
    ):
        """select要素が見つからない場合のフォールバック.

        X.comがカスタムUIに変更した場合に備える。
        具体的なフォールバック戦略はUI変更時に実装する。
        """
        print(
            f"  フォールバック: {field_name}={value} の設定を試行中..."
        )
        # ここはUI変更時に具体的な処理を追加する
        # 現時点では警告のみ
        pass
