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
from colorama import init, Fore, Style
from jarvis_brain import JarvisBrain, Memory 

# CONFIGURAZIONE
SERVER_URL = "ws://127.0.0.1:8000/stream"
VOICE_NAME = "it-Spk1_man" 
SAMPLE_RATE = 24000 
VAD_CONFIDENCE = 0.9 
VOLUME_GATE = 1500 

init(autoreset=True)

# ==========================================
# 🛠️ UTILITY
# ==========================================

def select_microphone():
    """Permette all'utente di selezionare il microfono dall'elenco."""
    mic_list = sr.Microphone.list_microphone_names()
    
    print(f"\n{Fore.CYAN}🎙️ SELEZIONA MICROFONO:{Style.RESET_ALL}")
    
    # Mostra la lista dei microfoni disponibili
    for i, name in enumerate(mic_list):
        print(f"  [{i}] {name}")
    
    # Tenta l'auto-rilevamento come suggerimento predefinito (indice 0 se non trova nulla)
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


print(f"{Fore.CYAN}🎧 [Client] Caricamento Audio e Modelli...{Style.RESET_ALL}")

try:
    vad_model, _ = torch.hub.load(repo_or_dir='snakers4/silero-vad', model='silero_vad', force_reload=False, trust_repo=True)
    whisper = WhisperModel("small", device="cuda" if torch.cuda.is_available() else "cpu", compute_type="int8")
except Exception as e:
    print(f"Errore Modelli: {e}"); sys.exit(1)

def check_interruption(stream):
    try:
        if stream.get_read_available() >= 512:
            data = stream.read(512, exception_on_overflow=False)
            audio_int16 = np.frombuffer(data, np.int16)
            if np.abs(audio_int16).mean() < VOLUME_GATE: return False
            if vad_model(torch.from_numpy(audio_int16.astype(np.float32)/32768.0), 16000).item() > VAD_CONFIDENCE: return True
    except Exception as e: 
        print(f"{Fore.RED}❌ Errore interruzione VAD: {e}{Style.RESET_ALL}")
        pass
    return False

async def speak_stream(text_generator, out_stream, in_stream):
    sentence_buffer = ""
    stop_chars = [".", "!", "?", "\n"] 
    
    for chunk in text_generator:
        chunk = re.sub(r'\{.*?\}', '', chunk)
        sentence_buffer += chunk
        
        is_end = any(sentence_buffer.strip().endswith(s) for s in stop_chars)
        if is_end and len(sentence_buffer) > 5:
            clean = sentence_buffer.strip()
            print(f"{Fore.MAGENTA}🔊 AI: {Style.RESET_ALL}{clean}")
            
            url = f"{SERVER_URL}?{urllib.parse.urlencode({'text': clean, 'voice': VOICE_NAME})}"
            try:
                async with websockets.connect(url) as ws:
                    async for msg in ws:
                        if check_interruption(in_stream):
                            print(f"{Fore.RED}🛑 STOP{Style.RESET_ALL}")
                            out_stream.stop_stream(); out_stream.start_stream() 
                            return True 
                        if isinstance(msg, bytes): out_stream.write(msg)
            except Exception as e:
                print(f"{Fore.RED}❌ Errore TTS WebSocket: {e}{Style.RESET_ALL}")
                pass
            sentence_buffer = "" 
            
    if sentence_buffer.strip():
        clean_final = sentence_buffer.strip()
        print(f"{Fore.MAGENTA}🔊 AI: {Style.RESET_ALL}{clean_final}")
        url = f"{SERVER_URL}?{urllib.parse.urlencode({'text': clean_final, 'voice': VOICE_NAME})}"
        try:
            async with websockets.connect(url) as ws:
                async for msg in ws:
                    if check_interruption(in_stream): return True
                    if isinstance(msg, bytes): out_stream.write(msg)
        except Exception as e:
            print(f"{Fore.RED}❌ Errore TTS WebSocket Finale: {e}{Style.RESET_ALL}")
            pass
    return False

