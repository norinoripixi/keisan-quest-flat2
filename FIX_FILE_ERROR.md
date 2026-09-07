# Streamlit Cloud FileNotFoundError 修正版

今回のエラーは `data/creatures.csv` をアプリが見つけられなかったことが原因である。

## GitHub上で必ずこの形にする

```text
リポジトリのルート/
├── app.py
├── requirements.txt
├── data/
│   └── creatures.csv
├── assets/
│   ├── correct.wav
│   ├── wrong.wav
│   ├── rare.wav
│   └── perfect.wav
└── ...
```

特に、次のような二重フォルダになっていないか確認する。

```text
リポジトリ/
└── keisan-quest/
    ├── app.py
    └── data/
        └── creatures.csv
```

この場合、Streamlit側の Main file path を

```text
keisan-quest/app.py
```

にする必要がある。

修正版 `app.py` は `Path(__file__).resolve().parent` を使い、
`app.py` 自身の場所から `data/creatures.csv` を探すため、Cloud上でも安定しやすい。
