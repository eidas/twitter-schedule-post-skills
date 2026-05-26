# X.com セレクタリファレンス

> **このファイルの目的**: X.comのUI変更時に更新する唯一のファイル。
> セレクタが変わったら、ここと `scripts/x_scheduler.py` の `SELECTORS` 辞書を同時に更新する。

## 最終確認日: 2025-05-XX（初期作成、実環境で要検証）

## セレクタ定義

### ログインフロー

| 要素 | セレクタ | 備考 |
|---|---|---|
| メールアドレス入力 | `input[autocomplete="username"]` | ログインフォームの最初の入力欄 |
| 「次へ」ボタン | `button:has-text("Next"), button:has-text("次へ")` | 言語設定により変化 |
| パスワード入力 | `input[type="password"]` | |
| ログイン実行ボタン | `button[data-testid="LoginForm_Login_Button"]` | |
| 2FA入力欄 | `input[data-testid="ocfEnterTextTextInput"]` | 2FA有効時のみ表示 |
| 2FA確定ボタン | `button[data-testid="ocfEnterTextNextButton"]` | |

### 投稿画面

| 要素 | セレクタ | 備考 |
|---|---|---|
| テキストエリア | `div[data-testid="tweetTextarea_0"]` | contenteditable div |
| メディア入力 | `input[data-testid="fileInput"]` | hidden input[type=file] |
| 予約アイコン | `button[data-testid="scheduleOption"]` | カレンダーアイコンのボタン |
| 投稿/予約ボタン | `button[data-testid="tweetButton"]` | 予約設定後は「予約設定」テキストになる |

### 予約ダイアログ

| 要素 | セレクタ | 備考 |
|---|---|---|
| 月 | `select[data-testid="ScheduledTweetDatePickerMonthInput"]` | select要素 |
| 日 | `select[data-testid="ScheduledTweetDatePickerDayInput"]` | select要素 |
| 年 | `select[data-testid="ScheduledTweetDatePickerYearInput"]` | select要素 |
| 時 | `select[data-testid="ScheduledTweetDatePickerHourInput"]` | select要素 |
| 分 | `select[data-testid="ScheduledTweetDatePickerMinuteInput"]` | select要素 |
| AM/PM | `select[data-testid="ScheduledTweetDatePickerAMPMInput"]` | 12h表記の場合のみ |
| 確定ボタン | `button[data-testid="scheduledConfirmationPrimaryAction"]` | |

### 確認用

| 要素 | セレクタ | 備考 |
|---|---|---|
| ホームリンク | `a[data-testid="AppTabBar_Home_Link"]` | ログイン状態の確認に使用 |
| トースト通知 | `div[data-testid="toast"]` | 成功/エラー通知 |

## セレクタ更新手順

1. ブラウザのDevToolsでX.comを開く
2. 対象要素を右クリック→「検証」
3. `data-testid` 属性を優先的に使う（安定性が高い）
4. `data-testid` がない場合は `aria-label` や構造ベースのセレクタを使用
5. このファイルと `scripts/x_scheduler.py` の `SELECTORS` を両方更新

## セレクタが見つからない場合の調査方法

```javascript
// DevToolsコンソールで実行
// data-testid属性を持つ要素を一覧
document.querySelectorAll('[data-testid]').forEach(el => {
  console.log(el.getAttribute('data-testid'), el.tagName);
});
```

## 既知の注意点

- X.comは頻繁にUI変更を行う。セレクタは1-2ヶ月で変わる可能性がある。
- ログイン後にセッションが保存されるため、2回目以降のログインは通常スキップされる。
- `locale="ja-JP"` で起動しているため、ボタンテキストは日本語になる可能性がある。
  テキストベースのセレクタ（`:has-text()`）は日英両方に対応させること。
- 予約投稿の日時UIがselect要素からカスタムコンポーネントに変わった場合、
  `_try_fallback_datetime_input` にフォールバック処理を実装する必要がある。
