# Google Spreadsheet セットアップガイド

## 1. サービスアカウントの作成

1. [Google Cloud Console](https://console.cloud.google.com/) を開く
2. プロジェクトを選択（または新規作成）
3. 「APIとサービス」→「認証情報」→「認証情報を作成」→「サービスアカウント」
4. 名前を付けて作成（例: `x-batch-poster`）
5. 作成したサービスアカウントの「鍵」タブ→「鍵を追加」→「JSON」
6. ダウンロードされたJSONファイルを `credentials.json` としてプロジェクトルートに配置

## 2. Google Sheets API の有効化

1. Google Cloud Console →「APIとサービス」→「ライブラリ」
2. 「Google Sheets API」を検索して有効化

## 3. Spreadsheetの共有設定

1. 対象のGoogle Spreadsheetを開く
2. 「共有」→ サービスアカウントのメールアドレス（`xxx@xxx.iam.gserviceaccount.com`）を追加
3. 権限は「編集者」に設定

## 4. Spreadsheet IDの確認

URLの以下の部分がSpreadsheet ID:
```
https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit
```

## 5. シートのヘッダー行

1行目に以下のヘッダーを設定:
```
text | scheduled_at | media_urls | status | executed_at | error_detail
```

## 6. 環境変数の設定

```bash
export GOOGLE_SERVICE_ACCOUNT_KEY_PATH=./credentials.json
export SPREADSHEET_ID=1ABC...xyz
export SHEET_NAME=Sheet1  # デフォルトはSheet1
```
