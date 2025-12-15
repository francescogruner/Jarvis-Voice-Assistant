import os
import google.generativeai as genai
from collections.abc import Iterable
import chromadb
from chromadb.utils import embedding_functions 
import uuid
import re
import requests
from datetime import datetime
from colorama import Fore, Style
import ast
import operator
import time 
from dotenv import load_dotenv # 🟢 NUOVO: per leggere il .env

# 🟢 Carica le variabili dal file .env all'avvio
load_dotenv()

# ==========================================
# 🔑 CONFIGURAZIONE API CHIAVI (LEGGE DAL .env)
# ==========================================
# Rimuove il default hard-coded per la GEMINI_API_KEY
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY: raise RuntimeError("GEMINI_API_KEY non impostata nel file .env o come variabile d'ambiente.")
genai.configure(api_key=API_KEY)

# 🟢 DATI PER LA RICERCA WEB DI GOOGLE (con fallback per errore chiaro)
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY", "ERRORE_CHIAVE_MANCANTE") 
GOOGLE_SEARCH_CX = os.getenv("GOOGLE_SEARCH_CX", "ERRORE_CX_MANCANTE") 

SIMILARITY_THRESHOLD = 1.4 
DEDUPLICATION_THRESHOLD = 0.3

# Mappa per gli operatori AST (Calcolatrice Sicura)
_op_map = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.USub: operator.neg, ast.UAdd: operator.pos,
    ast.Pow: operator.pow
}

print(f"{Fore.CYAN}🧠 [Brain] Init Database...{Style.RESET_ALL}")
try:
    db_path = os.path.join(os.getcwd(), "memoria_db")
    chroma_client = chromadb.PersistentClient(path=db_path)
    embedder_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    collection = chroma_client.get_or_create_collection(
        name="user_memories",
        embedding_function=embedder_fn
    )
    print(f"{Fore.GREEN}✅ Database Caricato: {collection.count()} ricordi.{Style.RESET_ALL}")
except Exception as e:
    print(f"{Fore.RED}❌ ERRORE DATABASE: {e}{Style.RESET_ALL}"); collection = None

