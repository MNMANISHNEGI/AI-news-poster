import requests

from dotenv import load_dotenv
import os
load_dotenv()

GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")

# === CONFIG ===


# === FUNCTIONS ===

def get_latest_ai_news():
    url = f"https://gnews.io/api/v4/search?q=artificial+intelligence&lang=en&sortby=publishedAt&token={GNEWS_API_KEY}"
    response = requests.get(url)
    articles = response.json().get("articles", [])
    if articles:
        return articles[0]
    return None


def generate_facebook_post(title, description, link):
    prompt = f"""
    Write a short, engaging Facebook post about this AI news:
    Title: {title}
    Description: {description}
    Link: {link}

    Add emojis, 2 relevant hashtags, and a call-to-action like 'What do you think?'
    """

    response = requests.post(
        "https://api.together.xyz/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {TOGETHER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",  
            "messages": [
                { "role": "user", "content": prompt }
            ],
            "temperature": 0.7,
            "max_tokens": 300
        }
    )

    data = response.json()
    if 'choices' in data and data['choices']:
        return data['choices'][0]['message']['content'].strip()
    else:
        return "⚠️ Error: Could not generate a Facebook post."


def post_to_facebook(message):
    url = f"https://graph.facebook.com/{FB_PAGE_ID}/feed"
    response = requests.post(url, data={
        "message": message,
        "access_token": FB_PAGE_ACCESS_TOKEN
    })
    return response.json()


def chat_with_gpt(user_input, chat_history):
    # Convert chat history to Together-compatible format
    messages = []
    for entry in chat_history:
        messages.append({
            "role": entry["role"],
            "content": entry["content"]
        })
    messages.append({
        "role": "user",
        "content": user_input
    })

    response = requests.post(
        "https://api.together.xyz/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {TOGETHER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 300
        }
    )

    data = response.json()
    if 'choices' in data and data['choices']:
        reply = data['choices'][0]['message']['content'].strip()
        chat_history.append({"role": "user", "content": user_input})
        chat_history.append({"role": "assistant", "content": reply})
        return reply
    else:
        return " Failed to get a response from Together.ai"


# === CHAT LOOP ===

def chatbot():
    print("Jarvis | Type 'exit' to quit | Type 'post latest ai news' to post")
    chat_history = [{"role": "system", "content": "You are a helpful assistant."}]

    while True:
        user_input = input("👤 You: ").strip()

        if user_input.lower() == "exit":
            print(" Goodbye!")
            break

        elif user_input.lower().startswith("post this:"):
            message = user_input[len("post this:"):].strip()
            result = post_to_facebook(message)
            if "id" in result:
                print(" Posted to Facebook! Post ID:", result["id"])
            else:
                print(" Failed to post:", result)

        elif user_input.lower() == "post latest ai news":
            print(" Fetching latest AI news...")
            article = get_latest_ai_news()
            if not article:
                print("❌ No news found.")
                continue
            title, desc, link = article["title"], article["description"], article["url"]
            post = generate_facebook_post(title, desc, link)
            print(" Suggested Post:\n", post)
            confirm = input("\n Post this to Facebook? (y/n): ").strip().lower()
            if confirm == "y":
                result = post_to_facebook(post)
                if "id" in result:
                    print(" Posted to Facebook! Post ID:", result["id"])
                else:
                    print(" Failed to post:", result)
            else:
                print(" Post canceled.")

        else:
            response = chat_with_gpt(user_input, chat_history)
            print(" GPT:", response)


# === RUN ===
if __name__ == "__main__":
    chatbot()
