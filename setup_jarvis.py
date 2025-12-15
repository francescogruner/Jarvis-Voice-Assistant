import os
import sys
import subprocess
import shutil # Necessario per copiare i file
from colorama import Fore, Style, init

init(autoreset=True)

# ====================================================================
# 1. VARIABILI E CONFIGURAZIONE
# ====================================================================

# Dipendenze (uguali per entrambe le versioni)
REQUIREMENTS_CONTENT = """
google-genai
python-dotenv
chromadb
requests
pyaudio
SpeechRecognition
faster-whisper
numpy
torch
colorama
sentence-transformers
"""

VIBEVOICE_DIR = "VibeVoice"
VIBEVOICE_REPO_URL = "https://github.com/microsoft/VibeVoice.git"
VERSIONS_PATH = "Versions" # Cartella che contiene Gemini e Ollama

# ====================================================================
# 2. FUNZIONI DI BASE E UTILITY
# ====================================================================

def run_command(command, error_message):
    """Esegue un comando e verifica se ci sono errori."""
    try:
        subprocess.check_call(command, shell=True)
    except subprocess.CalledProcessError:
        print(f"{Fore.RED}❌ ERRORE: {error_message}{Style.RESET_ALL}")
        return False
    return True

def get_user_input(prompt, link=None, sensitive=False):
    """Chiede input all'utente, con link informativo."""
    
    full_prompt = f"{Fore.YELLOW}🔑 {prompt}:{Style.RESET_ALL} "
    if link:
        print(f"{Fore.BLUE}ℹ️ Ottieni la risorsa qui: {link}{Style.RESET_ALL}")
        
    if sensitive:
        import getpass
        return getpass.getpass(full_prompt).strip()
    return input(full_prompt).strip()

def wait_for_confirmation(step_name):
    """Blocca l'esecuzione e attende la conferma dell'utente."""
    input(f"\n{Fore.CYAN}--- Premi INVIO per iniziare il passo: {step_name} ---{Style.RESET_ALL}")

def check_git_installed():
    """Verifica se Git è presente nel sistema."""
    try:
        subprocess.check_output("git --version", shell=True)
        return True
    except:
        return False

# ====================================================================
# 3. LOGICA DI SETUP DELLE VERSIONI
# ====================================================================

def select_and_copy_version():
    """Mostra un menu e copia i file della versione scelta nella root."""
    print(f"\n{Fore.CYAN}--- SELEZIONE VERSIONE JARVIS ---{Style.RESET_ALL}")
    print(f"{Fore.GREEN}[1] Versione GEMINI (Richiede GEMINI API Key)")
    print(f"{Fore.GREEN}[2] Versione OLLAMA (LLM Locale, Richiede 'ollama serve')")
    
    version = input(f"\n{Fore.YELLOW}Scegli il numero [1/2]: {Style.RESET_ALL}").strip()
    
    if version == '1':
        source_dir = os.path.join(VERSIONS_PATH, "Gemini")
        brain_source = "jarvis_brain.py"
        client_source = "jarvis_client.py"
        mode = "GEMINI"
    elif version == '2':
        source_dir = os.path.join(VERSIONS_PATH, "Ollama")
        brain_source = "jarvis_brain_ollama.py"
        client_source = "jarvis_client_ollama.py"
        mode = "OLLAMA"
    else:
        print(f"{Fore.RED}Selezione non valida. Annullamento setup.{Style.RESET_ALL}")
        sys.exit(1)
        
    # Nomi destinazione standardizzati
    DEST_BRAIN = "jarvis_brain.py"
    DEST_CLIENT = "jarvis_client.py"

    # Verifica che i file esistano nella cartella di origine
    if not (os.path.exists(os.path.join(source_dir, brain_source)) and os.path.exists(os.path.join(source_dir, client_source))):
        print(f"{Fore.RED}❌ ERRORE: Impossibile trovare i file in {source_dir}. Controlla la struttura delle cartelle 'Versions/...'!{Style.RESET_ALL}")
        sys.exit(1)

    # Copia i file nella root (rinominandoli per l'uso standard)
    try:
        shutil.copy(os.path.join(source_dir, brain_source), DEST_BRAIN)
        shutil.copy(os.path.join(source_dir, client_source), DEST_CLIENT)
        print(f"{Fore.GREEN}✅ Versione '{mode}' copiata e standardizzata come '{DEST_BRAIN}' e '{DEST_CLIENT}'.{Style.RESET_ALL}")
        return mode
    except Exception as e:
        print(f"{Fore.RED}❌ ERRORE durante la copia dei file: {e}{Style.RESET_ALL}")
        sys.exit(1)