# ==========================================
# 🛠️ CLASSE TOOLS (Tutte le Abilità Reali)
# ==========================================
class Tools:
    # --- BASE (Calcolatrice Sicura) ---
    @staticmethod
    def _evaluate_expression(node):
        if isinstance(node, ast.Num): return node.n
        if isinstance(node, ast.BinOp):
            return _op_map[type(node.op)](Tools._evaluate_expression(node.left), Tools._evaluate_expression(node.right))
        if isinstance(node, ast.UnaryOp):
            return _op_map[type(node.op)](Tools._evaluate_expression(node.operand))
        if isinstance(node, ast.Expression): return Tools._evaluate_expression(node.body)
        raise TypeError(node)

    @staticmethod
    def calculate(expression):
        """Esegue calcoli matematici in modo sicuro."""
        try:
            tree = ast.parse(expression, mode='eval')
            result = Tools._evaluate_expression(tree)
            return str(result)
        except Exception:
            return "Errore calcolo."
    
    # --- MEMORIA ---
    @staticmethod
    def save_memory(info):
        """Salva informazioni importanti sull'utente nel database a lungo termine."""
        if collection is None: return "Errore DB."
        try:
            collection.add(documents=[info], metadatas=[{"speaker": "user", "timestamp": datetime.now().isoformat()}], ids=[str(uuid.uuid4())])
            print(f"{Fore.GREEN}💾 [MEMORIA] Salvato.{Style.RESET_ALL}")
            return "Salvato."
        except Exception as e: return f"Errore: {e}"

    # 🟢 --- WEB SEARCH (Google Search API Stabile) ---
    @staticmethod
    def web_search(query):
        """Esegue una ricerca su Google via API e restituisce un riassunto."""
        print(f"{Fore.CYAN}🌐 Google Search API: '{query}'...{Style.RESET_ALL}")
        
        # 🟢 VERIFICA DEI VALORI DEL .env
        if GOOGLE_SEARCH_API_KEY == "ERRORE_CHIAVE_MANCANTE":
            return "Errore: GOOGLE_SEARCH_API_KEY non trovata nel file .env."
        if GOOGLE_SEARCH_CX == "ERRORE_CX_MANCANTE":
            return "Errore: GOOGLE_SEARCH_CX non trovato nel file .env."
        
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
            for i in range(3): 
                response = requests.get(url, params=params, timeout=5)
                response.raise_for_status() 
                data = response.json()
                
                if data.get('error'):
                    error_detail = data['error']['message']
                    print(f"{Fore.RED}❌ ERRORE GOOGLE API (Configurazione/Rate-Limit): {error_detail}{Style.RESET_ALL}")
                    return f"Errore di configurazione API: {error_detail}"
                
                items = data.get("items", [])
                
                if items:
                    results = []
                    for item in items:
                        results.append(f"- {item.get('title')}: {item.get('snippet')}")
                    
                    return "\n".join(results)[:1500]
                
                time.sleep(1.5) 
                
            return "Nessun risultato trovato sul web."

        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}❌ ERRORE GOOGLE API (Network): {e}{Style.RESET_ALL}")
            return "In questo momento non riesco a cercare sul web. Riprova più tardi."
        except Exception as e:
            print(f"{Fore.RED}❌ ERRORE GOOGLE API (Generico): {e}{Style.RESET_ALL}")
            return "In questo momento non riesco a cercare sul web. Riprova più tardi."


    # --- METEO (Open-Meteo) ---
    @staticmethod
    def get_weather(city):
        """Ottiene il meteo attuale per una specifica città."""
        print(f"{Fore.CYAN}☁️ Meteo: {city}...{Style.RESET_ALL}")
        try:
            geo = requests.get("https://geocoding-api.open-meteo.com/v1/search", params={"name": city, "count": 1}, timeout=3).json()
            if not geo.get("results"): return "Città non trovata."
            lat, lon = geo["results"][0]["latitude"], geo["results"][0]["longitude"]
            weather_data = requests.get("https://api.open-meteo.com/v1/forecast", params={"latitude": lat, "longitude": lon, "current_weather": True}, timeout=3).json()
            cw = weather_data.get("current_weather")
            if not cw: return "Impossibile ottenere il meteo attuale."
            return f"Meteo {city}: {cw['temperature']}°C, Vento {cw['windspeed']} km/h."
        except Exception as e: return f"Err Meteo: {e}"

    # --- FILESYSTEM (Desktop Sandbox) ---
    @staticmethod
    def _get_path(name=""): 
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        target = os.path.normpath(os.path.join(desktop, name))
        if not target.startswith(desktop): raise PermissionError("Tentativo di accesso esterno al Desktop.")
        return target

    @staticmethod
    def list_files():
        """Elenca i file e le cartelle presenti sul Desktop."""
        print(f"{Fore.CYAN}📂 Listo file Desktop...{Style.RESET_ALL}")
        try: files = [f for f in os.listdir(Tools._get_path()) if not f.startswith('.')]; return "File: " + ", ".join(files[:30])
        except Exception as e: return f"Errore: {e}"
        
    @staticmethod
    def read_file(filename):
        """Legge il contenuto di un file di testo sul Desktop."""
        print(f"{Fore.CYAN}📂 Leggo: {filename}...{Style.RESET_ALL}")
        try:
            path = Tools._get_path(filename); 
            if not os.path.exists(path): return "File non trovato."
            with open(path, 'r', encoding='utf-8', errors='ignore') as f: return f.read()[:2000]
        except PermissionError: return "Accesso file non consentito."
        except Exception as e: return f"Err: {e}"
    
    @staticmethod
    def write_file(filename, content):
        """Crea o sovrascrive un file di testo sul Desktop."""
        print(f"{Fore.CYAN}✍️ Scrivo: {filename}...{Style.RESET_ALL}")
        try:
            path = Tools._get_path(filename)
            with open(path, 'w', encoding='utf-8') as f: f.write(content)
            return "File scritto."
        except PermissionError: return "Accesso file non consentito."
        except Exception as e: return f"Err: {e}"

    @staticmethod
    def create_folder(foldername):
        """Crea una nuova cartella sul Desktop."""
        print(f"{Fore.CYAN}📁 Creo Cartella: {foldername}...{Style.RESET_ALL}")
        try:
            path = Tools._get_path(foldername)
            os.makedirs(path, exist_ok=True)
            return "Cartella creata."
        except PermissionError: return "Accesso file non consentito."
        except Exception as e: return f"Err: {e}"
    
    # --- BASE ---
    @staticmethod
    def get_time(): return datetime.now().strftime("%H:%M")

# --- CLASSE MEMORIA (Per compatibilità e reset) ---
class Memory:
    @staticmethod
    def save_direct(text): return Tools.save_memory(text)
    
    @staticmethod
    def search(query, limit=3):
        if collection is None: return []
        try:
            res = collection.query(query_texts=[query], n_results=limit)
            return [doc for doc, dist in zip(res['documents'][0], res['distances'][0]) if dist < SIMILARITY_THRESHOLD] if res['documents'] else []
        except: return []
    
    @staticmethod
    def reset():
        if collection is None: return "Errore DB."
        try:
            ids = collection.get()['ids']
            if ids: collection.delete(ids=ids)
            print(f"{Fore.GREEN}🗑️ [DB] Memoria cancellata.{Style.RESET_ALL}")
            return "Memoria cancellata completamente."
        except: return "Errore reset."