async def main_loop():
    r = sr.Recognizer()
    r.energy_threshold = 300   
    r.pause_threshold = 1.0    
    
    # 🟢 AGGIORNATO: Selezione interattiva del microfono
    mic_idx = select_microphone()
    mic_list = sr.Microphone.list_microphone_names() # Rileggi la lista per il nome corretto
    
    # 🟢 VERIFICA INDICE
    if mic_idx >= len(mic_list) or mic_idx < 0:
        print(f"{Fore.RED}❌ ERRORE: L'indice microfono selezionato ({mic_idx}) non è valido. Riavvia e scegli un indice corretto.{Style.RESET_ALL}")
        sys.exit(1)

    p = pyaudio.PyAudio()
    out_s = p.open(format=pyaudio.paInt16, channels=1, rate=SAMPLE_RATE, output=True)
    in_s = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, input_device_index=mic_idx, frames_per_buffer=512)
    in_s.stop_stream() 

    brain = JarvisBrain() 

    print(f"\n{Fore.GREEN}🚀 JARVIS v51 (SAFE EXIT & MEMORY FIX){Style.RESET_ALL}")
    print(f"{Fore.YELLOW}ℹ️  Premi CTRL+C per uscire (risposta rapida).{Style.RESET_ALL}\n")

    with sr.Microphone(device_index=mic_idx) as source:
        r.adjust_for_ambient_noise(source, duration=1.0) 
        print(f"✅ PARLA! (Mic: {mic_list[mic_idx]})")

        while True:
            try:
                try:
                    if in_s.is_active(): in_s.stop_stream() 
                except Exception as e:
                    if "Stream not open" not in str(e):
                        print(f"{Fore.RED}⚠️ Errore Audio Inatteso (Ignorato): {e}{Style.RESET_ALL}")
                    
                print(f"{Fore.CYAN}\n👂 Ascolto...{Style.RESET_ALL}", end="\r")
                
                try:
                    audio = await asyncio.to_thread(r.listen, source, timeout=2.0, phrase_time_limit=10)
                except sr.WaitTimeoutError:
                    continue 
                
                print(f"{Fore.YELLOW}⚡ Trascrizione...          {Style.RESET_ALL}", end="\r")
                
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    f.write(audio.get_wav_data()); tmp_name = f.name
                
                try:
                    segs, _ = whisper.transcribe(tmp_name, language="it", beam_size=1)
                    user_text = " ".join([s.text for s in segs]).strip()
                except: user_text = ""
                finally: 
                    try: os.remove(tmp_name)
                    except: pass

                if len(user_text) < 2 or "sottotitoli" in user_text.lower(): continue
                
                
                if "dimentica tutto" in user_text.lower() or "tabula rasa" in user_text.lower() or "cancella tutto" in user_text.lower():
                    reset_res = Memory.reset() 
                    print(f"🔧 {reset_res}")
                    
                    await speak_stream(iter(["Ho cancellato tutte le informazioni memorizzate su di te. Ho fatto tabula rasa!"]), out_s, in_s)
                    
                    try:
                        out_s.stop_stream(); out_s.close()
                        in_s.stop_stream(); in_s.close()
                        p.terminate()
                        
                        p = pyaudio.PyAudio()
                        out_s = p.open(format=pyaudio.paInt16, channels=1, rate=SAMPLE_RATE, output=True)
                        in_s = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, input_device_index=mic_idx, frames_per_buffer=512)
                        in_s.stop_stream() 
                        print(f"{Fore.YELLOW}✅ Audio resettato senza riavvio del processo.{Style.RESET_ALL}")
                        
                    except Exception as audio_e:
                        print(f"{Fore.RED}❌ FALLIMENTO RESET AUDIO: {audio_e}{Style.RESET_ALL}")
                        print(f"{Fore.RED}🛑 Eseguo riavvio completo del processo Python per stabilità.{Style.RESET_ALL}")
                        os.execv(sys.executable, ['python'] + sys.argv)
                        
                    continue 

                print(f"👤 TU: {user_text}")

                in_s.start_stream() 
                
                try:
                    generator = brain.think(user_text)
                    if await speak_stream(generator, out_s, in_s):
                        print(f"{Fore.CYAN}⚡ Restart...{Style.RESET_ALL}")
                except GeneratorExit: pass 
                except Exception as e: 
                    print(f"Err Brain: {e}")

            except KeyboardInterrupt:
                print(f"\n{Fore.RED}🛑 Uscita in corso...{Style.RESET_ALL}")
                break 
            except Exception as e: 
                print(f"⚠️ Loop Error (FATAL): {e}")

    out_s.stop_stream(); out_s.close()
    in_s.stop_stream(); in_s.close()
    p.terminate()
    print("✅ Bye.")

if __name__ == "__main__":
    try: asyncio.run(main_loop())
    except KeyboardInterrupt: pass