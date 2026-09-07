# 🧮 けいさんクエスト 完成版

GitHub → Streamlit Community Cloud → Supabase で動かす、子ども向け計算練習アプリである。

## できること

- ＋1〜＋10を選択
- 10問連続出題
- 回答後約1秒で自動的に次問へ
- 正答率・平均回答時間・最速タイム
- コンボ
- 正解・不正解の視覚演出
- 効果音
- Safari用手動再生フォールバック
- 全120種類の生き物図鑑
- COMMON / RARE / SUPER RARE / LEGEND
- 高速回答・コンボでレア率上昇
- PERFECTボーナス
- 自己ベスト・最近の記録
- Supabaseによるクラウド永続保存
- Supabase未設定時はCSVでローカル動作

---

## ファイル構成

```text
keisan-quest/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example
│
├── assets/
│   ├── correct.wav
│   ├── wrong.wav
│   ├── rare.wav
│   └── perfect.wav
│
├── data/
│   ├── creatures.csv
│   └── .gitkeep
│
└── sql/
    └── schema.sql
```

---

# まずGitHubへアップロード

GitHubで `keisan-quest` リポジトリを開く。

既存版を置き換える場合は、このZIPの中身をリポジトリへアップロードする。

特に次の新しいファイル・フォルダを忘れない。

```text
.streamlit/
assets/
data/creatures.csv
sql/schema.sql
```

Commitする。

---

# Supabaseを作る

1. Supabaseで新しいProjectを作成する
2. Projectができたら SQL Editor を開く
3. `sql/schema.sql` の全文を貼り付ける
4. Runを押す

これで、

```text
results
collections
```

の2テーブルが作成される。

---

# SupabaseのURLとKeyを確認

Supabase DashboardのProject SettingsまたはAPI Keysの画面から、

```text
Project URL
Publishable key / anon key
```

を確認する。

**service_role key はアプリに入れないこと。**

---

# Streamlit Community CloudにSecretsを設定

GitHubに本物のキーを書いてはいけない。

`.streamlit/secrets.toml.example` は見本だけである。

Streamlit Community Cloudのアプリ設定画面で、Secretsに次の形式で入力する。

```toml
[supabase]
url = "https://xxxxxxxx.supabase.co"
key = "xxxxxxxx"
```

保存後、アプリを再起動する。

アプリ画面に、

```text
☁️ Supabase保存中
```

と出れば成功である。

---

# ローカルPCでSupabaseを使う場合

`.streamlit/secrets.toml.example` をコピーし、

```text
.streamlit/secrets.toml
```

という名前にする。

中身を自分のSupabase情報に書き換える。

```toml
[supabase]
url = "https://xxxxxxxx.supabase.co"
key = "xxxxxxxx"
```

`secrets.toml` は `.gitignore` に入っているので、GitHubにはアップロードされない。

---

# Safariの効果音

Safari/WebKitは自動再生をブラウザ側で止める場合がある。

そのためアプリには、

```text
🍎 Safari用：手動再生ボタンも表示
```

を用意している。

自動で鳴らない端末ではこれをONにする。

macOS Safariではサイトごとの「自動再生」設定を許可すると改善する場合がある。

---

# 生き物図鑑

全120種類である。

レア度は、

```text
★     COMMON
★★    RARE
★★★   SUPER RARE
★★★★  LEGEND
```

の4段階。

基本確率は、

```text
COMMON      76%
RARE        19%
SUPER RARE   4%
LEGEND       1%
```

である。

ただし、

- 2秒未満
- 3コンボ
- 5コンボ
- PERFECT

でレア率が上がる。

10問PERFECTなら、さらにRARE以上を1匹獲得する。

---

# 保存されるデータ

## results

1ゲームごとの結果。

- 名前
- ＋レベル
- 正解数
- 正答率
- 合計タイム
- 平均タイム
- 最速タイム
- 日時

## collections

生き物図鑑。

- 名前
- 生き物ID
- 獲得数
- 初回獲得日時
- 最終獲得日時

---

# 子どもの名前について

現状は名前をそのままDBに保存する。

公開アプリにする場合は、本名ではなく、

```text
たろう
PLAYER1
パンダくん
```

などのニックネーム利用を推奨する。

---

# 長男向け：今回覚えること

今回の構造は、

```text
app.py
  ↓
Supabaseへ保存
  ↓
次にアプリを開いたとき
  ↓
Supabaseから読み込む
```

である。

これまでのCSVと違い、

```text
スマホ
タブレット
PC
```

のどこから開いても同じ記録を使える。

これが「データベースを使う」大きな意味である。
