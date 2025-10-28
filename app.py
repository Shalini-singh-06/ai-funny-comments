from flask import Flask, render_template, request, jsonify
from gtts import gTTS
import google.generativeai as genai
import instaloader
from youtube_transcript_api import YouTubeTranscriptApi
import requests
import os
from dotenv import load_dotenv
from urllib.error import HTTPError

# ---------- Load environment variables ----------
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("❌ GEMINI_API_KEY not found in .env file!")

# ---------- Configure Gemini API ----------
genai.configure(api_key=api_key)

app = Flask(__name__)

# ---------- Get video info (YouTube / Instagram) ----------
def get_video_info(link):
    try:
        if "youtube.com" in link or "youtu.be" in link or "shorts" in link:
            return fetch_youtube_info(link)
        elif "instagram.com" in link:
            return fetch_instagram_info(link)
        else:
            return "Funny or trending video"
    except Exception as e:
        print("⚠️ Error fetching info:", e)
        return "Funny trending video"


# ---------- YouTube Shorts info ----------
def fetch_youtube_info(url):
    try:
        # Extract video ID
        video_id = None
        if "v=" in url:
            video_id = url.split("v=")[1].split("&")[0]
        elif "shorts/" in url:
            video_id = url.split("shorts/")[1].split("?")[0]

        if not video_id:
            raise ValueError("Invalid YouTube URL")

        # Try fetching transcript
        transcript_text = ""
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
            transcript_text = " ".join([t["text"] for t in transcript])
        except Exception:
            transcript_text = ""

        # Get title & author
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        response = requests.get(oembed_url)
        response.raise_for_status()
        data = response.json()

        title = data.get("title", "")
        author = data.get("author_name", "")

        combined_text = f"Video Title: {title}\nUploader: {author}\nTranscript: {transcript_text}"
        if len(combined_text) < 50:
            combined_text += " (Funny video short clip, make creative reactions!)"

        return combined_text.strip()

    except HTTPError as e:
        print(f"⚠️ YouTube fetch failed: {e}")
        return "Funny YouTube video"
    except Exception as e:
        print(f"⚠️ Error while fetching YouTube info: {e}")
        return "Funny YouTube short video"


# ---------- Instagram Reels info ----------
def fetch_instagram_info(url):
    try:
        # Extract shortcode
        shortcode = url.split("/")[-2]
        L = instaloader.Instaloader()
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        caption = post.caption or "Funny Instagram video"
        return f"Instagram Reel Caption: {caption}"
    except Exception as e:
        print(f"⚠️ Instagram fetch failed: {e}")
        # fallback when post is private or login required
        return "Funny Instagram Reel or meme video"


# ---------- Generate funny Hinglish comments ----------
def generate_comment(description):
    prompt = f"""
    Tum ek creative aur funny social media comment generator ho 😎  
    Niche diye gaye video ke liye 10 unique, hilarious, aur engaging comments likho.  
    Comments **Hinglish (Hindi + English mix)** me ho — jaise real log likhte hain.  
    Har comment ka tone alag ho — funny, savage, emotional, crazy, ya sarcastic.  
    Har comment short (max 12 words) aur emoji ke sath ho 😄  
    Output numbered list me do (1 se 10 tak).  
    Comments realistic aur trend-style hone chahiye (Instagram & YouTube Reels tone me).

    Video info: "{description}"
    """

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    return response.text.strip()


# ---------- Generate Hindi voice ----------
def generate_voice(text, filename="static/comment_hi.mp3"):
    tts = gTTS(text, lang="hi")
    tts.save(filename)


# ---------- Flask Routes ----------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    link = data.get("link", "").strip()

    desc = get_video_info(link)
    comments = generate_comment(desc)
    generate_voice(comments)

    return jsonify({
        "comments": comments,
        "audio": "/static/comment_hi.mp3"
    })


# ---------- Run app ----------
if __name__ == "__main__":
    if not os.path.exists("static"):
        os.mkdir("static")
    app.run(debug=True)
