# 🧮 けいさんクエスト：GitHubドラッグ＆ドロップ用フラット版

この版は、GitHubのWeb画面で**全ファイルをそのまま一括ドラッグ＆ドロップ**して使えるようにしてある。

フォルダを作る必要はない。

## GitHub上でこうなっていれば正解

```text
app.py
requirements.txt
creatures.csv
correct.wav
wrong.wav
rare.wav
perfect.wav
README.md
config.toml
schema.sql
...
```

`app.py` と `creatures.csv` が同じ階層に見えていればよい。

## Streamlit Community Cloud

Main file path は

```text
app.py
```

にする。

## Supabase

`schema.sql` をSupabaseのSQL Editorで実行する。

Streamlit Community CloudのSecretsには以下を登録する。

```toml
[supabase]
url = "https://xxxx.supabase.co"
key = "xxxx"
```

※ `secrets.toml.example` は見本であり、本物のキーをGitHubへアップロードしない。

## Safari

Safariで自動効果音が鳴らない場合は、アプリ内の
「Safari用：手動再生ボタンも表示」をONにする。


## v4 改良点

### 1. GETした動物が次の問題でも見える
回答後は自動で次の問題へ進むが、直前に獲得した生き物を次の問題画面上部に残す。
そのため、テンポを落とさず何をGETしたか確認できる。

### 2. トップページに図鑑ボタン
トップページの

```text
📚 いきもの図鑑を見る
```

を押すと、その場で図鑑を開閉できる。
