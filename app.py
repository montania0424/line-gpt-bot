## ■ ファイル構成
# line_gpt_amazon_bot/
# ├― app.py
# ├― requirements.txt
# └― Procfile

# ========================
# app.py
# ========================
from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from openai import OpenAI
import os, urllib.parse

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AMAZON_TAG = "montania0424-22"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
client = OpenAI(api_key=OPENAI_API_KEY)

def generate_keywords(user_input):
    prompt = f"""
    ユーザーが曖昧なニュアンスで欲しい商品を言います。
    その内容をもとにAmazonで検索するためのキーワードを一行で作ってください。

    ユーザー: {user_input}
    検索キーワード:
    """
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=50
    )
    return response.choices[0].message.content.strip()

def generate_product_recommendations(keyword):
    prompt = f"""
    「{keyword}」でAmazonを検索したとして人気の商品を3件選び、次の順で情報を紹介してください:
- 商品名
- おすすめポイント
- 価格相場

それぞれの商品に対してAmazonのアフィリエイトリンク (https://www.amazon.co.jp/s?k=...) を「tag={AMAZON_TAG}」付きで作成して表示してください。

日本語の読みやすい文章で簡潔に回答してください。
    """
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=700
    )
    return response.choices[0].message.content.strip()

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return 'Invalid signature', 400
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_input = event.message.text
    keyword = generate_keywords(user_input)
    product_summary = generate_product_recommendations(keyword)

    reply_text = f"「{keyword}」の検索結果から人気商品を3件紹介するよ！\n\n{product_summary}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
