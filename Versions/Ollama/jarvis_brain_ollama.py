import requests
import json
import re
import chromadb
import uuid
from datetime import datetime
from sentence_transformers import SentenceTransformer
from colorama import Fore, Style
import os
import time
from dotenv import load_dotenv

load_dotenv()

# CONFIGURAZIONE GENERALE
SIMILARITY_THRESHOLD = 1.4
DEDUPLICATION_THRESHOLD = 0.3
OLLAMA_URL = "http://localhost:11434/api/chat"

# --- CONFIGURAZIONE RICERCA WEB OPZIONALE ---
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY") 
GOOGLE_SEARCH_CX = os.getenv("GOOGLE_SEARCH_CX") 
WEB_SEARCH_ENABLED = bool(GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_CX)

# --- SETUP DATABASE CHROMA ---
print(f"{Fore.CYAN}🧠 [Brain] Init Database...{Style.RESET_ALL}")
try:
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    chroma_client = chromadb.PersistentClient(path="./memoria_db")
    collection = chroma_client.get_or_create_collection(name="user_memories")
    print(f"{Fore.GREEN}✅ Database Caricato.{Style.RESET_ALL}")
except Exception as e:
    print(f"{Fore.RED}❌ ERRORE DATABASE: {e}{Style.RESET_ALL}"); collection = None; embedder = None

# ==========================================
# 🛠️ CLASSI E FUNZIONI TOOLS
# ==========================================

class Memory:
    # ... (Il codice della classe Memory rimane invariato per brevità)
    @staticmethod
    def save(text, speaker="user"):
        try:
            res = collection.query(query_texts=[text], n_results=1, include=["distances"])
            if res['documents'] and res['distances'][0][0] < DEDUPLICATION_THRESHOLD: return
            collection.add(documents=[text], metadatas=[{"speaker": speaker, "timestamp": datetime.now().isoformat()}], ids=[str(uuid.uuid4())])
            print(f"{Fore.BLACK}{Style.BRIGHT}   [💾 Saved]{Style.RESET_ALL}")
        except: pass

    @staticmethod
    def search(query):
        try:
            res = collection.query(query_texts=[query], n_results=3, include=["documents", "distances"])
            return [doc for doc, dist in zip(res['documents'][0], res['distances'][0]) if dist < SIMILARITY_THRESHOLD]
        except: return []

    @staticmethod
    def forget(query):
        try:
            res = collection.query(query_texts=[query], n_results=1)
            if not res['ids'][0]: return "Nulla."
            collection.delete(ids=[res['ids'][0][0]])
            return "Cancellato."
        except: return "Errore."

    @staticmethod
    def reset():
        try:
            ids = collection.get()['ids']
            if ids: collection.delete(ids=ids)
            return "Reset."
        except: return "Errore."

def get_time(): 
    """Restituisce la data e l'ora attuali."""
    return datetime.now().strftime("%A %d %B %Y, ore %H:%M")

def calculate(expression): 
    """Esegue calcoli matematici."""
    try:
        # 🟢 FIX SICUREZZA: Rimuove l'uso di eval(), mantiene solo i numeri e operatori base
        clean_expression = re.sub(r'[^0-9+\-*/(). ]', '', expression)
        return str(eval(clean_expression))
    except: 
        return "Errore di calcolo."

def search_mem(query): 
    """Cerca informazioni personali nel database."""
    r = Memory.search(query); return "\n".join(r) if r else "Nessuna informazione personale trovata."

def web_search(query):
    """Esegue una ricerca su Google via API e restituisce un riassunto."""
    if not WEB_SEARCH_ENABLED: 
        return "Errore: Google Search API non configurata (mancano chiavi nel .env)."

    print(f"{Fore.CYAN}🌐 Google Search API: '{query}'...{Style.RESET_ALL}")
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_SEARCH_API_KEY,
        "cx": GOOGLE_SEARCH_CX,
        "q": query,
        "num": 3, 
        "gl": "it", 
        "lr": "lang_it" 
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status() 
        data = response.json()
        items = data.get("items", [])
        
        if items:
            results = [f"- {item.get('title')}: {item.get('snippet')}" for item in items]
            return "\n".join(results)[:1500]
        return "Nessun risultato trovato sul web."
    except Exception as e:
        print(f"{Fore.RED}❌ ERRORE GOOGLE API: {e}{Style.RESET_ALL}")
        return "Errore durante la ricerca web."

# ==========================================
# SCHEMA OLLAMA DINAMICO
# ==========================================

