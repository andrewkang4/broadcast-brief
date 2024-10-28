import os
import requests
import json
from collections import deque

# Function to fetch a tweet by ID
def get_tweet_by_id(bearer_token, tweet_id, tweet_fields=None):
    url = "https://api.twitter.com/2/tweets"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }
    params = {
        "ids": tweet_id
    }
    if tweet_fields:
        params["tweet.fields"] = ",".join(tweet_fields)

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        raise Exception(f"Cannot fetch tweet: {response.status_code} - {response.text}")

    return response.json()

# Function to search for replies using conversation_id
def search_replies(bearer_token, conversation_id, max_results=100, tweet_fields=None, expansions=None, user_fields=None):
    search_url = "https://api.twitter.com/2/tweets/search/recent"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }
    query = f"conversation_id:{conversation_id} -is:retweet"
    params = {
        "query": query,
        "max_results": max_results
    }
    if tweet_fields:
        params["tweet.fields"] = ",".join(tweet_fields)
    if expansions:
        params["expansions"] = ",".join(expansions)
    if user_fields:
        params["user.fields"] = ",".join(user_fields)

    all_replies = []
    next_token = None

    while True:
        if next_token:
            params["next_token"] = next_token

        response = requests.get(search_url, headers=headers, params=params)

        if response.status_code != 200:
            raise Exception(f"Search request failed: {response.status_code} - {response.text}")

        data = response.json()
        if "data" in data:
            all_replies.extend(data["data"])

        if "meta" in data and "next_token" in data["meta"]:
            next_token = data["meta"]["next_token"]
        else:
            break  # No more pages

    return all_replies

# Function to perform BFS and get replies up to 3 levels deep
def get_replies_bfs(bearer_token, conversation_id, max_depth=3):
    reply_tweet_fields = ["author_id", "conversation_id", "created_at", "in_reply_to_user_id", "text"]
    reply_user_fields = ["username", "name"]
    expansions = ["author_id"]

    # Use a deque to handle BFS
    queue = deque([(conversation_id, 0)])  # (conversation_id, level)
    all_replies = []
    visited_conversations = set() 
    level_concatenated_replies = []

    while queue:
        current_conversation_id, level = queue.popleft()

        if level >= max_depth:
            break

        if current_conversation_id in visited_conversations:
            continue

        visited_conversations.add(current_conversation_id)

        replies = search_replies(
            bearer_token,
            current_conversation_id,
            max_results=100,
            tweet_fields=reply_tweet_fields,
            expansions=expansions,
            user_fields=reply_user_fields
        )

        concatenated_replies = "\n".join(set([reply.get("text", "") for reply in replies]))
        if concatenated_replies:
            level_concatenated_replies.append(concatenated_replies)

        for reply in replies:
            all_replies.append(reply)
            if "conversation_id" in reply:
                queue.append((reply["conversation_id"], level + 1))

    return "\n".join(level_concatenated_replies)

def fetch_replies(tweet_id):
    bearer_token = os.environ.get("X_BEARER_TOKEN")
    if not bearer_token:
        raise ValueError("Error: Please set the BEARER_TOKEN environment variable.")

    tweet_fields = ["conversation_id"]
    original_tweet = get_tweet_by_id(
        bearer_token, 
        tweet_id, 
        tweet_fields=tweet_fields
    )

    if "data" not in original_tweet or not original_tweet["data"]:
        raise ValueError("Original tweet not found.")

    conversation_id = original_tweet["data"][0]["conversation_id"]

    concatenated_replies = get_replies_bfs(
        bearer_token,
        conversation_id,
        max_depth=5
    )

    return concatenated_replies

print(fetch_replies('1845262727888945596'))