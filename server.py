from flask import Flask, request, send_file
from flask_cors import CORS
import asyncio
import edge_tts
import os

app = Flask(__name__)
CORS(app)

async def generate_audio(text, output_file):
    voice = "vi-VN-HoaiMyNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

@app.route('/tts', methods=['POST'])
def tts():
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        if not text:
            return {"error": "Không có nội dung"}, 400

        output_file = f"temp_{os.getpid()}_{int(asyncio.get_event_loop().time())}.mp3"
        
        # Thử tạo file audio với edge-tts
        asyncio.run(generate_audio(text, output_file))

        if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
            return {"error": "Không tạo được file âm thanh"}, 500

        response = send_file(output_file, mimetype="audio/mp3", as_attachment=False)
        return response

    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/')
def home():
    return "Server Edge-TTS đang hoạt động hoàn hảo!"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
