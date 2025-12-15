# 🚀 JARVIS ASSISTANT: Real-Time AI Voice Assistant (IT/EN)

<p align="center">
  <img src="https://img.shields.io/badge/Status-Active-brightgreen" alt="Project Status"/>
  <img src="https://img.shields.io/badge/Language-Italian-blue" alt="Primary Language: Italian"/>
  <img src="https://img.shields.io/github/license/francescogruner/Jarvis-Voice-Assistant" alt="License"/>
  <img src="https://img.shields.io/github/forks/francescogruner/Jarvis-Voice-Assistant?style=social" alt="GitHub forks"/>
</p>

## 🌐 MULTI-VERSION | MULTI-MODEL | REAL-TIME TTS

> Jarvis è l'assistente vocale italiano ad alte prestazioni definitivo. Progettato per il controllo locale e l'elaborazione vocale in tempo reale, offre una scelta unica: la potenza del cloud con **Google Gemini** o la privacy del locale con **Ollama**. Tutto questo con una sintesi vocale ultra-rapida grazie a VibeVoice.

<p align="center">
  <img src="https://img.shields.io/badge/TTS-VibeVoice-purple" alt="TTS Technology"/>
  <img src="https://img.shields.io/badge/ASR-FasterWhisper-yellowgreen" alt="ASR Technology"/>
  <img src="https://img.shields.io/badge/Cloud-Gemini-red" alt="Cloud LLM"/>
  <img src="https://img.shields.io/badge/Local-Ollama-000080?logo=ollama&logoColor=white" alt="Local LLM"/>
</p>

---

## 🇮🇹 GUIDA IN ITALIANO (Italian Guide)

### 🌟 Punti di Forza

| Caratteristica | Descrizione |
| :--- | :--- |
| **Doppia IA** | Scegli tra **Gemini** (per bassa potenza locale) o **Ollama** (per privacy e controllo totale). |
| **Tempo Reale** | ASR (Faster-Whisper) e TTS (VibeVoice) garantiscono un tempo di risposta vocale minimo. |
| **Memoria** | Utilizza **ChromaDB** per la memoria contestuale e a lungo termine. |
| **Microfono** | Selezione interattiva del microfono al primo avvio per la massima compatibilità hardware. |

### ⚙️ Architettura del Sistema

Jarvis è un sistema a **tre componenti** che devono essere attivi contemporaneamente:

1.  **Server LLM/Brain:** L'intelligenza (Gemini Cloud o Ollama Locale).
2.  **Server TTS (VibeVoice):** Il server vocale locale sulla porta `8000` (richiede GPU).
3.  **Jarvis Client:** L'applicazione Python che gestisce microfono, ASR, e riproduzione audio.

### 📦 Prerequisiti

* **Python 3.10+** installato e nel PATH.
* **Git** installato.
* **GPU NVIDIA** con driver aggiornati (Raccomandata la serie RTX 30/40).
* **(Solo per Versione Ollama):** Ollama installato e un modello base (es. `llama3`) scaricato (`ollama pull llama3`).

### ▶️ Istruzioni per l'Installazione Guidata

L'installazione è centralizzata in un unico script e gestisce tutte le dipendenze Python e VibeVoice.

1.  **Clona la Repository** o scarica lo ZIP e apri il terminale nella cartella principale.
2.  **Avvia il Setup:** Esegui lo script:

    ```bash
    python setup_jarvis.py
    ```

3.  **Segui i Passaggi:** Lo script guiderà l'utente attraverso la selezione della versione, la configurazione delle chiavi API (necessarie per Gemini, opzionali per Ollama) e l'installazione automatica di VibeVoice.

### 🚀 Istruzioni per l'Avvio (Post-Setup)

Lancia i server nell'ordine corretto in **terminali separati**:

| Terminale | Comando (Esempio) | Ruolo |
| :--- | :--- | :--- |
| **#1** | `ollama serve` (SOLO se usi OLLAMA) | Server LLM Locale |
| **#2** | `python VibeVoice/demo/vibevoice_realtime_demo.py --model_path microsoft/VibeVoice-Realtime-0.5B --port 8000` | Server TTS VibeVoice (Bloccante) |
| **#3** | `python jarvis_client.py` | Jarvis Client (Ascolto e Interazione) |

---

## 🇬🇧 ENGLISH GUIDE (English Guide)

### 🌟 Key Features

* **Dual AI Backbone:** Choose between **Gemini** (for low local power) or **Ollama** (for total privacy and local control).
* **Real-Time Performance:** Faster-Whisper (ASR) and VibeVoice (TTS) ensure minimal voice response latency.
* **Memory:** Uses **ChromaDB** for powerful contextual and long-term memory management.
* **Microphone Setup:** Interactive microphone selection on first run for maximum hardware compatibility.

*(The rest of the English guide follows the same clean structure as the Italian section.)*

---

## ❓ Supporto / Support

Se incontri problemi o hai domande sul progetto, sentiti libero di scrivermi, cerca su LinkedIn Francesco Gruner:

**[https://www.linkedin.com/in/francescogruner/](https://www.linkedin.com/in/francescogruner/)**

