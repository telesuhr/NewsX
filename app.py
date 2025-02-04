from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from dotenv import load_dotenv
import requests
from openai import OpenAI
import tweepy

# 最初に環境変数を読み込む
load_dotenv(override=True)

# 環境変数の読み込みと検証
def get_env_var(name):
    value = os.getenv(name)
    if not value:
        raise ValueError(f"環境変数 {name} が設定されていません")
    return value.strip().strip('"').strip("'")

# 環境変数の取得
OPENAI_API_KEY = get_env_var("OPENAI_API_KEY")
NEWS_API_KEY = get_env_var("NEWS_API_KEY")
TWITTER_API_KEY = get_env_var("TWITTER_API_KEY")
TWITTER_API_SECRET = get_env_var("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = get_env_var("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = get_env_var("TWITTER_ACCESS_TOKEN_SECRET")
TWITTER_BEARER_TOKEN = get_env_var("TWITTER_BEARER_TOKEN")

# APIキーの検証用出力
print("\nAPI Keys:")
print(f"OpenAI API Key: {OPENAI_API_KEY[:10]}...")
print(f"News API Key: {NEWS_API_KEY[:10]}...")

# OpenAI APIクライアントの初期化
openai_client = OpenAI(
    api_key=OPENAI_API_KEY
)

# Twitter認証情報の表示
print("\nTwitter Credentials:")
print(f"API Key: {TWITTER_API_KEY[:5]}...")
print(f"API Secret: {TWITTER_API_SECRET[:5]}...")
print(f"Access Token: {TWITTER_ACCESS_TOKEN[:5]}...")
print(f"Access Token Secret: {TWITTER_ACCESS_TOKEN_SECRET[:5]}...")
print(f"Bearer Token: {TWITTER_BEARER_TOKEN[:5]}...")

# Twitter認証 (OAuth 2.0)
client = tweepy.Client(
    bearer_token=TWITTER_BEARER_TOKEN,
    consumer_key=TWITTER_API_KEY,
    consumer_secret=TWITTER_API_SECRET,
    access_token=TWITTER_ACCESS_TOKEN,
    access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
    wait_on_rate_limit=True
)

# アプリケーションのルートディレクトリを取得
root_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(root_dir, "templates")
env_path = os.path.join(root_dir, ".env")
print(f"\n現在のディレクトリ: {root_dir}")
print(f"環境変数ファイルのパス: {env_path}")
print(f"環境変数ファイルは存在する?: {os.path.exists(env_path)}")

if os.path.exists(env_path):
    print("\n.envファイルの内容:")
    with open(env_path, "r") as f:
        for line in f:
            # APIキーの最初の5文字だけを表示
            if "=" in line and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                print(f"{key}={value[:5]}...")

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


app = Flask(__name__, template_folder=template_dir)
CORS(app)


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
    try:
        data = request.json
        text = data.get("text", "")
        character = data.get("character", "default")

        if not text:
            return jsonify({"error": "テキストが空です"}), 400

        print(f"Received text to summarize (first 100 chars): {text[:100]}...")
        print(f"Creating OpenAI chat completion for character: {character}")

        try:
            # キャラクター別のプロンプトを設定
            character_prompts = {
                "ojaru": """あなたは「おじゃる丸」のように話す、明るく元気なキャラクターです。
以下のニュースを、以下の特徴を持つように要約してください：
- 「〜じゃ」「〜でおじゃる」などのおじゃる口調を使う
- 元気で明るい口調で話す
- 絵文字を適切に使用する
- 重要なポイントを分かりやすく伝える
- 140文字程度に要約する""",

                "techwriter": """あなたは技術系ライターです。
以下のニュースを、以下の特徴を持つように要約してください：
- 技術的な観点から分析する
- 業界への影響や技術トレンドに言及する
- 専門用語を適切に使用する
- 絵文字を適切に使用する
- 客観的な視点を維持する
- 140文字程度に要約する""",

                "investor": """あなたは投資家です。
以下のニュースを、以下の特徴を持つように要約してください：
- 市場や株価への影響を分析する
- 投資判断に役立つ情報を提供する
- 財務や経済の専門用語を適切に使用する
- 絵文字を適切に使用する
- 140文字程度に要約する""",

                "analyst": """あなたは経済アナリストです。
以下のニュースを、以下の特徴を持つように要約してください：
- マクロ経済の視点から分析する
- 業界動向や市場への影響を考察する
- 経済用語を適切に使用する
- データや数値を効果的に活用する
- 絵文字を適切に使用する
- 140文字程度に要約する""",

                "default": """以下のニュースを要約してください：
- 重要なポイントを簡潔に伝える
- 分かりやすい言葉を使用する
- 絵文字を適切に使用する
- 140文字程度に要約する"""
            }

            prompt = character_prompts.get(character, character_prompts["default"])

            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text}
                ],
                max_tokens=200,
                temperature=0.7
            )

            summary = response.choices[0].message.content.strip()
            print(f"Generated summary (first 100 chars): {summary[:100]}...")

            return jsonify({"summary": summary})

        except Exception as api_error:
            error_msg = f"OpenAI APIエラー: {str(api_error)}"
            print(error_msg)
            print("エラーの詳細:")
            print(f"Error Type: {type(api_error).__name__}")
            print(f"Error Args: {api_error.args}")
            return jsonify({
                "error": error_msg,
                "details": {
                    "error_type": type(api_error).__name__,
                    "error_args": api_error.args
                }
            }), 500

    except Exception as e:
        error_msg = f"要約処理に失敗しました: {str(e)}"
        print(error_msg)
        print("エラーの詳細:")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Args: {e.args}")
        return jsonify({
            "error": error_msg,
            "details": {
                "error_type": type(e).__name__,
                "error_args": e.args
            }
        }), 500