# --- DEFINIZIONE TOOLS PER GEMINI ---
def save_mem(info: str): 
    """Salva informazioni importanti sull'utente nel database a lungo termine."""
    return Tools.save_memory(info)
def search_web(query: str):
    """Esegue una ricerca su internet e restituisce un riassunto."""
    return Tools.web_search(query)
def get_weather_at(city: str):
    """Ottiene il meteo attuale per una specifica città."""
    return Tools.get_weather(city)
def list_f():
    """Elenca i file e le cartelle presenti sul Desktop."""
    return Tools.list_files()
def read_f(filename: str):
    """Legge il contenuto di un file di testo sul Desktop."""
    return Tools.read_file(filename)
def write_f(filename: str, content: str):
    """Crea o sovrascrive un file di testo sul Desktop."""
    return Tools.write_file(filename, content)
def create_dir(foldername: str):
    """Crea una nuova cartella sul Desktop."""
    return Tools.create_folder(foldername)
def get_t():
    """Restituisce l'orario corrente."""
    return Tools.get_time()
def calc(expr: str):
    """Esegue un calcolo matematico."""
    return Tools.calculate(expr)

MY_TOOLS = [save_mem, search_web, get_weather_at, list_f, read_f, write_f, create_dir, get_t, calc]

# ==========================================
# 🤖 CERVELLO (MANUALE / VELOCE)
# ==========================================
class JarvisBrain:
    def __init__(self):
        # 🟢 ACCURATEZZA TEMPORALE: Data corretta per il contesto
        self.sys_instruction = (
            f"Oggi è {datetime.now().strftime('%d/%m/%Y')}. Sei Jarvis. Rispondi in italiano. "
            "Usa i tuoi strumenti per ogni compito che non puoi risolvere internamente. "
            "Usa `save_mem` solo per fatti personali espliciti e importanti. "
            "Usa lo strumento `search_web` SOLO quando l'utente ti chiede chiaramente di cercare su internet. "
            "QUANDO ESEGUI search_web, la query deve essere più corta e diretta possibile, fedele all'intento dell'utente."
        )
        
        try:
            model = genai.GenerativeModel("gemini-2.0-flash-lite-preview-02-05", tools=MY_TOOLS, system_instruction=self.sys_instruction)
            # Modalità Manuele (FAST MODE)
            self.chat = model.start_chat(enable_automatic_function_calling=False) 
            self.chat.send_message("Ping", stream=False)
            print(f"{Fore.GREEN}OK (FAST MODE) 🚀{Style.RESET_ALL}")
        except Exception as e: 
            print(f"{Fore.RED}Errore Init: {e}{Style.RESET_ALL}"); self.chat = None

    def think(self, user_text):
        if not self.chat: yield "Errore critico."; return

        # Recupero Memoria
        memories = Memory.search(user_text)
        prompt = user_text
        if memories:
            prompt = f"INFO MEMORIA:\n" + "\n".join([f"- {m}" for m in memories]) + f"\n\nUTENTE: {user_text}"
            print(f"{Fore.BLUE}🔍 Ricordi: {len(memories)}{Style.RESET_ALL}")
        
        try:
            response = self.chat.send_message(prompt, stream=False)
            
            # --- LOOP MANUALE DEI TOOLS (FIX BUG 400 resiliente) ---
            while hasattr(response, 'candidates') and response.candidates:
                
                calls = [p.function_call for p in response.candidates[0].content.parts if getattr(p, "function_call", None)]
                
                if not calls:
                    break 

                fc = calls[0]
                fname = fc.name
                args = dict(fc.args) if getattr(fc, "args", None) else {}
                
                print(f"{Fore.YELLOW}🛠️ Tool: {fname}{Style.RESET_ALL}")
                
                res = "Err"
                
                if fname == "save_mem": res = save_mem(**args)
                elif fname == "search_web": res = search_web(**args)
                elif fname == "get_weather_at": res = get_weather_at(**args)
                elif fname == "list_f": res = list_f()
                elif fname == "read_f": res = read_f(**args)
                elif fname == "write_f": res = write_f(**args)
                elif fname == "create_dir": res = create_dir(**args)
                elif fname == "get_t": res = get_t()
                elif fname == "calc": res = calc(**args)
                
                # 🟢 FIX COMPATIBILITÀ: Torniamo alla sintassi PROTOS Stabile 
                response = self.chat.send_message(
                    genai.protos.Content(parts=[genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=fname, 
                            response={"result": res}
                        )
                    )])
                )

            if response.text: yield response.text.replace("*", "")
                
        except Exception as e:
            print(f"{Fore.RED}Err Brain: {e}{Style.RESET_ALL}")
            yield "Ho avuto un problema tecnico. Riprova tra poco."