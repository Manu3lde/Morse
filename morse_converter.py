from abc import ABC, abstractmethod
from pydub import AudioSegment
import numpy as np
import json
import argparse, sys, shutil, os, subprocess

# Morse Code Dictionary
MORSE_CODE_DICT = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.',
    'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---',
    'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---',
    'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
    'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--',
    'Z': '--..', '0': '-----', '1': '.----', '2': '..---', '3': '...--',
    '4': '....-', '5': '.....', '6': '-....', '7': '--...', '8': '---..',
    '9': '----.', ' ': '/'
}

# Encoder Interface
class Encoder(ABC):
    @abstractmethod
    def encode(self, data: str) -> str:
        pass

    @abstractmethod
    def decode(self, data: str) -> str:
        pass

# Morse Encoder
class MorseEncoder(Encoder):
    def encode(self, text: str) -> str:
        return ' '.join(MORSE_CODE_DICT.get(char.upper(), '') for char in text)

    def decode(self, morse: str) -> str:
        reverse_dict = {v: k for k, v in MORSE_CODE_DICT.items()}
        return ''.join(reverse_dict.get(code, '') for code in morse.split())

# Substitution Cipher (Example Encryption)
class SubstitutionCipher(Encoder):
    def __init__(self, key: str):
        self.key = key  # Example: "swap" for dot-dash swap

    def encode(self, morse: str) -> str:
        return morse.replace('.', 'X').replace('-', '.').replace('X', '-')

    def decode(self, morse: str) -> str:
        return self.encode(morse)  # Symmetric

# Encoder Chain for Multiple Layers
class EncoderChain:
    def __init__(self):
        self.encoders = []

    def add_encoder(self, encoder: Encoder):
        self.encoders.append(encoder)

    def encode(self, data: str) -> str:
        for encoder in self.encoders:
            data = encoder.encode(data)
        return data

    def decode(self, data: str) -> str:
        for encoder in reversed(self.encoders):
            data = encoder.decode(data)
        return data

# Audio Generation Function
def generate_morse_audio(morse: str, freq: float = 750, dot_duration: int = 100) -> AudioSegment:
    def generate_tone(duration: int) -> AudioSegment:
        t = np.linspace(0, duration / 1000, int(44100 * duration / 1000), False)
        waveform = np.sin(2 * np.pi * freq * t) * 0.5  # 50% volume (float -1..1)
        # convert to 16-bit PCM signed integers and pass raw bytes to pydub
        pcm16 = (waveform * 32767).astype(np.int16)
        return AudioSegment(pcm16.tobytes(), frame_rate=44100, sample_width=2, channels=1)

    silence = lambda ms: AudioSegment.silent(duration=ms)
    # add 3 seconds silence at start
    audio = silence(3000)

    for symbol in morse:
        if symbol == '.':
            audio += generate_tone(dot_duration)
            audio += silence(dot_duration)
        elif symbol == '-':
            audio += generate_tone(dot_duration * 3)
            audio += silence(dot_duration)
        elif symbol == ' ':
            audio += silence(dot_duration * 2)  # Gap between letters
        elif symbol == '/':
            audio += silence(dot_duration * 6)  # Gap between words

    # add 3 seconds silence at end
    audio += silence(3000)

    return audio

# Save Audio Function (small improvement to report errors)
def save_audio(audio: AudioSegment, filename: str, format: str = "mp3"):
    try:
        audio.export(filename, format=format)
        print(f"Saved audio to {filename} (format={format})")
    except Exception as e:
        print(f"Failed to save audio to {filename}: {e}")
        print("Make sure ffmpeg is installed and available on PATH for pydub.")
        sys.exit(1)

# Load Config Function
def load_config(config_file: str) -> dict:
    try:
        with open(config_file, 'r') as f:
            cfg = json.load(f)
            return cfg
    except FileNotFoundError:
        print(f"Configuration file not found: {config_file}")
        print("Create a config.json in the same folder or pass --config <path>.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Configuration file {config_file} is not valid JSON.")
        sys.exit(1)

# Main Function
def main():
    parser = argparse.ArgumentParser(description="Morse code -> audio generator")
    parser.add_argument("--text", "-t", help="Text to convert to Morse (if not provided, prompted interactively)")
    parser.add_argument("--out", "-o", default=None, help="Output filename (default: output.<format> from config)")
    parser.add_argument("--config", "-c", default="config.json", help="Path to config.json")
    args = parser.parse_args()

    print("Morse Converter starting...")
    print("Ensure dependencies: pydub, numpy and ffmpeg (ffmpeg on PATH).")
    print("Run: python morse_converter.py --text \"Hello\" --out myfile.mp3\n")

    config = load_config(args.config)
    print(f"Loaded config: freq={config.get('freq')}, dot_duration={config.get('dot_duration')}, encryption={config.get('encryption')}, output_format={config.get('output_format')}")

    # determine output filename
    out_filename = args.out if args.out else f"output.{config.get('output_format', 'mp3')}"

    # get text (CLI arg or prompt)
    if args.text:
        text = args.text
        print(f"Using text from CLI: {text}")
    else:
        try:
            text = input("Enter text to convert: ")
        except KeyboardInterrupt:
            print("\nAborted by user.")
            sys.exit(0)

    # Set up encoder chain
    chain = EncoderChain()
    chain.add_encoder(MorseEncoder())

    # Add encryption if specified
    if config.get("encryption") == "substitution":
        chain.add_encoder(SubstitutionCipher(key="swap"))

    # Encode the text
    print("Encoding text to Morse...")
    morse = chain.encode(text)
    print(f"Morse output (first 200 chars): {morse[:200]}")

    # Generate audio
    print("Generating audio (this may take a moment)...")
    audio = generate_morse_audio(morse, config.get("freq", 750), config.get("dot_duration", 100))

    # Save output
    print(f"Saving audio to {out_filename} ...")
    save_audio(audio, out_filename, format=config.get("output_format", "mp3"))

    print("Done. Tip: If the MP3 won't play, ensure ffmpeg is installed and reachable by pydub.")

#this is a fix
if __name__ == "__main__":
    main()