@app.route("/api/post_to_x", methods=["POST"])
def post_to_x():
    try:
        data = request.json
        text = data.get("text", "")
        url = data.get("url", "")  # URLを取得
        
        if not text:
            return jsonify({"error": "テキストが空です"}), 400
            
        # URLがある場合は、テキストの末尾に追加
        if url:
            # 140文字制限を考慮してテキストを調整
            max_text_length = 140 - len(url) - 1  # URLの長さ + スペース1文字分
            if len(text) > max_text_length:
                text = text[:max_text_length-3] + "..."
            post_text = f"{text} {url}"
        else:
            post_text = text
            
        # 認証情報を再確認
        print("\nPosting to Twitter with credentials:")
        print(f"API Key: {TWITTER_API_KEY[:5]}...")
        print(f"API Secret: {TWITTER_API_SECRET[:5]}...")
        print(f"Access Token: {TWITTER_ACCESS_TOKEN[:5]}...")
        print(f"Access Token Secret: {TWITTER_ACCESS_TOKEN_SECRET[:5]}...")
        print(f"Bearer Token: {TWITTER_BEARER_TOKEN[:5]}...")
            
        # API v2でツイート投稿
        try:
            response = client.create_tweet(text=post_text)
            if response and response.data:
                tweet_id = response.data["id"]
                return jsonify({
                    "success": True,
                    "tweet_id": tweet_id,
                    "tweet_url": f"https://twitter.com/i/web/status/{tweet_id}"
                })
        except tweepy.errors.Unauthorized as e:
            error_msg = f"Twitter認証エラー: {str(e)}"
            print(error_msg)
            print("エラーの詳細:")
            print(f"Response Status Code: {getattr(e, 'response', {}).get('status_code', 'N/A')}")
            print(f"Response Text: {getattr(e, 'response', {}).get('text', 'N/A')}")
            print(f"API Error Code: {getattr(e, 'api_code', 'N/A')}")
            print(f"API Error Message: {getattr(e, 'api_messages', 'N/A')}")
            return jsonify({
                "error": error_msg,
                "details": {
                    "status_code": getattr(e, 'response', {}).get('status_code', 'N/A'),
                    "error_text": getattr(e, 'response', {}).get('text', 'N/A'),
                    "api_code": getattr(e, 'api_code', 'N/A'),
                    "api_messages": getattr(e, 'api_messages', 'N/A')
                }
            }), 401
        except tweepy.errors.Forbidden as e:
            error_msg = f"Twitter APIアクセス制限エラー: {str(e)}"
            print(error_msg)
            print("エラーの詳細:")
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Args: {e.args}")
            return jsonify({
                "error": error_msg,
                "details": {
                    "error_type": type(e).__name__,
                    "error_args": e.args,
                    "message": "このエンドポイントにアクセスするには、Twitter Developer Portalでの追加設定が必要な可能性があります。"
                }
            }), 403
        except tweepy.errors.TweepyException as e:
            error_msg = f"Twitterエラー: {str(e)}"
            print(error_msg)
            print("エラーの詳細:")
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Args: {e.args}")
            return jsonify({
                "error": error_msg,
                "details": {
                    "error_type": type(e).__name__,
                    "error_args": e.args
                }
            }), 500
            
    except Exception as e:
        error_msg = f"ツイートの投稿に失敗しました: {str(e)}"
        print(error_msg)
        print("エラーの詳細:")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Args: {e.args}")
        return jsonify({
            "error": error_msg,
            "details": {
                "error_type": type(e).__name__,
                "error_args": e.args
            }
        }), 500


if __name__ == "__main__":
    app.run(debug=True, port=4000)
