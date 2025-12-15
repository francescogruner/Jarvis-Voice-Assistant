🇮🇹 JARVIS ASSISTANT: Real-Time AI Voice Assistant (IT/EN)

🌐 MULTI-VERSION | MULTI-MODEL | REAL-TIME TTS

Jarvis è un assistente vocale italiano ad alte prestazioni, progettato per il controllo locale e l'elaborazione vocale in tempo reale. Offre una scelta unica: la potenza del cloud con Google Gemini o la privacy del locale con Ollama, il tutto accoppiato a una sintesi vocale (TTS) rapidissima grazie a VibeVoice.



🇮🇹 ITALIANO (Italian Guide)

🌟 Punti Chiave

Lingua Primaria: Interamente configurato per la lingua italiana (ASR, TTS e LLM).



Architettura Ibrida: Scegli tra l'efficienza del Cloud Gemini o l'uso locale di Ollama.



Real-Time Voice: Utilizza VibeVoice per un TTS velocissimo e Faster-Whisper per il riconoscimento vocale (ASR).



Strumenti: Gestione memoria, calcoli, orologio, e, a seconda della versione, integrazione con Google Search.



⚙️ Architettura del Sistema

Jarvis è un sistema a tre componenti che devono essere attivi contemporaneamente per funzionare:



Server LLM/Brain: L'intelligenza (Gemini Cloud o Ollama Locale).



Server TTS (VibeVoice): Il server vocale locale sulla porta 8000 (richiede GPU).



Jarvis Client: L'applicazione Python che gestisce microfono, ASR, e riproduzione audio.



📦 Prerequisiti

Python 3.10+ installato e nel PATH.



Git installato.



GPU NVIDIA con driver aggiornati (Raccomandata la serie RTX 30/40, testato su GTX 3050T).



(Solo per Versione Ollama): Ollama installato e un modello base (es. llama3) scaricato (ollama pull llama3).



▶️ Istruzioni per l'Installazione Guidata

L'installazione è centralizzata in un unico script.



Clona la Repository o scarica lo ZIP e apri il terminale nella cartella principale (/Jarvis\_Root/).



Avvia il Setup: Esegui lo script:



Bash



python setup\_jarvis.py

Seleziona la Versione: Lo script ti chiederà se vuoi installare la versione Gemini o Ollama.



Segui i Passaggi: Lo script guiderà l'utente attraverso l'installazione delle dipendenze, la configurazione delle chiavi API (necessarie per Gemini, opzionali per Ollama) e l'installazione automatica di VibeVoice.



🚀 Istruzioni per l'Avvio (Post-Setup)

Al termine del setup, devi lanciare i server nell'ordine corretto:



(Solo Ollama) Avvia il Server LLM:



Bash



ollama serve

Avvia il Server TTS (VibeVoice) in un NUOVO Terminale:



Bash



python VibeVoice/demo/vibevoice\_realtime\_demo.py --model\_path microsoft/VibeVoice-Realtime-0.5B --port 8000

Avvia Jarvis Client in un NUOVO Terminale:



Bash



python jarvis\_client.py

🇬🇧 ENGLISH (English Guide)

🌟 Key Features

Primary Language: Fully configured for the Italian language (ASR, TTS, and LLM).



Hybrid Architecture: Choose between the efficiency of the Gemini Cloud or the privacy of local Ollama.



Real-Time Voice: Utilizes VibeVoice for ultra-fast TTS and Faster-Whisper for Speech Recognition (ASR).



Tools: Memory management, calculations, clock, and, depending on the version, Google Search integration.



⚙️ System Architecture

Jarvis is a three-component system that must run concurrently:



LLM/Brain Server: (Gemini Cloud or Local Ollama) — The intelligence.



TTS Server (VibeVoice): (Local, port 8000) — Generates voice in real-time (requires GPU).



Jarvis Client: (Local) — Manages microphone, ASR, requests, and audio playback.



📦 Prerequisites

Python 3.10+ installed and in your PATH.



Git installed.



NVIDIA GPU with up-to-date drivers (RTX 30/40 series recommended, tested successfully on GTX 3050T).



(Ollama Version Only): Ollama installed and a base model (e.g., llama3) downloaded (ollama pull llama3).



▶️ Guided Installation Instructions

The installation process is centralized in a single script.



Clone the Repository or download the ZIP, and open your terminal in the main folder (/Jarvis\_Root/).



Start Setup: Run the script:



Bash



python setup\_jarvis.py

Select Version: The script will ask you whether you want to install the Gemini or Ollama version.



Follow Steps: The script guides the user through installing dependencies, configuring API keys (required for Gemini, optional for Ollama), and automatically setting up VibeVoice.



🚀 Startup Instructions (Post-Setup)

Upon completion of the setup, your system is ready to launch. You will need two separate terminals running for operation:



(Ollama Only) Start the LLM Server:



Bash



ollama serve

Start the TTS Server (VibeVoice) in a NEW Terminal:



Bash



python VibeVoice/demo/vibevoice\_realtime\_demo.py --model\_path microsoft/VibeVoice-Realtime-0.5B --port 8000

Start the Jarvis Client in a NEW Terminal:



Bash



python jarvis\_client.py

❓ Support

If you encounter issues or have questions about the project, feel free to reach out to the project creator, Francesco Gruner, on LinkedIn:



https://www.linkedin.com/in/francescogruner/

