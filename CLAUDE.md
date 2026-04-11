# agterm-win 開発サマリー

## プロジェクト概要

WSL上で動くAIエージェント向けターミナルアプリ。macOS専用の[cmux](https://cmux.com)にインスパイアされ、WSLg（Linux GUIアプリ）+ Windowsトースト通知で同等の体験を実現する。

## リポジトリ

https://github.com/nkchan/agterm-win

## 技術スタック

- **GUI**: Python + GTK4 + libvte（WSLgで動くLinux GUIアプリ）
- **通知**: PowerShell経由でWindowsトースト（WSLインターオップ）
- **通知検知**: OSC 9 / OSC 99 / OSC 777 エスケープシーケンス
- **対象環境**: Windows 11 + WSL2 + WSLg（Ubuntu 22.04/24.04）

## 現在のファイル構成

```
agterm-win/
├── agterm/
│   ├── __init__.py       # バージョン定義
│   ├── __main__.py       # Gtk.Application エントリーポイント
│   ├── window.py         # メインウィンドウ
│   ├── tab_model.py      # タブのデータモデル（Tab, TabModel クラス）
│   ├── tab_sidebar.py    # 縦タブサイドバー GTK4ウィジェット
│   ├── pane.py           # libvte ターミナルペイン
│   ├── osc.py            # OSC通知パーサー
│   └── notifier.py       # WSL→PowerShell→Windowsトーストブリッジ
├── scripts/
│   ├── claude_hook.sh       # Claude Code フックスクリプト
│   └── claude_settings.json # Claude Code settings.json テンプレート
├── install.sh            # セットアップスクリプト（apt + pip + desktop entry）
├── pyproject.toml
├── README.md
└── .gitignore
```

## 通知フロー

```
Claude Code（Stop / Notification イベント）
  └─ ~/.config/agterm-win/claude_hook.sh
       ├─ OSC 777エスケープを標準出力 → VTE → agterm-win タブが点灯
       └─ powershell.exe を直接呼び出し → Windowsトースト通知
```

## 主要クラス・設計

### TabModel（tab_model.py）
- `Tab`: id, label, branch, workdir, port, status, notify, notify_message, split を持つdataclass
- `TabModel`: タブのCRUD + アクティブタブ管理 + オブザーバーパターン

### AgTermWindow（window.py）
- サイドバー（TabSidebar）＋ タブバー＋ ペインエリアの3ペイン構成
- `_on_agent_notify(tab_id, message)` でOSC通知を受け取りサイドバー更新＋トースト発火

### TerminalPane（pane.py）
- `Vte.Terminal` を埋め込んでシェルをspawn
- OSCシーケンス検知は `contents-changed` シグナルベース（VTE 0.60+では `termprop-changed` も用意）

### notifier.py
- `send_windows_toast(title, message)` → `powershell.exe` を subprocess で呼ぶ
- WSL環境でなければスキップしてログ出力

## TODO（未実装・改善が必要な箇所）

1. **OSC検知の実装**: `pane.py` の `_on_contents_changed` が空。VTEからOSCシーケンスを実際に取り出す処理が必要
   - VTE 0.60未満: `get_text()` をスキャンして `osc.py` の `parse_osc()` を使う
   - VTE 0.60以上: `osc-received` シグナルがあればそちらを使う

2. **タブのステータス更新**: シェルのプロセス監視（claude, python等の実行検知）でstatusを `running` / `idle` に自動切替

3. **分割ペインのUI**: `tab.split` フラグはあるが、UIからトグルするボタンが未実装

4. **タブのメタ情報自動取得**: git branch / cwd / port をVTEのシェルから定期取得（`OSC 7` でcwd通知が使える）

5. **設定ファイル**: フォント、カラーテーマ等をYAML/TOMLで永続化

6. **テスト**: 各モジュールのユニットテストなし

## 開発の進め方（Claude Codeへの指示）

まず動作確認できる状態にすることを優先する。

### Step 1: インストール確認
```bash
bash install.sh
python3 -m agterm
```
GTK4ウィンドウが開けばOK。エラーがあれば依存関係を修正する。

### Step 2: OSC通知の実装（最重要）
`agterm/pane.py` の `_on_contents_changed` にOSC検知を実装する。
`agterm/osc.py` の `parse_osc()` を使ってパースし、
検知したら `self._on_notify(self._tab.id, message)` を呼ぶ。

### Step 3: Windowsトースト動作確認
WSL上で以下を手動実行してトーストが出るか確認：
```bash
python3 -c "from agterm.notifier import send_windows_toast; send_windows_toast('test', 'hello')"
```

### Step 4: Claude Codeフック動作確認
```bash
bash ~/.config/agterm-win/claude_hook.sh "テスト通知"
```
