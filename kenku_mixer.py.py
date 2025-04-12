import sounddevice as sd
import numpy as np
import simpleaudio as sa
import keyboard
import os
import soundfile as sf
import threading
import time
import tkinter as tk
from tkinter import ttk

# ====== CONFIG ======
USE_GUI = True
SAMPLE_RATE = 44100
CHANNELS = 1
VOICE_DIR = "kenku_sounds"
MIXED_OUTPUT = "mixed_output.wav"

recorded_data = None
crow_volume = 0.5
npc_volume = 0.5

sound_bindings = {
    'numpad1': os.path.join(VOICE_DIR, 'kenku_call1.wav'),
    'numpad2': os.path.join(VOICE_DIR, 'kenku_call2.wav'),
    'numpad3': os.path.join(VOICE_DIR, 'kenku_call3.wav'),
}

# ====== SOUND LOADING ======
def load_crow_caws():
    """Loads all crow caws for mixing"""
    if not os.path.exists(VOICE_DIR):
        os.makedirs(VOICE_DIR)
    return [os.path.join(VOICE_DIR, f) for f in os.listdir(VOICE_DIR) if f.endswith(".wav")]

# ====== SOUND PLAYBACK ======
def play_sound(file_path):
    if os.path.exists(file_path):
        data, fs = sf.read(file_path, dtype='float32')
        sa.play_buffer((data * 32767).astype(np.int16), CHANNELS, 2, fs)
    else:
        print(f"Sound file not found: {file_path}")

def play_mapped_sound(key):
    if key in sound_bindings:
        play_sound(sound_bindings[key])
    else:
        print(f"No sound mapped to key: {key}")

# ====== RECORD + MIX ======
def record_and_mix(duration=5):
    global recorded_data
    print("Recording...")
    npc_audio = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=CHANNELS)
    sd.wait()
    print("Recording finished.")

    crow_caws = load_crow_caws()
    if not crow_caws:
        print("No crow caws found in VOICE_DIR.")
        return

    crow_file = random.choice(crow_caws)
    crow_data, crow_fs = sf.read(crow_file, dtype='float32')

    if crow_fs != SAMPLE_RATE:
        print("Sample rate mismatch. Please convert all WAV files to 44100 Hz.")
        return

    npc_len = npc_audio.shape[0]
    crow_len = crow_data.shape[0]

    if crow_len < npc_len:
        repeat_factor = int(np.ceil(npc_len / crow_len))
        crow_data = np.tile(crow_data, repeat_factor)[:npc_len]
    else:
        crow_data = crow_data[:npc_len]

    # Apply volume mix
    mixed = (npc_volume * npc_audio[:, 0]) + (crow_volume * crow_data)
    mixed = np.clip(mixed, -1.0, 1.0)  # Avoid clipping

    recorded_data = mixed.reshape(-1, 1)

    # Save to file
    sf.write(MIXED_OUTPUT, recorded_data, SAMPLE_RATE)
    print(f"Mixed audio saved to {MIXED_OUTPUT}")

    print("Playing mixed audio...")
    sa.play_buffer((mixed * 32767).astype(np.int16), CHANNELS, 2, SAMPLE_RATE)

def replay_audio():
    if recorded_data is not None:
        print("Replaying last mixed audio...")
        sa.play_buffer((recorded_data.flatten() * 32767).astype(np.int16), CHANNELS, 2, SAMPLE_RATE)
    else:
        print("No mixed audio recorded yet.")

# ====== KEYBOARD BINDINGS ======
def keyboard_loop():
    while True:
        for key in sound_bindings:
            if keyboard.is_pressed(key):
                play_mapped_sound(key)
                time.sleep(0.3)
        if keyboard.is_pressed("numpad0"):  # Record + mix
            record_and_mix(duration=5)
            time.sleep(0.3)
        if keyboard.is_pressed("numpad9"):  # Replay
            replay_audio()
            time.sleep(0.3)

# ====== GUI ======
def create_gui():
    def set_crow_volume(val):
        global crow_volume
        crow_volume = float(val)

    def set_npc_volume(val):
        global npc_volume
        npc_volume = float(val)

    root = tk.Tk()
    root.title("Kenku Soundboard")

    tk.Label(root, text="Kenku Soundboard").pack(pady=5)

    for key, path in sound_bindings.items():
        label = f"{key.upper()}: {os.path.basename(path)}"
        tk.Button(root, text=label, command=lambda p=path: play_sound(p)).pack(pady=2)

    tk.Button(root, text="Record + Mix (Numpad 0)", command=lambda: record_and_mix(duration=5)).pack(pady=5)
    tk.Button(root, text="Replay Mixed Audio (Numpad 9)", command=replay_audio).pack(pady=5)

    # Volume sliders
    tk.Label(root, text="Crow Volume").pack()
    crow_slider = ttk.Scale(root, from_=0.0, to=1.0, value=crow_volume, command=set_crow_volume)
    crow_slider.pack(pady=2)

    tk.Label(root, text="NPC Volume").pack()
    npc_slider = ttk.Scale(root, from_=0.0, to=1.0, value=npc_volume, command=set_npc_volume)
    npc_slider.pack(pady=2)

    root.protocol("WM_DELETE_WINDOW", root.quit)
    root.mainloop()

# ====== MAIN ======
def main():
    load_crow_caws()
    threading.Thread(target=keyboard_loop, daemon=True).start()
    if USE_GUI:
        create_gui()

if __name__ == '__main__':
    main()