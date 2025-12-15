import asyncio
import websockets
import urllib.parse
import speech_recognition as sr
from faster_whisper import WhisperModel
import pyaudio
import os
import sys
import tempfile
import torch
import numpy as np
import re
import requests
from colorama import init, Fore, Style

# IMPORTIAMO IL CERVELLO AGGIORNATO
from jarvis_brain_ollama import JarvisBrain, Memory

# CONFIGURAZIONE AUDIO
SERVER_URL = "ws://127.0.0.1:8000/stream"
VOICE_NAME = "it-Spk1_man" 
SAMPLE_RATE = 24000 
VAD_CONFIDENCE = 0.9 
VOLUME_GATE = 3000 

init(autoreset=True)

# ==========================================
# 🛠️ UTILITY
# ==========================================
def select_ollama_model():
    """Permette all'utente di selezionare un modello Ollama attivo."""
    print(f"{Fore.CYAN}--- Verifica Modelli Ollama in corso su localhost:11434...{Style.RESET_ALL}")
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=3)
        resp.raise_for_status()
        models = [m['name'] for m in resp.json().get('models', [])]
        
        if not models:
            print(f"{Fore.RED}⚠️ Nessun modello Ollama trovato. Sarà usato 'llama3.2:1b' come fallback (devi installarlo manualmente).{Style.RESET_ALL}")
            return "llama3.2:1b"
            
        print(f"\n{Fore.CYAN}🧠 Modelli Ollama trovati. Seleziona il modello da usare (Ollama deve restare attivo):{Style.RESET_ALL}")
        for i, m in enumerate(models): 
            print(f"  [{i}] {m}")
            
        while True:
            sel = input(f"\nNumero o Invio (default: {models[0]}): ").strip()
            if not sel: return models[0]
            if sel.isdigit() and int(sel) < len(models): return models[int(sel)]
            print(f"{Fore.RED}Selezione non valida. Riprova.{Style.RESET_ALL}")
            
    except requests.exceptions.ConnectionError:
        print(f"{Fore.RED}❌ ERRORE: Ollama non è in esecuzione su http://localhost:11434. Avvia 'ollama serve' in un terminale separato.{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"{Fore.RED}❌ Errore Ollama: {e}{Style.RESET_ALL}")
        sys.exit(1)

def select_microphone():
    """Permette all'utente di selezionare il microfono dall'elenco."""
    mic_list = sr.Microphone.list_microphone_names()
    
    print(f"\n{Fore.CYAN}🎙️ SELEZIONA MICROFONO:{Style.RESET_ALL}")
    
    # Mostra la lista dei microfoni disponibili
    for i, name in enumerate(mic_list):
        print(f"  [{i}] {name}")
    
    # Tenta l'auto-rilevamento come suggerimento predefinito
    auto_idx = next((i for i, m in enumerate(mic_list) if "Fifine" in m or "USB" in m), 0)
    
    while True:
        try:
            prompt = f"Inserisci l'indice del microfono da usare (default: {auto_idx}): "
            sel = input(prompt).strip()
            
            if not sel: # Se l'utente preme Invio, usa il default (auto_idx)
                return auto_idx
            
            idx = int(sel)
            if 0 <= idx < len(mic_list):
                return idx
            else:
                print(f"{Fore.RED}Indice non valido. Scegli un numero tra 0 e {len(mic_list) - 1}.{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}Input non valido. Inserisci un numero.{Style.RESET_ALL}")


# SETUP AI AUDIO
print(f"{Fore.CYAN}🎧 [Client] Caricamento Audio e Modelli...{Style.RESET_ALL}")
try:
    vad_model, _ = torch.hub.load(repo_or_dir='snakers4/silero-vad', model='silero_vad', force_reload=False, trust_repo=True)
    whisper = WhisperModel("small", device="cuda" if torch.cuda.is_available() else "cpu", compute_type="int8")
except Exception as e: 
    print(f"{Fore.RED}❌ Errore Whisper/VAD: {e}{Style.RESET_ALL}")
    sys.exit(1)

def check_interruption(stream):
    # La logica di interruzione rimane la stessa (VAD)
    try:
        if stream.get_read_available() >= 512:
            data = stream.read(512, exception_on_overflow=False)
            audio_int16 = np.frombuffer(data, np.int16)
            if np.abs(audio_int16).mean() < VOLUME_GATE: return False
            if vad_model(torch.from_numpy(audio_int16.astype(np.float32)/32768.0), 16000).item() > VAD_CONFIDENCE: return True
    except: pass
    return False

async def speak_stream(text_generator, out_stream, in_stream):
    # La logica di TTS stream (VibeVoice) rimane la stessa
    sentence_buffer = ""
    stop_chars = [".", "!", "?", "\n"] 
    SERVER_URL = "ws://127.0.0.1:8000/stream" # Per chiarezza

    for chunk in text_generator:
        chunk = re.sub(r'\{.*?\}', '', chunk)
        chunk = re.sub(r'<.*?>', '', chunk)
        sentence_buffer += chunk
        
        is_end = any(sentence_buffer.strip().endswith(s) for s in stop_chars)
        is_long_enough = len(sentence_buffer) > 5
        is_not_mid_number = not sentence_buffer.strip().endswith(":")
        
        if is_end and is_long_enough and is_not_mid_number:
            clean_sent = sentence_buffer.strip()
            print(f"{Fore.MAGENTA}🔊 AI: {Style.RESET_ALL}{clean_sent}")
            
            url = f"{SERVER_URL}?{urllib.parse.urlencode({'text': clean_sent, 'voice': VOICE_NAME})}"
            try:
                async with websockets.connect(url, ping_timeout=10) as ws:
                    async for msg in ws:
                        if check_interruption(in_stream):
                            print(f"{Fore.RED}🛑 STOP{Style.RESET_ALL}")
                            out_stream.stop_stream(); out_stream.start_stream()
                            return True 
                        if isinstance(msg, bytes): out_stream.write(msg)
            except Exception as e: 
                print(f"{Fore.RED}❌ Errore TTS WebSocket: VibeVoice Down? {e}{Style.RESET_ALL}")
                pass
            sentence_buffer = "" 
            
    if sentence_buffer.strip():
        print(f"{Fore.MAGENTA}🔊 AI: {Style.RESET_ALL}{sentence_buffer.strip()}")
        url = f"{SERVER_URL}?{urllib.parse.urlencode({'text': sentence_buffer.strip(), 'voice': VOICE_NAME})}"
        try:
            async with websockets.connect(url, ping_timeout=10) as ws:
                async for msg in ws:
                    if isinstance(msg, bytes): out_stream.write(msg)
        except: pass
    
    return False

async def main_loop():
    # 1. SELEZIONE MODELLO OLLAMA
    model_name = select_ollama_model()
    
    # 2. CONFIGURAZIONE AUDIO
    r = sr.Recognizer()
    r.energy_threshold = 300   
    r.pause_threshold = 1.2    # Paziente!
    r.dynamic_energy_threshold = False
    
    # 🟢 AGGIORNATO: Selezione interattiva del microfono
    mic_idx = select_microphone()
    
    mic_list = sr.Microphone.list_microphone_names() # Rileggi la lista per mostrare il nome corretto
    
    p = pyaudio.PyAudio()
    out_s = p.open(format=pyaudio.paInt16, channels=1, rate=SAMPLE_RATE, output=True)
    
    # Controlla se l'indice è valido prima di aprirlo
    if mic_idx >= len(mic_list):
        print(f"{Fore.RED}❌ ERRORE: L'indice microfono selezionato ({mic_idx}) non è valido. Riavvia e scegli un indice corretto.{Style.RESET_ALL}")
        sys.exit(1)
        
    in_s = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, input_device_index=mic_idx, frames_per_buffer=512)
    in_s.stop_stream()

    # 3. AVVIO BRAIN
    brain = JarvisBrain(model=model_name)

    print(f"\n{Fore.GREEN}🚀 JARVIS v30 (Ollama + VibeVoice){Style.RESET_ALL}")
    print(f"Modello LLM: {model_name}{Style.RESET_ALL}")

    with sr.Microphone(device_index=mic_idx) as source:
        print("🤫 Calibrazione (2 sec)...")
        r.adjust_for_ambient_noise(source, duration=2.0) 
        print(f"✅ PARLA ORA! (Mic: {mic_list[mic_idx]})") # Mostra il nome corretto

        while True:
            try:
                # 🟢 FERMA STREAM AUDIO IN USCITA PER ASCOLTARE (Fix)
                if in_s.is_active(): in_s.stop_stream()
                print(f"{Fore.CYAN}\n👂 Ascolto...{Style.RESET_ALL}", end="\r")
                
                audio = await asyncio.to_thread(r.listen, source, timeout=None, phrase_time_limit=None)
                
                print(f"{Fore.YELLOW}⚡ Trascrizione...{Style.RESET_ALL}", end="\r")
                
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    f.write(audio.get_wav_data()); tmp_name = f.name
                
                segs, _ = whisper.transcribe(tmp_name, language="it", beam_size=1)
                user_text = " ".join([s.text for s in segs]).strip()
                os.remove(tmp_name)

                if len(user_text) < 2: continue
                
                # Intercettazione comandi memoria
                if "tabula rasa" in user_text.lower(): print(f"🔧 {Memory.reset()}"); continue
                if "dimentica che" in user_text.lower(): 
                    print(f"🔧 {Memory.forget(user_text.split('che',1)[1])}"); 
                    continue
                
                print(f"👤 TU: {user_text}")

                # 🟢 AVVIA STREAM AUDIO IN INGRESSO (Per Barge-in)
                in_s.start_stream()
                
                try:
                    generator = brain.think(user_text)
                    if await speak_stream(generator, out_s, in_s):
                        pass
                except Exception as e: print(f"{Fore.RED}Err Brain: {e}{Style.RESET_ALL}")

            except Exception as e: print(f"⚠️ Loop: {e}")

    out_s.close(); in_s.close(); p.terminate()

if __name__ == "__main__":
    try: 
        print(f"{Fore.YELLOW}--- Avvia Ollama (ollama serve) in un terminale separato PRIMA di procedere ---{Style.RESET_ALL}")
        asyncio.run(main_loop())
    except KeyboardInterrupt: print("\n👋 Bye!")