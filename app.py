from flask import Flask, request, jsonify
import openai
import re
from fuzzywuzzy import process
import os

# ✅ Load API Key from Environment Variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# ✅ Load training text from file
with open("training_text.txt", "r", encoding="utf-8") as f:
    training_text = f.read()

# ✅ Clean and process the text
clean_text = re.sub(r'[^\x00-\x7F]+', ' ', training_text)
paragraphs = [p.strip() for p in clean_text.split("\n\n") if len(p.strip()) > 100]

app = Flask(__name__)

@app.route("/chat", methods=["GET"])
def chat():
    user_query = request.args.get("question", "").strip()

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
        return jsonify({"answer": answer})

    return jsonify({"answer": "Sorry, I couldn't find an answer. Try asking differently."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
