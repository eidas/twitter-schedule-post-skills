---
name: x-batch-poster
description: >
  Google SpreadsheetからX.com（Twitter）への投稿予約をバッチ実行するスキル。
  Playwrightを使ってX.comのWeb UIから予約投稿を設定する。
  「Spreadsheetの内容をXに予約投稿」「Xにバッチ投稿」「シートから投稿予約」
  「X投稿をスケジュール」「ツイート予約」などのフレーズで発火する。
  Google Spreadsheetとの連携、X.comのWeb UI操作、バッチ処理の
  いずれかに関わるタスクでもこのスキルを使うこと。
---

# X Batch Poster

Google Spreadsheetから投稿データを読み取り、X.comのWeb UI上で予約投稿を設定するスキル。
実際の投稿はX.comが予約日時に自動実行する。API非公開の予約機能をPlaywrightで操作する。

## 前提条件

### 必須ソフトウェア
- Python 3.10+
- Playwright (`pip install playwright && playwright install chromium`)
- gspread + google-auth (`pip install gspread google-auth`)

### 認証情報
- **Google**: サービスアカウントのJSON鍵ファイル → `references/gsheet-setup.md` を参照
- **X.com**: 環境変数 `X_EMAIL`, `X_PASSWORD` にログイン情報を設定
  - 2FA有効時は `X_2FA_SECRET` にTOTPシークレットを設定（pyotpで生成）

### 環境変数一覧
```
GOOGLE_SERVICE_ACCOUNT_KEY_PATH=./credentials.json
SPREADSHEET_ID=<Google SpreadsheetのID>
SHEET_NAME=Sheet1
X_EMAIL=your@email.com
X_PASSWORD=yourpassword
X_2FA_SECRET=JBSWY3DPEHPK3PXP   # 2FA有効時のみ
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

ユーザーから最大実行行数（デフォルト: 10）を受け取ったら、以下を実行する。

### Step 1: 環境チェック
```bash
python scripts/check_env.py
```
不足があれば指示を出して停止。

### Step 2: バッチ実行
```bash
python scripts/run_batch.py --max-rows <N> --spreadsheet-id <ID> --sheet-name <SHEET>
```

内部処理:
1. Spreadsheetから status が空 or `pending` の行を上から1行取得
2. バリデーション（テキスト空チェック、日時の未来チェック）
3. Playwrightで X.com にログイン（初回のみ、以降はセッション再利用）
4. 投稿画面を開き、テキスト入力 → 予約日時設定 → 確定
5. 結果を Spreadsheet の status / executed_at / error_detail 列に書き戻す
6. 最大行数まで 1〜5 を繰り返す

### Step 3: 結果報告
完了後、サマリーを出力する（成功/失敗/スキップの件数）。

## エラーハンドリング方針
- **1行の失敗で全体を止めない** — status=failed を記録して次の行へ進む
- **ネットワークエラー** — 1行あたり最大3回リトライ（5秒間隔）
- **X.comログイン失敗** — 即座に全体停止（認証情報の問題のため続行不可）
- **レートリミット検知** — 30秒待機してリトライ
- **セレクタ不一致** — X.comのUI変更の可能性あり → `references/x-selectors.md` を参照して更新

## X.com UI操作の詳細
Playwrightでの操作手順とセレクタは `references/x-selectors.md` に集約。
X.comのUI変更時はそのファイルのみ更新すればよい。

## トラブルシューティング
よくある問題と対処法は `references/troubleshooting.md` を参照。
