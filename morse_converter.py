from abc import ABC, abstractmethod
from pydub import AudioSegment
import numpy as np
import json

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
        audio = np.sin(2 * np.pi * freq * t) * 0.5  # 50% volume
        return AudioSegment(audio.tobytes(), frame_rate=44100, sample_width=2, channels=1)

    silence = lambda ms: AudioSegment.silent(duration=ms)
    audio = AudioSegment.silent(duration=0)

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

    return audio

# Save Audio Function
def save_audio(audio: AudioSegment, filename: str, format: str = "mp3"):
    audio.export(filename, format=format)

# Load Config Function
def load_config(config_file: str) -> dict:
    with open(config_file, 'r') as f:
        return json.load(f)

# Main Function
def main():
    config = load_config("config.json")
    text = input("Enter text to convert: ")
    
    # Set up encoder chain
    chain = EncoderChain()
    chain.add_encoder(MorseEncoder())
    
    # Add encryption if specified
    if config.get("encryption") == "substitution":
        chain.add_encoder(SubstitutionCipher(key="swap"))
    # Add more conditions here for other encryptions, e.g., AES
    
    # Encode the text
    morse = chain.encode(text)
    
    # Generate audio
    audio = generate_morse_audio(morse, config["freq"], config["dot_duration"])
    
    # Save output
    save_audio(audio, "output." + config["output_format"], format=config["output_format"])
    print(f"Audio saved as output.{config['output_format']}")

if __name__ == "__main__":
    main()