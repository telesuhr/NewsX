from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if .env file exists and print its contents (for debugging)
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
print(f"Loading .env from: {env_path}")
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        print("Contents of .env file:")
        for line in f:
            if line.startswith("NEWS_API_KEY"):
                print(f"Found NEWS_API_KEY: {line.strip()}")

# アプリケーションのルートディレクトリを取得
root_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(root_dir, "templates")

app = Flask(__name__, template_folder=template_dir)
CORS(app)

# API keys
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "").strip().strip('"').strip("'")
print(f"Loaded NEWS_API_KEY from .env: {NEWS_API_KEY}")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip().strip('"').strip("'")
print(f"Loaded OPENAI_API_KEY from .env: {OPENAI_API_KEY[:10]}...")

# Initialize OpenAI client
client = OpenAI()  # APIキーは環境変数から自動的に読み込まれます

# APIキーの検証
NEWS_API_BASE_URL = "https://newsapi.org/v2/everything"
try:
    test_params = {"q": "test", "pageSize": 1, "language": "en", "apiKey": NEWS_API_KEY}
    test_response = requests.get(NEWS_API_BASE_URL, params=test_params)
    test_data = test_response.json()

    if test_data.get("status") == "ok":
        print("NewsAPI key is valid!")
    else:
        print(
            "NewsAPI key validation failed:", test_data.get("message", "Unknown error")
        )
except Exception as e:
    print("Error validating NewsAPI key:", str(e))


@app.route("/")
def index():
    return render_template("index.html", news=[])


@app.route("/api/news", methods=["GET"])
def get_news():
    query = request.args.get("query", "")
    print(f"Using NEWS_API_KEY: {NEWS_API_KEY[:10]}...")

    if not query:
        return jsonify({"error": "Search query is required"}), 400

    try:
        print(f"Searching news for query: {query}")
        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 10,
            "apiKey": NEWS_API_KEY,
        }

        # デバッグ用：実際のリクエストURLを表示
        request_url = (
            NEWS_API_BASE_URL
            + "?"
            + "&".join([f"{k}={v}" for k, v in params.items() if k != "apiKey"])
        )
        print(f"Request URL (without API key): {request_url}")

        response = requests.get(NEWS_API_BASE_URL, params=params)
        news_data = response.json()

        print("NewsAPI Response Status:", news_data.get("status"))
        if news_data.get("articles"):
            print("NewsAPI Response Articles Count:", len(news_data.get("articles")))

        if news_data.get("status") != "ok":
            error_msg = f"NewsAPI Error: {news_data.get('message', 'Unknown error')}"
            print(error_msg)
            print("Full response:", news_data)
            return jsonify({"error": error_msg}), 400

        return jsonify(news_data)
    except Exception as e:
        error_msg = f"Error fetching news: {str(e)}"
        print(error_msg)
        return jsonify({"error": error_msg}), 500


@app.route("/api/summarize", methods=["POST"])
def summarize():
    data = request.json
    text = data.get("text", "")
    print(f"Received text to summarize (first 100 chars): {text[:100]}...")

    try:
        print("Creating OpenAI chat completion...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": """あなたはXに多数のフォロワーを抱えた、テンションが高めでポジティブなアカウントを運用しています。
以下の英語記事を日本語に翻訳・要約する際は、以下の点に注意してください：

1. 英語の記事を日本語に翻訳し、Xに投稿する際に有意義な情報となるよう、重要なポイントを簡潔に伝えてください
2. あなたはおじゃる丸です。「〜でおじゃる」が口癖の可愛い少年が投稿するような、ちょっと風変わりでポジティブな口調で記述してください
   例：「すごいでおじゃる〜！」「これは雅でおじゃる」「まことか...！」「おじゃる〜！」など
3. 要約は3-4文程度で簡潔にまとめてください
4. 適切な絵文字を2-3個使用して、テンションの高さを表現してください（ただし多用は避ける）
5. 重要な数字やデータがある場合は、それを「すごいでおじゃる〜！」「か〜ず〜ま〜！」などの感嘆表現とともに含めてください
6. 過度にセンセーショナルな表現は避けつつも、ポジティブで前向きなトーンを維持してください
7. 日本のユーザーにとって特に関連性が高い情報は「これは日本でも来るでおじゃる！」などの形で強調してください
8. 記事の面白さや驚きを「おじゃ〜！」「趣深いでおじゃる！」などの表現で伝えてください""",
                },
                {"role": "user", "content": text},
            ],
        )
        summary = response.choices[0].message.content
        print(f"Generated summary (first 100 chars): {summary[:100]}...")
        return jsonify({"summary": summary})
    except Exception as e:
        error_msg = f"Error summarizing text: {str(e)}"
        print(error_msg)
        return jsonify({"error": error_msg}), 500


if __name__ == "__main__":
    app.run(debug=True, port=4000)
