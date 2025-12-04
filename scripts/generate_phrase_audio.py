"""
Generate audio files for all quick phrases (offline cache)
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

from tts import ElevenLabsTTS

# 20 Quick Phrases
QUICK_PHRASES = [
    "すみません！",
    "お会計お願いします",
    "トイレはどこですか？",
    "カードは使えますか？",
    "おすすめは何ですか？",
    "これをください",
    "水をください",
    "メニューをください",
    "アレルギーがあります",
    "辛くしないでください",
    "いらっしゃいませ",
    "少々お待ちください",
    "お待たせいたしました",
    "かしこまりました",
    "申し訳ございません",
    "ありがとうございました",
    "またのお越しをお待ちしております",
    "こちらへどうぞ",
    "ご注文はお決まりですか？",
    "以上でよろしいですか？",
]

def generate_all_audio():
    audio_dir = Path(__file__).parent.parent / 'audio'
    audio_dir.mkdir(exist_ok=True)

    tts = ElevenLabsTTS()

    print(f"Generating audio for {len(QUICK_PHRASES)} phrases...")
    print(f"Output directory: {audio_dir}")
    print()

    for i, phrase in enumerate(QUICK_PHRASES, 1):
        # Create safe filename from phrase
        safe_name = phrase.replace('！', '').replace('？', '').replace('、', '_')
        filename = f"{safe_name}.mp3"
        filepath = audio_dir / filename

        if filepath.exists():
            print(f"[{i}/{len(QUICK_PHRASES)}] Skip (exists): {phrase}")
            continue

        print(f"[{i}/{len(QUICK_PHRASES)}] Generating: {phrase}")

        try:
            audio_data = tts.generate_speech(phrase, sister="User")
            if audio_data:
                with open(filepath, 'wb') as f:
                    f.write(audio_data)
                print(f"  -> Saved: {filename}")
            else:
                print(f"  -> Error: No audio data returned")
        except Exception as e:
            print(f"  -> Error: {e}")

    print()
    print("Done!")
    print(f"Audio files: {len(list(audio_dir.glob('*.mp3')))}")

if __name__ == '__main__':
    generate_all_audio()
