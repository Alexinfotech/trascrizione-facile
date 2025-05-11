# src/config.py
import os
from pathlib import Path
import sys

# --- Informazioni Applicazione ---
APP_NAME = "TrascriviPro Avanzato"
VERSION = "1.0.1" # Incremento versione per la riscrittura
AUTHOR = "Tuo Nome/Azienda Qui" # Aggiungi se vuoi

# --- Percorsi di Base ---
# La directory radice del progetto (dove si trova la cartella 'src')
PROJECT_ROOT_DIR = Path(__file__).resolve().parent.parent

# --- Percorsi Dati Applicazione ---
# Nome della cartella principale per i dati dell'applicazione
# Verrà creata nella directory di supporto specifica della piattaforma.
APP_DATA_FOLDER_NAME = APP_NAME # Usiamo direttamente il nome dell'app per la cartella principale

# Determina il percorso base per i dati dell'applicazione in base alla piattaforma
if sys.platform == "darwin":  # macOS
    APP_BASE_DATA_PATH = Path.home() / "Library" / "Application Support" / APP_DATA_FOLDER_NAME
elif sys.platform == "win32":  # Windows
    # Usa %APPDATA% (roaming) o %LOCALAPPDATA% (non-roaming). Scegliamo APPDATA.
    appdata_path = os.getenv('APPDATA')
    if appdata_path:
        APP_BASE_DATA_PATH = Path(appdata_path) / APP_DATA_FOLDER_NAME
    else: # Fallback se APPDATA non è definito (improbabile)
        APP_BASE_DATA_PATH = Path.home() / ".config" / APP_DATA_FOLDER_NAME
else:  # Linux e altri (standard XDG)
    xdg_config_home = os.getenv('XDG_CONFIG_HOME')
    if xdg_config_home:
        APP_BASE_DATA_PATH = Path(xdg_config_home) / APP_DATA_FOLDER_NAME
    else:
        APP_BASE_DATA_PATH = Path.home() / ".config" / APP_DATA_FOLDER_NAME

# Sottocartelle per profili e log
PROFILES_DIR_NAME = "profiles"
LOGS_DIR_NAME = "logs" # Usato anche per i debug audio

PROFILES_DIR = APP_BASE_DATA_PATH / PROFILES_DIR_NAME
LOGS_DIR = APP_BASE_DATA_PATH / LOGS_DIR_NAME # Directory per i log testuali e la sottocartella audio_debugs

# Creazione delle directory necessarie all'avvio del modulo config
try:
    APP_BASE_DATA_PATH.mkdir(parents=True, exist_ok=True)
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    (LOGS_DIR / "audio_debugs").mkdir(parents=True, exist_ok=True) # Assicura che esista anche questa
except OSError as e:
    # Questo è un problema serio se non possiamo scrivere i dati dell'app.
    # In un'app reale, potremmo voler gestire questo in modo più elegante o uscire.
    print(f"ATTENZIONE: Impossibile creare le directory dei dati dell'applicazione: {e}")
    # Come fallback, si potrebbe tentare di usare la directory corrente, ma non è ideale per la distribuzione.
    # Per ora, lasciamo che un eventuale errore di scrittura avvenga più avanti se le directory non sono accessibili.

# File per le preferenze globali dell'app
APP_PREFERENCES_FILENAME = "preferences.json"
APP_PREFERENCES_FILE = APP_BASE_DATA_PATH / APP_PREFERENCES_FILENAME


# --- Impostazioni Whisper ---
DEFAULT_WHISPER_MODEL = "base"  # Modello di default all'avvio o per nuovi profili
DEFAULT_LANGUAGE = "italian"    # Lingua di default
AVAILABLE_WHISPER_MODELS = ["tiny", "base", "small", "medium", "large"] # Modelli selezionabili

# Parametri di trascrizione di default per Whisper
# Questi possono essere sovrascritti o estesi nel Transcriber
DEFAULT_WHISPER_TEMPERATURE = 0.0 # Per un output più deterministico
# Valori possibili per temperature: tupla (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)
# Valori più alti rendono l'output più casuale, valori più bassi più focalizzato e deterministico.

# Altri parametri che potremmo voler esporre o configurare in futuro:
#DEFAULT_BEAM_SIZE = 5
#DEFAULT_PATIENCE = None
#DEFAULT_NO_SPEECH_THRESHOLD = 0.6 # Soglia per considerare audio come "no speech"
#DEFAULT_LOGPROB_THRESHOLD = -1.0  # Soglia per la probabilità logaritmica dei token


