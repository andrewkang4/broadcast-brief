import os
import json
import requests
import tweepy
import asyncio
from flask import Flask, render_template, request, jsonify

NUM_SENTENCES = 1

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"

API_KEY = ""
POST_IDS = []

CONVERSATION = [{
    "role":
    "user",
    "content":
    """
Create a concise social media post for X that combines the information from the following text and image. The post should reflect key details from both sources, ensuring they complement each other effectively. If there is important information in the image that is relevant to the text but not in the text, please include it in the post. Keep the post content under 280 characters.

For example, if the input is talking about an event and the image shows some number of people, include the number of people in the post.

Please return only the post content. Do not return any other text.
"""
}]

LATEST = []

CURR_NUM_SENTENCES = 0

async def create_chat_completion(conversation):
    api_key = os.getenv("XAI_API_KEY")
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "messages": conversation,
        "model": "grok-vision-preview",
        "stream": False,
    }

    print("HERE")
    full_response = []
    with requests.post(url, headers=headers, json=data,
                       stream=False) as response:
        response.raise_for_status()
        full_response = response.json()["choices"][0]["message"]["content"]
    print("HERE2")
    return full_response

async def make_post(post):
    ACCESS_KEY = os.getenv("X_ACCESS_TOKEN")
    ACCESS_SECRET = os.getenv("X_ACCESS_SECRET")
    CONSUMER_KEY = os.getenv("X_API_KEY")
    CONSUMER_SECRET = os.getenv("X_API_SECRET")

    api = tweepy.Client(access_token=ACCESS_KEY,
                        access_token_secret=ACCESS_SECRET,
                        consumer_key=CONSUMER_KEY,
                        consumer_secret=CONSUMER_SECRET)

    test = api.create_tweet(text=post)
    print("TEST", test)
    post_id = test.data['id'] if test.data else None
    if post_id:
        POST_IDS.append(post_id)
        print(f"Post ID {post_id} saved to global list")

async def summarize_and_make_post(conversation):
    post = await create_chat_completion(conversation)
    await make_post(post)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_sentence', methods=['POST'])
def process_sentence():
    global LATEST, CURR_NUM_SENTENCES, NUM_SENTENCES

    data = request.json
    sentence = data.get('sentence', '')

    base64_image = data.get('image', '')

    LATEST.append(sentence.lower())
    CURR_NUM_SENTENCES += 1

    if CURR_NUM_SENTENCES == NUM_SENTENCES:
        CURR_NUM_SENTENCES = 0
        current_conv = {
            "role":
            "user",
            "content": [{
                "type": "text",
                "text": " ".join(LATEST)
            }, {
                "type": "image_url",
                "image_url": {
                    "url": base64_image
                }
            }]
        }

        CONVERSATION.append(current_conv)
        asyncio.run(summarize_and_make_post(CONVERSATION))

    processed_sentence = sentence.lower()

    return jsonify({'processed_sentence': processed_sentence})

@app.route('/user-agent')
def get_user_agent():
    user_agent = request.headers.get('User-Agent')
    return jsonify({'user_agent': user_agent})

if __name__ == '__main__':
    LATEST = []
    CURR_NUM_SENTENCES = 0
    app.run(host='0.0.0.0', port=5000)