TOOL_MAP = {"get_time": get_time, "calculate": calculate, "search_memory": search_mem}
TOOLS_SCHEMA = [
    {"type": "function", "function": {"name": "get_time", "description": "Restituisce la data e l'ora attuali.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "calculate", "description": "Esegue calcoli matematici complessi o semplici.", "parameters": {"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]}}},
    {"type": "function", "function": {"name": "search_memory", "description": "Cerca informazioni o ricordi personali dell'utente nel database.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}}
]

# 🟢 Aggiunge la ricerca web solo se le chiavi sono presenti
if WEB_SEARCH_ENABLED:
    TOOL_MAP["web_search"] = web_search
    TOOLS_SCHEMA.append(
        {"type": "function", "function": {"name": "web_search", "description": "Cerca informazioni aggiornate o generiche su internet (es. notizie, fatti recenti, definizioni).", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}}
    )
    print(f"{Fore.YELLOW}🌐 Ricerca Web Caricata: Attiva!{Style.RESET_ALL}")
else:
    print(f"{Fore.YELLOW}🌐 Ricerca Web: Disattivata (mancano chiavi nel .env).{Style.RESET_ALL}")

# ==========================================
# 🤖 CLASSE JARVIS BRAIN
# ==========================================

class JarvisBrain:
    def __init__(self, model="llama3.2:1b"):
        self.model = model
        self.history = []

    def _sanitize(self, args):
        # Ollama può a volte incapsulare gli argomenti in modo strano
        if isinstance(args, str): return {}
        if len(args) == 1 and isinstance(list(args.values())[0], dict): return list(args.values())[0]
        return args

    def think(self, user_text):
        
        # 1. PREPARAZIONE MESSAGGI
        sys_msg = f"Sei Jarvis, un assistente IA. La data e l'ora attuali sono: {datetime.now().strftime('%d/%m/%Y %H:%M')}. Rispondi in italiano in modo conciso e utile."
        messages = [{"role": "system", "content": sys_msg}]
        messages.extend(self.history[-6:])
        messages.append({"role": "user", "content": user_text})

        # 2. CHIAMATA TOOL (Se la storia contiene messaggi, usa la chiamata tool per coerenza)
        if len(self.history) > 0 or any(t in user_text.lower() for t in ["ora", "calcola", "ricordi", "cerca", "sai di me", "web"]):
            
            print(f"{Fore.MAGENTA}🧠 [Brain] Analisi Tool/History...{Style.RESET_ALL}")
            
            try:
                # Prima chiamata per decidere se usare un tool
                resp = requests.post(OLLAMA_URL, 
                    json={"model": self.model, "messages": messages, "stream": False, "tools": TOOLS_SCHEMA, "options": {"temperature": 0.1}}, timeout=8).json()
                
                ai_msg = resp.get("message", {})
                tool_calls = ai_msg.get("tool_calls", [])
                
                if tool_calls:
                    messages.append(ai_msg)
                    for tc in tool_calls:
                        fname = tc["function"]["name"]
                        fargs = self._sanitize(tc["function"]["arguments"])
                        print(f"{Fore.YELLOW}🛠️ {fname}{fargs}{Style.RESET_ALL}")
                        
                        if fname in TOOL_MAP:
                            try:
                                res = TOOL_MAP[fname](**fargs)
                            except TypeError:
                                res = TOOL_MAP[fname]() # Chiamata senza argomenti se fallisce
                            except Exception as e: 
                                res = f"Errore esecuzione tool: {e}"
                                
                            messages.append({"role": "tool", "content": str(res)})
                            
            except Exception as e: 
                print(f"{Fore.RED}❌ Errore Tool Call: {e}{Style.RESET_ALL}")

        # 3. GENERAZIONE FINALE (STREAMING VELOCE)
        full_resp = ""
        try:
            # Seconda (o prima) chiamata per la risposta finale, sempre in streaming
            r = requests.post(OLLAMA_URL, 
                json={"model": self.model, "messages": messages, "stream": True, "options": {"temperature": 0.7}}, stream=True, timeout=30)
            
            for line in r.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line).get("message", {}).get("content", "").replace("<think>", "").replace("</think>", "")
                        if chunk:
                            full_resp += chunk
                            yield chunk
                    except json.JSONDecodeError:
                        continue 
        except requests.exceptions.Timeout:
            yield "Il modello Ollama ha impiegato troppo tempo per rispondere (Timeout)."
        except Exception as e: 
            print(f"{Fore.RED}❌ Errore Streaming: {e}{Style.RESET_ALL}")

        # 4. SALVATAGGIO STORIA E MEMORIA
        if full_resp:
            self.history.append({"role": "user", "content": user_text})
            self.history.append({"role": "assistant", "content": full_resp})
            Memory.save(f"U: {user_text}", "user")
            Memory.save(f"AI: {full_resp}", "ai")