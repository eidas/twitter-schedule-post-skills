---
name: x-batch-poster
description: >
  X.com（Twitter）への投稿予約を実行するスキル。
  Playwrightを使ってX.comのWeb UIから予約投稿を設定する。
  「Spreadsheetの内容をXに予約投稿」「Xにバッチ投稿」「シートから投稿予約」
  「X投稿をスケジュール」「ツイート予約」「単発で予約投稿」「1件だけ予約」
  などのフレーズで発火する。
  Google Spreadsheetとの連携、X.comのWeb UI操作、バッチ処理、単発投稿の
  いずれかに関わるタスクでもこのスキルを使うこと。
---

# X Batch Poster

X.comのWeb UI上で予約投稿を設定するスキル。
**バッチモード**（Google Spreadsheetから複数件読み取り）と
**単発モード**（テキスト・日時を直接指定）の2つの動作モードをサポートする。
実際の投稿はX.comが予約日時に自動実行する。API非公開の予約機能をPlaywrightで操作する。

ユーザーのChromeブラウザにCDP（Chrome DevTools Protocol）で接続して操作するため、
X.comへのログインはユーザーのChromeで済んでいる状態が前提。

## 前提条件

### 必須ソフトウェア
- Python 3.10+
- Playwright (`uv add playwright`)
- gspread + google-auth (`uv add gspread google-auth`)

### Chrome の準備

デバッグポートを有効にして Chrome を起動し、X.com にログインしておく。

**Windows の場合（既存の Chrome をすべて閉じてから実行）:**
```
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

または DevToolsActivePort 自動検出（ポートをランダム割り当て）:
```
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=0
```

起動後、Chrome で https://x.com にアクセスしてログインしておくこと。

### 認証情報
- **Google**: サービスアカウントのJSON鍵ファイル → `references/gsheet-setup.md` を参照

### 環境変数一覧
```
GOOGLE_SERVICE_ACCOUNT_KEY_PATH=./credentials.json
SPREADSHEET_ID=<Google SpreadsheetのID>
SHEET_NAME=Sheet1
# Chrome のリモートデバッグ URL（省略時は DevToolsActivePort から自動検出）
# CHROME_CDP_URL=http://localhost:9222
```

## Spreadsheetの列仕様

| 列 | ヘッダー名 | 内容 | 必須 |
|---|---|---|---|
| A | text | 投稿テキスト（280文字以内） | ○ |
| B | scheduled_at | 予約日時 `YYYY-MM-DD HH:MM` (JST) | ○ |
| C | media_urls | 画像/動画URL（カンマ区切り、最大4枚） | × |
| D | status | 処理状態（後述） | 自動 |
| E | executed_at | 処理実行日時 | 自動 |
| F | error_detail | エラー詳細 | 自動 |

### status値
- 空 or `pending` → 未処理（処理対象）
- `scheduled` → 予約設定完了
- `failed` → 予約設定失敗（error_detail列に詳細）
- `skipped` → スキップ（テキスト空、日時不正など）

## 実行フロー

### 【単発モード】テキストと日時を直接受け取った場合

ユーザーから投稿テキストと予約日時（+ 任意でメディアパス）を直接受け取ったら以下を実行する。
Spreadsheetは不要。Googleサービスアカウント認証も不要。

#### Step 1: 環境チェック
```bash
uv run python scripts/check_env.py --skip-gsheet
```
Chrome が未接続の場合は起動手順を案内して停止。

#### Step 2: 単発投稿実行
```bash
uv run python scripts/run_batch.py \
  --text "投稿テキスト" \
  --scheduled-at "YYYY-MM-DD HH:MM" \
  [--media "ファイルパス1,ファイルパス2"]
```

#### Step 3: 結果報告
成功 or 失敗を報告する。

---

### 【バッチモード】Spreadsheetから読み取る場合

ユーザーから最大実行行数（デフォルト: 10）を受け取ったら、以下を実行する。

#### Step 1: 環境チェック
```bash
uv run python scripts/check_env.py
```
不足があれば指示を出して停止。Chrome が未接続の場合は起動手順を案内する。

#### Step 2: バッチ実行
```bash
uv run python scripts/run_batch.py --max-rows <N> --spreadsheet-id <ID> --sheet-name <SHEET>
```

内部処理:
1. Spreadsheetから status が空 or `pending` の行を上から1行取得
2. バリデーション（テキスト空チェック、日時の未来チェック）
3. ユーザーの Chrome に CDP で接続し、X.com のログイン状態を確認（未ログインなら即停止）
4. 投稿画面を開き、テキスト入力 → 予約日時設定 → 確定
5. 結果を Spreadsheet の status / executed_at / error_detail 列に書き戻す
6. 最大行数まで 1〜5 を繰り返す

#### Step 3: 結果報告
完了後、サマリーを出力する（成功/失敗/スキップの件数）。

## テスト時の実行フロー

ユーザーからテストしてという指示があったら、以下を実行する。

### Step 1: テストの実行
```bash
uv run python scripts/run_batch.py --test
```

## エラーハンドリング方針
- **1行の失敗で全体を止めない** — status=failed を記録して次の行へ進む
- **ネットワークエラー** — 1行あたり最大3回リトライ（5秒間隔）
- **X.com 未ログイン** — 即座に全体停止。Chrome で X.com にログインして再実行
- **Chrome 未接続** — 即座に停止。--remote-debugging-port 付きで Chrome を再起動
- **レートリミット検知** — 30秒待機してリトライ
- **セレクタ不一致** — X.comのUI変更の可能性あり → `references/x-selectors.md` を参照して更新

## X.com UI操作の詳細
Playwrightでの操作手順とセレクタは `references/x-selectors.md` に集約。
X.comのUI変更時はそのファイルのみ更新すればよい。

## トラブルシューティング
よくある問題と対処法は `references/troubleshooting.md` を参照。