# ====================================================================
# 4. FUNZIONE PRINCIPALE DI SETUP
# ====================================================================

def main_setup():
    
    print(f"{Fore.GREEN}====================================================={Style.RESET_ALL}")
    print(f"{Fore.GREEN}🚀 JARVIS ASSISTANT - SETUP WIZARD (Multi-Version){Style.RESET_ALL}")
    print(f"{Fore.GREEN}====================================================={Style.RESET_ALL}")
    
    # --- 0. SELEZIONE E COPIA FILE ---
    if not os.path.exists(VERSIONS_PATH):
        print(f"{Fore.RED}❌ ERRORE: Cartella '{VERSIONS_PATH}' non trovata. Controlla il pacchetto ZIP!{Style.RESET_ALL}")
        sys.exit(1)
        
    MODE = select_and_copy_version()
    
    # --- VERIFICA PREREQUISITI ---
    if not check_git_installed():
        print(f"{Fore.RED}❌ REQUISITO MANCANTE: Git non è installato o non è nel PATH.{Style.RESET_ALL}")
        print(f"{Fore.RED}VibeVoice richiede Git per il download. Installa Git e riavvia lo script.{Style.RESET_ALL}")
        sys.exit(1)
    else:
        print(f"{Fore.GREEN}✅ Git rilevato. Possiamo procedere.{Style.RESET_ALL}")
    
    # --- PASSO 1: Installazione Dipendenze Python ---
    wait_for_confirmation("1. Installazione Dipendenze Python")
    print(f"{Fore.CYAN}Esecuzione: pip install...{Style.RESET_ALL}")
    try:
        with open("requirements.txt", "w") as f:
            f.write(REQUIREMENTS_CONTENT)
        if run_command("pip install -r requirements.txt", "Impossibile installare le dipendenze."):
            print(f"{Fore.GREEN}✅ Dipendenze Jarvis installate con successo.{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ Errore critico: {e}{Style.RESET_ALL}")
        sys.exit(1)

    # --- PASSO 2: Configurazione Chiavi e .env ---
    wait_for_confirmation("2. Configurazione Chiavi API e .env")
    
    gemini_key = ""
    if MODE == "GEMINI":
        print(f"{Fore.CYAN}Richiesta delle chiavi per la versione GEMINI/WEB (tutte necessarie):{Style.RESET_ALL}")
        gemini_key = get_user_input("GEMINI_API_KEY", link="https://ai.google.dev/gemini-api/docs/api-key", sensitive=True)
        google_key = get_user_input("GOOGLE_SEARCH_API_KEY", link="https://developers.google.com/custom-search/v1/overview", sensitive=True)
        google_cx = get_user_input("GOOGLE_SEARCH_CX (ID Motore di Ricerca)", link="https://programmablesearchengine.google.com/controlpanel/create")
    else: # OLLAMA
        print(f"{Fore.CYAN}Richiesta delle chiavi per la versione OLLAMA. Ricerca Web OPZIONALE:{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Lascia i campi Google vuoti per una configurazione solo locale.{Style.RESET_ALL}")
        gemini_key = "NOT_USED_IN_OLLAMA_MODE" 
        google_key = get_user_input("GOOGLE_SEARCH_API_KEY (OPZIONALE)", link="https://developers.google.com/custom-search/v1/overview", sensitive=True)
        google_cx = get_user_input("GOOGLE_SEARCH_CX (ID Motore di Ricerca - OPZIONALE)", link="https://programmablesearchengine.google.com/controlpanel/create")
    
    # Creazione .env
    env_content = f"""
# Configurazione per la versione {MODE}
GEMINI_API_KEY={gemini_key} 

# Chiavi per la ricerca web stabile di Google
GOOGLE_SEARCH_API_KEY={google_key}
GOOGLE_SEARCH_CX={google_cx}
"""
    try:
        with open(".env", "w") as f:
            f.write(env_content)
        print(f"{Fore.GREEN}✅ File .env creato con successo.{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ Errore nella creazione del file .env: {e}{Style.RESET_ALL}")
        sys.exit(1)
        
    # --- PASSO 3: Download VibeVoice (TTS) ---
    wait_for_confirmation("3. Download del Codice VibeVoice (TTS)")
    
    if os.path.exists(VIBEVOICE_DIR):
        print(f"{Fore.YELLOW}⚠️ Cartella {VIBEVOICE_DIR} già esistente. Salto il download Git.{Style.RESET_ALL}")
    else:
        print(f"Esecuzione: git clone {VIBEVOICE_REPO_URL}...")
        if run_command(f"git clone {VIBEVOICE_REPO_URL} {VIBEVOICE_DIR}", "Impossibile clonare VibeVoice."):
            print(f"{Fore.GREEN}✅ Repository VibeVoice scaricato in {VIBEVOICE_DIR}.{Style.RESET_ALL}")
             
    
    # --- PASSO 4: Automazione e Istruzioni Finali (Avvio) ---
    wait_for_confirmation("4. Automazione VibeVoice e Istruzioni Finali")
    
    print(f"\n{Fore.GREEN}====================================================={Style.RESET_ALL}")
    print(f"{Fore.GREEN}🎉 JARVIS SETUP COMPLETATO!{Style.RESET_ALL}")
    print(f"{Fore.GREEN}====================================================={Style.RESET_ALL}")
    
    # --- ISTRUZIONI AGGIUNTIVE PER OLLAMA ---
    if MODE == "OLLAMA":
        print(f"\n{Fore.YELLOW}*** PREPARAZIONE OLLAMA ***{Style.RESET_ALL}")
        print(f"1. {Fore.CYAN}SERVER OLLAMA (LLM):{Style.RESET_ALL}")
        print(f"   Prima di avviare Jarvis, devi lanciare il server Ollama in un terminale separato:")
        print(f"   {Fore.WHITE}ollama serve{Style.RESET_ALL}")
        print(f"   (Se non lo hai già fatto, scarica un modello: {Fore.WHITE}ollama pull llama3{Style.RESET_ALL})")
    
    # --- AUTOMAZIONE INSTALLAZIONE DIPENDENZE VIBEVOICE ---
    print(f"\n{Fore.YELLOW}PASSO A: INSTALLAZIONE AUTOMATICA DIPENDENZE VIBEVOICE{Style.RESET_ALL}")
    print(f"Esecuzione: pip install per VibeVoice... (Potrebbe richiedere qualche minuto){Style.RESET_ALL}")
    
    try:
        install_command = f"cd {VIBEVOICE_DIR} && pip install -e . && cd .."
        if run_command(install_command, "Impossibile installare le dipendenze VibeVoice. Controlla il tuo ambiente CUDA/GPU."):
            print(f"{Fore.GREEN}✅ Dipendenze VibeVoice installate con successo.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ Installazione VibeVoice fallita. Procedi manualmente al lancio del server.{Style.RESET_ALL}")
            
    except Exception as e:
        print(f"{Fore.RED}❌ Errore durante l'installazione di VibeVoice: {e}{Style.RESET_ALL}")


    # --- ISTRUZIONI AVVIO SERVER (Bloccante) ---
    print(f"\n{Fore.YELLOW}PASSO B: AVVIA IL SERVER TTS (in un NUOVO Terminale){Style.RESET_ALL}")
    print(f"Il server VibeVoice è stato testato e funziona anche su GPU come la GTX 3050T.")
    
    server_command = f"python {VIBEVOICE_DIR}/demo/vibevoice_realtime_demo.py --model_path microsoft/VibeVoice-Realtime-0.5B --port 8000"
    
    print(f"\n{Fore.RED}⚠️ ATTENZIONE: Apri una NUOVA finestra PowerShell o Terminale e incolla il comando qui sotto. Questo terminale deve restare APERTO:{Style.RESET_ALL}")
    print(f"   {Fore.WHITE}{server_command}{Style.RESET_ALL}")
    
    # --- ISTRUZIONI AVVIO CLIENT JARVIS ---
    print(f"\n{Fore.YELLOW}PASSO C: AVVIA JARVIS CLIENT (ASR + LLM){Style.RESET_ALL}")
    print(f"1. Chiudi il terminale di setup attuale (questo terminale).")
    print(f"2. {Fore.CYAN}Apri un SECONDO terminale{Style.RESET_ALL} (dopo aver lanciato il server TTS e, se Ollama, il server Ollama).")
    print(f"3. {Fore.CYAN}Esegui Jarvis:{Style.RESET_ALL}")
    print(f"   {Fore.WHITE}python jarvis_client.py{Style.RESET_ALL}")

    # --- LINK DI SUPPORTO ---
    print(f"\n{Fore.CYAN}--- Hai bisogno di supporto? ---{Style.RESET_ALL}")
    print(f"Per assistenza tecnica o domande sul progetto, scrivi a Francesco Gruner su LinkedIn:")
    print(f"{Fore.MAGENTA}https://www.linkedin.com/in/francescogruner/{Style.RESET_ALL}")

    print(f"\n{Fore.RED}Premere INVIO per chiudere lo script di Setup.{Style.RESET_ALL}")
    input()


if __name__ == "__main__":
    main_setup()