# --- Comandi Vocali Speciali ---
# Le liste devono contenere stringhe in minuscolo
COMMAND_START_RECORDING = ["avvia dettatura", "inizia trascrizione", "modalità dettatura"] # Esempio
COMMAND_STOP_RECORDING = ["ferma dettatura", "stop trascrizione", "fine dettatura"]
# Potremmo aggiungere un COMMAND_TOGGLE_MODE se implementiamo una modalità comando
SPECIAL_COMMANDS = COMMAND_START_RECORDING + COMMAND_STOP_RECORDING # Verrà usato da TextProcessor


# --- Impostazioni di Logging ---
LOG_FILENAME = "app.log" # Nome del file di log principale
LOG_FILE = LOGS_DIR / LOG_FILENAME
LOG_LEVEL = "DEBUG"  # Livelli: DEBUG, INFO, WARNING, ERROR, CRITICAL (per sviluppo, DEBUG è utile)
# LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - [%(module)s.%(funcName)s:%(lineno)d] - %(message)s' # Definito nel logger


# --- Definizione Punteggiatura per Comandi Vocali ---
# Le chiavi devono essere in minuscolo per un matching case-insensitive nel TextProcessor.
# I valori sono come verranno inseriti.
# Questa mappa verrà usata SOLO se decidiamo di mantenere la punteggiatura vocale esplicita.
# Al momento, l'idea è di affidarsi a Whisper per la punteggiatura standard.
PUNCTUATION_MAP = {
    "virgola": ",",
    "punto": ".",
    "punto e virgola": ";",
    "punto interrogativo": "?",
    "punto esclamativo": "!",
    "due punti": ":",
    "trattino": "-",
    "linea": "-", # Alias per trattino
    "parentesi aperta": "(",
    "parentesi chiusa": ")",
    "apri parentesi": "(", # Alias
    "chiudi parentesi": ")", # Alias
    # "spazio": " ", # "spazio" come comando vocale è ambiguo, meglio gestirlo con pause naturali
    # "doppio spazio": "  ",
    "virgolette aperte": "\"", # Semplici virgolette dritte
    "virgolette chiuse": "\"",
    "apri virgolette": "\"",
    "chiudi virgolette": "\"",
    "a capo": "\n",      # Comando fondamentale da mantenere
    "nuova riga": "\n", # Alias
    "paragrafo": "\n\n", # Comando utile da mantenere
    "tab": "\t",         # Utile per formattazione
    "tabulazione": "\t"  # Alias
}
# Ordina le chiavi per lunghezza decrescente per evitare che chiavi più corte (es. "punto")
# vengano matchate prima di chiavi più lunghe che le contengono (es. "punto e virgola").
SORTED_PUNCTUATION_KEYS = sorted(PUNCTUATION_MAP.keys(), key=len, reverse=True)


# --- Impostazioni Editor Interno ---
INTERNAL_EDITOR_ENABLED_DEFAULT = False  # Default per nuovi profili

# --- Nomi File di Configurazione del Profilo ---
# Questi nomi verranno usati per i file JSON all'interno di ogni cartella di profilo.
PROFILE_SETTINGS_FILENAME = "settings.json"          # Impostazioni generali del profilo (modello, lingua, output, ecc.)
MACROS_FILENAME = "macros.json"                      # Macro definite dall'utente
VOCABULARY_FILENAME = "vocabulary.json"              # Vocabolario personalizzato (lista di parole/frasi)
PRONUNCIATION_RULES_FILENAME = "pronunciation.json"  # Regole di correzione della pronuncia


# --- Costanti per l'Interfaccia Utente (se necessarie globalmente) ---
# Esempio: DEFAULT_FONT_SIZE = 12

# --- Soglie e Parametri per il Trascrittore ---
# (Spostati qui da transcriber.py per centralizzare la configurazione)
# Valori attuali, possono essere ottimizzati
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1
# Durata di ogni blocco audio catturato da sounddevice (in secondi).
# Valori più piccoli = più callback = potenzialmente più reattivo ma più overhead.
AUDIO_BLOCK_DURATION_S = 0.2
# Secondi di silenzio dopo i quali processare l'audio accumulato.
AUDIO_SILENCE_THRESHOLD_S = 1.0
# Max secondi di audio da bufferizzare prima di forzare una trascrizione intermedia,
# anche se non c'è silenzio. Aumentare questo può dare più contesto a Whisper.
AUDIO_MAX_BUFFER_S_INTERIM = 6.0 # AUMENTATO COME DA TUA RICHIESTA (era 4.0)
# Minimi secondi di audio registrato per considerare il silenzio come una pausa valida.
AUDIO_MIN_SPEECH_FOR_SILENCE_S = 0.5
# Minimi secondi di audio necessari nel buffer finale (quando si stoppa) per processarlo.
AUDIO_MIN_CHUNK_FOR_FINAL_S = 0.2