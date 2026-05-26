# トラブルシューティング

## ログイン関連

### 「ログインに失敗しました」
- X_EMAIL, X_PASSWORD 環境変数を再確認
- X.comでパスワードが変更されていないか確認
- 手動でブラウザからログインして、追加の認証（電話番号確認など）が要求されていないか確認
- セッションディレクトリ `~/.x-batch-poster/session` を削除して再試行

### 2FAエラー
- X_2FA_SECRET が正しいか確認（Base32エンコード文字列）
- pyotp がインストールされているか確認: `pip install pyotp`
- サーバーの時刻がずれていないか確認（TOTPは時刻ベース）

### 「unusual login activity」の警告
- 新しいIPからのログインでX.comが追加認証を要求している
- 一度手動でブラウザからログインして認証を済ませる
- VPNを使っている場合はIPが安定するよう設定する

## Spreadsheet関連

### 「gspread.exceptions.APIError: 403」
- サービスアカウントにSpreadsheetが共有されているか確認
- Google Sheets APIが有効化されているか確認

### 行が読み取れない
- ヘッダー行の列名が正確か確認: `text`, `scheduled_at`, `media_urls`, `status`, `executed_at`, `error_detail`
- 空行がデータの途中に入っていないか確認（gspreadは空行でデータ終了と認識する場合がある）

## 予約投稿関連

### 「予約ボタンが見つかりません」
- X.comのUIが変更された可能性 → `references/x-selectors.md` を参照してセレクタを更新
- ページの読み込みが完了していない → タイムアウト値を増やす

### 予約日時が正しく設定されない
- 日時フォーマットが `YYYY-MM-DD HH:MM` か確認
- タイムゾーンはJSTで設定されている（Playwrightのtimezone_id）
- X.comの予約UIがselect要素からカスタムUIに変わっていないか DevTools で確認

### メディアがアップロードされない
- ファイルパスが正しいか確認（ローカルパスのみ対応、URLは未対応）
- ファイル形式がX.comでサポートされているか確認（jpg, png, gif, mp4）
- ファイルサイズの上限を超えていないか確認

## 一般的な問題

### プロセスが途中で停止する
- `status` 列を確認して、どの行まで処理されたか確認
- `failed` になった行の `error_detail` 列を確認
- `--no-headless` オプションでブラウザを表示して実行し、動作を目視確認

### レートリミット
- X.comの投稿制限に引っかかっている場合、30秒待機して自動リトライされる
- 大量投稿の場合は `--max-rows` を小さくして複数回に分ける
- 行間の待機時間を延ばすには `run_batch.py` の `time.sleep(3)` を調整
