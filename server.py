from flask import Flask, request, send_file
import asyncio
import edge_tts
import os

app = Flask(__name__)

async def generate_audio(text, output_file):
    voice = "vi-VN-HoaiMyNeural" # Giọng nữ mượt mà, tự nhiên
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

@app.route('/tts', methods=['POST'])
def tts():
    try:
        data = request.get_json()
        text = data.get('text', '')
        if not text:
            return {"error": "Không có nội dung"}, 400

        output_file = "temp_edge.mp3"
        
        # Chạy bất đồng bộ
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(generate_audio(text, output_file))

        return send_file(output_file, mimetype="audio/mp3")

    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/')
def home():
    return "Server Edge-TTS đang hoạt động hoàn hảo!"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
