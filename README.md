# NewsX

NewsXは、ニュース記事を検索し、AIを使って要約するツールです。要約された記事は、おじゃる丸風の口調で出力されます。

## 機能

- NewsAPIを使用したニュース記事の検索
- OpenAI GPT-3.5を使用した記事の要約
- おじゃる丸風の可愛らしい口調での要約文生成
- シンプルで使いやすいWebインターフェース

## 必要条件

- Python 3.8以上
- NewsAPI キー
- OpenAI API キー

## セットアップ

1. リポジトリをクローン
```bash
git clone https://github.com/telesuhr/NewsX.git
cd NewsX
```

2. 依存パッケージをインストール
```bash
pip install -r requirements.txt
```

3. 環境変数の設定
`.env.example`ファイルを`.env`にコピーし、APIキーを設定
```bash
cp .env.example .env
```
`.env`ファイルを編集して、APIキーを設定：
```
NEWS_API_KEY=your_newsapi_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

## 使い方

1. アプリケーションを起動
```bash
python app.py
```

2. ブラウザで http://localhost:4000 にアクセス

3. 検索ボックスにキーワードを入力してニュースを検索

4. 記事の「要約」ボタンをクリックして、おじゃる丸風の要約を生成

## ライセンス

MIT

## 作者

[あなたの名前]
