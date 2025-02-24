from flask import Flask, request, jsonify, render_template
import openai
import re
from fuzzywuzzy import process
import os

# ✅ Load API Key from Environment Variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# ✅ Set a Password for Access
ACCESS_PASSWORD = "training123"  # Change this to any password you want

# ✅ Load training text from file
with open("training_text.txt", "r", encoding="utf-8") as f:
    training_text = f.read()

# ✅ Clean and process the text
clean_text = re.sub(r'[^\x00-\x7F]+', ' ', training_text)
paragraphs = [p.strip() for p in clean_text.split("\n\n") if len(p.strip()) > 100]

app = Flask(__name__, template_folder="templates")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["GET"])
def chat():
    password = request.args.get("password", "").strip()
    user_query = request.args.get("question", "").strip()

    if password != ACCESS_PASSWORD:
        return jsonify({"error": "Unauthorized. Please provide the correct password."}), 403

    if not user_query:
        return jsonify({"error": "Please provide a question"}), 400

    # ✅ Find best matches from the book
    best_matches = process.extract(user_query, paragraphs, limit=3)

    # ✅ Remove unwanted matches
    filtered_matches = [
        match[0] for match in best_matches
        if not any(word in match[0][:50] for word in ["Table of Contents", "Chapter", "Index", "About the Author"])
    ]

    # ✅ Send best match to ChatGPT
    if filtered_matches:
        context = "\n".join(filtered_matches[:3])
        prompt = f"Based on the following training book content, answer the question:\n\n{context}\n\nUser Question: {user_query}\n\nAnswer:"

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        answer = response.choices[0].message.content

        # ✅ Format response with bullet points
        formatted_answer = answer.replace("\n", "\n• ")
        return jsonify({"answer": f"• {formatted_answer}"})

    return jsonify({"answer": "Sorry, I couldn't find an answer. Try asking differently."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
