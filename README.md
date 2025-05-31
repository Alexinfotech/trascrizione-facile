# TrascriviPro Avanzato

**Versione:** 1.0.1 (come da `src/config.py`)
**Data Ultimo Aggiornamento Significativo:** 2024-05-20
**Autore:** [Il tuo nome o nome dell'organizzazione]

## Indice

1.  [Descrizione Generale](#descrizione-generale)
2.  [Funzionalità Principali](#funzionalità-principali)
3.  [Tecnologie Utilizzate](#tecnologie-utilizzate)
4.  [Struttura del Progetto](#struttura-del-progetto)
5.  [Installazione e Avvio](#installazione-e-avvio)
    - [5.1. Prerequisiti (per macOS, ambiente di sviluppo)](#51-prerequisiti-per-macos-ambiente-di-sviluppo)
    - [5.2. Creazione Ambiente Virtuale e Installazione Dipendenze (macOS)](#52-creazione-ambiente-virtuale-e-installazione-dipendenze-macos)
    - [5.3. Avvio dell'Applicazione (macOS, da sorgente)](#53-avvio-dellapplicazione-macos-da-sorgente)
    - [X. Note per l'Esecuzione su Windows (da Sorgente, Sperimentale)](#x-note-per-lesecuzione-su-windows-da-sorgente-sperimentale)
6.  [Guida all'Uso](#guida-alluso)
    - [Profili Utente](#profili-utente)
    - [Avvio e Arresto Trascrizione](#avvio-e-arresto-trascrizione)
    - [Comandi Vocali](#comandi-vocali)
    - [Editor Interno ed Esterno](#editor-interno-ed-esterno)
    - [Salvataggio in PDF](#salvataggio-in-pdf)
7.  [Architettura e Dettagli Tecnici](#architettura-e-dettagli-tecnici)
    - [Modulo Principale (`main.py`)](#modulo-principale-mainpy)
    - [Configurazione (`config.py`)](#configurazione-configpy)
    - [Logger (`utils/logger.py`)](#logger-utilsloggerpy)
    - [Core Logic (`src/core/`)](#core-logic-srccore)
      - [`profile_manager.py`](#profile_managerpy)
      - [`transcriber.py`](#transcriberpy)
      - [`text_processor.py`](#text_processorpy)
      - [`output_handler.py`](#output_handlerpy)
    - [Interfaccia Grafica (`src/gui/`)](#interfaccia-grafica-srcgui)
      - [`main_window.py`](#main_windowpy)
      - [`profile_dialogs.py`](#profile_dialogspy)
    - [Gestione dei Thread](#gestione-dei-thread)
    - [Persistenza Dati](#persistenza-dati)
8.  [Impacchettamento per macOS (Creazione App Installabile)](#impacchettamento-per-macos-creazione-app-installabile)
    - [Prerequisiti per l'Impacchettamento](#prerequisiti-per-limpacchettamento)
    - [Installazione di PyInstaller](#installazione-di-pyinstaller)
    - [Creazione del File `.spec`](#creazione-del-file-spec)
    - [Modifica del File `.spec` (Cruciale)](#modifica-del-file-spec-cruciale)
    - [Esecuzione di PyInstaller con il File `.spec`](#esecuzione-di-pyinstaller-con-il-file-spec)
    - [Verifica e Distribuzione dell'App](#verifica-e-distribuzione-dellapp)
    - [Icona dell'Applicazione (Opzionale ma Raccomandato)](#icona-dellapplicazione-opzionale-ma-raccomandato)
    - [Firma del Codice (Opzionale ma Raccomandato per Distribuzione)](#firma-del-codice-opzionale-ma-raccomandato-per-distribuzione)
9.  [Troubleshooting e Problemi Noti](#troubleshooting-e-problemi-noti)
10. [Possibili Miglioramenti Futuri](#possibili-miglioramenti-futuri)
11. [Contributi](#contributi)
12. [Licenza](#licenza)

---

## Descrizione Generale

**TrascriviPro Avanzato** è un'applicazione desktop per macOS progettata per offrire una soluzione di trascrizione vocale in tempo reale, locale e altamente personalizzabile. Sfruttando la potenza del modello Whisper di OpenAI (eseguito localmente per garantire la privacy), l'applicazione permette agli utenti di dettare testo direttamente in applicazioni esterne o in un editor integrato, con supporto per comandi vocali, profili utente multipli e un'ampia gamma di personalizzazioni.

L'obiettivo generale è fornire agli utenti macOS uno strumento di dettatura potente e flessibile che permetta di trasformare rapidamente il parlato in testo scritto, mantenendo il controllo completo sui propri dati e sulle impostazioni di trascrizione.

## Funzionalità Principali

-   **Trascrizione Vocale Locale in Tempo Reale:** Converte il parlato dell'utente in testo utilizzando `openai-whisper` per la trascrizione offline, garantendo privacy e nessun costo per API esterne. L'output del testo avviene a segmenti (dopo pause o ogni tot secondi di parlato continuo), non parola per parola istantaneamente.
-   **Output Flessibile:**
    -   Trascrizione diretta in qualsiasi applicazione esterna attiva (es. editor di testo, software di refertazione) tramite simulazione tastiera (`pyautogui`).
    -   Editor di testo integrato per la visualizzazione e la modifica del testo trascritto.
-   **Comandi Vocali:**
    -   Dettatura della punteggiatura (es. "virgola", "punto") che viene convertita nei simboli appropriati.
    -   Utilizzo di comandi di formattazione come "a capo", "nuova riga", "paragrafo".
    -   Comandi speciali come "ferma dettatura" per arrestare la trascrizione.
    -   Supporto futuro per comandi vocali di avvio della trascrizione.
-   **Personalizzazione Avanzata tramite Profili Utente:**
    -   Ogni utente può creare e gestire più profili con impostazioni personalizzate.
    -   Ogni profilo memorizza impostazioni specifiche per:
        -   **Macro (AutoText):** Comandi vocali personalizzati per inserire rapidamente blocchi di testo predefiniti.
        -   **Vocabolario Personalizzato:** Un elenco di parole/frasi (es. termini medici, tecnici) per migliorare l'accuratezza del riconoscimento di Whisper.
        -   **Regole di Correzione Pronuncia:** Mappature "testo parlato" -> "testo da scrivere" per correggere difetti di pronuncia o usare abbreviazioni.
        -   **Preferenze del modello Whisper** (es. tiny, base, small, medium, large).
        -   **Preferenza per l'output** (editor interno vs. esterno).
        -   Abilitazione della **registrazione audio opzionale per debug**.
-   **Import/Export Profili:** Facile condivisione e backup dei profili utente tramite file JSON (salvati in sottocartelle dedicate dentro la directory di supporto dell'app).
-   **Salvataggio in PDF:** Il testo dall'editor interno può essere esportato in formato PDF.
-   **Logging Dettagliato:** Registrazione dettagliata delle operazioni dell'app su file e console.
-   **Selezione del Dispositivo di Input Audio:** Possibilità di scegliere il microfono desiderato.

## Tecnologie Utilizzate

-   **Python:** Linguaggio di programmazione principale (versione 3.9+ raccomandata).
-   **PyQt6:** Framework per la creazione dell'interfaccia grafica utente (GUI).
-   **`openai-whisper`:** Libreria per la trascrizione vocale automatica (ASR) basata sui modelli Whisper di OpenAI, eseguita localmente.
-   **`sounddevice`:** Libreria per la cattura e la riproduzione audio multipiattaforma.
-   **`pyautogui`:** Libreria per controllare mouse e tastiera, utilizzata per inviare testo ad applicazioni esterne (richiede permessi di Accessibilità su macOS).
-   **JSON:** Formato utilizzato per il salvataggio dei profili utente, delle preferenze dell'applicazione e delle configurazioni.
-   **NumPy:** Utilizzata da `sounddevice` e `whisper` per la manipolazione di array numerici (audio).
-   **Wave:** Modulo standard Python per la lettura e scrittura di file audio `.wav`.

## Struttura del Progetto

La struttura principale del progetto è organizzata come segue:

    TrascriviPro_Avanzato/
    ├── src/                     # Codice sorgente dell'applicazione
    │   ├── __init__.py
    │   ├── main.py              # Punto di ingresso dell'applicazione
    │   ├── config.py            # Configurazioni globali, costanti, percorsi
    │   ├── core/                # Logica di business e funzionalità centrali
    │   │   ├── __init__.py
    │   │   ├── profile_manager.py # Gestione dei profili utente
    │   │   ├── transcriber.py     # Logica di cattura audio e trascrizione Whisper
    │   │   ├── text_processor.py  # Elaborazione testo (macro, comandi, punteggiatura)
    │   │   └── output_handler.py  # Gestione output testo (editor interno/esterno)
    │   ├── gui/                 # Componenti dell'interfaccia grafica (PyQt6)
    │   │   ├── __init__.py
    │   │   ├── main_window.py     # Finestra principale dell'applicazione
    │   │   └── profile_dialogs.py # Dialoghi per gestione profili e impostazioni
    │   └── utils/               # Utility varie (es. logger)
    │       ├── __init__.py
    │       └── logger.py          # Configurazione del sistema di logging
    ├── profiles/                # NON nel repository; directory creata in Application Support per i dati dei profili
    ├── logs/                    # NON nel repository; directory creata in Application Support per i file di log e debug audio
    ├── README.md                # Questo file
    └── requirements.txt         # File con le dipendenze del progetto
    └── setup_macos.spec         # (Dopo creazione) File di specifica per PyInstaller

Le directory `profiles/` e `logs/` vengono create dinamicamente dall'applicazione nella directory di supporto appropriata per macOS (`~/Library/Application Support/TrascriviPro Avanzato/`).

## 5. Installazione e Avvio

Questa applicazione è stata sviluppata e ottimizzata con l'obiettivo di diventare un'applicazione `.app` **installabile e nativa per macOS**. Le istruzioni seguenti si riferiscono all'esecuzione del codice sorgente in un ambiente di sviluppo, principalmente su macOS.

### 5.1. Prerequisiti (per macOS, ambiente di sviluppo)

-   **macOS:** L'ambiente di sviluppo e test primario.
-   **Python:** Versione 3.9 o superiore. Puoi verificarlo con `python3 --version`.
-   **Pip:** Gestore di pacchetti Python, solitamente installato con Python.
-   **FFmpeg:** Whisper richiede FFmpeg per la gestione dei formati audio.
    -   Installazione tramite [Homebrew](https://brew.sh/index_it) (consigliato su macOS):
        `brew install ffmpeg`
-   **PortAudio:** `sounddevice` dipende da PortAudio. Su macOS, di solito è gestito correttamente. Se necessario:
    `brew install portaudio`

### 5.2. Creazione Ambiente Virtuale e Installazione Dipendenze (macOS)

Per mantenere le dipendenze del progetto isolate, consiglio caldamente di usare un ambiente virtuale.

1.  **Clona il Repository:**
    `git clone https://github.com/Alexinfotech/trascrizione-facile.git`
    `cd trascrizione-facile`
2.  **Crea un ambiente virtuale** (lo chiamo `venv`):
    `python3 -m venv venv`
3.  **Attiva l'ambiente virtuale:**
    `source venv/bin/activate`
    (Il prompt del terminale mostrerà `(venv)` all'inizio).
4.  **Installa le dipendenze** dal file `requirements.txt`:
    `pip install -r requirements.txt`
    *Il file `requirements.txt` contiene tutte le librerie necessarie come PyQt6, openai-whisper, torch, torchaudio, sounddevice, pyautogui, e numpy.*

### 5.3. Avvio dell'Applicazione (macOS, da sorgente)

Con l'ambiente virtuale attivato e le dipendenze installate, dalla directory principale del progetto (`trascrizione-facile/`):
`python -m src.main`

L'applicazione dovrebbe avviarsi. I log verranno stampati sulla console e salvati nel file `app.log` nella directory di supporto dell'applicazione (`~/Library/Application Support/TrascriviPro Avanzato/logs/` su macOS).

### X. Note per l'Esecuzione su Windows (da Sorgente, Sperimentale)

Sebbene questa applicazione sia stata progettata e ottimizzata primariamente per macOS con l'intento di creare un'app .app installabile, è teoricamente possibile eseguire il codice sorgente anche su Windows. Tuttavia, questo richiede una configurazione manuale più complessa e non è garantito che tutte le funzionalità si comportino esattamente come su macOS senza specifici test e adattamenti.

Se desideri provare ad eseguire l'applicazione da sorgente su un PC Windows utilizzando, ad esempio, Visual Studio Code:

1.  **Clona il Repository su Windows:**
    `git clone https://github.com/Alexinfotech/trascrizione-facile.git`
    `cd trascrizione-facile`
2.  **Configura un Ambiente Python su Windows:**
    -   Installa Python 3.9+ per Windows da python.org (assicurati di aggiungere Python al PATH).
    -   Crea un ambiente virtuale:
        `python -m venv venv`
    -   Attiva l'ambiente virtuale (il comando è diverso su Windows):
        `.\venv\Scripts\activate`
3.  **Installa le Dipendenze Critiche per Windows:**
    -   **FFmpeg per Windows:**
        -   Scarica i binari di FFmpeg per Windows (es. da gyan.dev). Scegli una release build (non la nightly).
        -   Estrai l'archivio (es. in `C:\ffmpeg`).
        -   Aggiungi la cartella `bin` di FFmpeg (es. `C:\ffmpeg\bin`) al PATH di sistema di Windows. In alternativa, puoi copiare `ffmpeg.exe`, `ffplay.exe`, `ffprobe.exe` nella stessa cartella dello script Python principale o in una cartella già nel PATH. Questo è cruciale per Whisper.
    -   **PyTorch e Torchaudio per Windows:** L'installazione di PyTorch può essere specifica. Visita il sito ufficiale di PyTorch e usa il configuratore per ottenere il comando pip corretto per la tua configurazione (es. CPU-only o con supporto CUDA se hai una GPU NVIDIA).
        -   Esempio per CPU-only (verifica sempre sul sito di PyTorch per il comando più aggiornato):
            `pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu`
    -   **Altre Dipendenze Python:** Installa il resto delle dipendenze da `requirements.txt` (se hai adattato PyTorch) o manualmente:
        `pip install PyQt6 openai-whisper sounddevice pyautogui numpy`
        *(Se `requirements.txt` include una versione specifica di torch/torchaudio non adatta a Windows, installale separatamente come sopra e poi installa il resto).*
4.  **Esegui l'Applicazione:**
    -   Dal terminale (con l'ambiente virtuale attivo):
        `python -m src.main`
**Potenziali Aree di Modifica/Verifica per Windows:**
-   **Percorsi File:** La logica in `src/config.py` per `APP_BASE_DATA_PATH` tenta già di gestire Windows usando `%APPDATA%`. Verifica che i profili e i log vengano creati e letti correttamente (solitamente in `C:\Users\TUO_UTENTE\AppData\Roaming\TrascriviPro Avanzato\`).
-   **`sounddevice`:** La selezione del microfono e il suo funzionamento potrebbero richiedere verifiche.
-   **`pyautogui`:** L'interazione con altre applicazioni (output esterno) va testata. Potrebbe funzionare senza i permessi di Accessibilità richiesti da macOS, ma UAC o antivirus potrebbero interferire.
-   **Estetica GUI:** Piccole differenze visive sono normali tra macOS e Windows con PyQt6.
-   **Librerie C++ Ridistribuibili:** Alcune dipendenze potrebbero richiedere l'installazione di specifici pacchetti ridistribuibili di Microsoft Visual C++ se non già presenti.

## Guida all'Uso

### Profili Utente

-   **Gestione Profili:** Accedi dal menu `File > Gestisci Profili...` o dal pulsante "Gestisci Profili..." nella finestra principale.
    -   **Crea:** Inserisci un nome per un nuovo profilo. Verrà creato con impostazioni di default.
    -   **Carica:** Seleziona un profilo dalla lista e clicca "Carica Selezionato e Chiudi" (o doppio click) per attivarlo.
    -   **Elimina:** Rimuove permanentemente un profilo selezionato.
    -   **Importa/Esporta:** Permette di salvare un profilo in un file `.zip` o di importarne uno da un file `.zip`.
-   **Impostazioni Profilo Attivo:** Accedi dal menu `File > Impostazioni Profilo Attivo...`. Qui puoi configurare:
    -   **Nome Visualizzato:** Modifica il nome del profilo.
    -   **Modello Whisper:** Scegli la dimensione del modello (da `tiny` a `large`). Modelli più grandi sono più accurati ma richiedono più risorse e tempo per il caricamento iniziale.
    -   **Output Editor Interno:** Se spuntato, il testo trascritto appare nell'editor dell'app. Altrimenti, viene inviato all'applicazione esterna attiva.
    -   **Registra Audio Debug:** Salva l'audio catturato in file `.wav` nella directory dei log.
    -   **Macro:** Definisci comandi vocali personalizzati che espandono testo predefinito (es. "firma" -> "Dr. Mario Rossi").
    -   **Vocabolario:** Inserisci termini specifici (uno per riga) per migliorare il riconoscimento.
    -   **Regole di Correzione Pronuncia:** Correggi parole che Whisper potrebbe interpretare male (es. "parlato" -> "scritto").

### Avvio e Arresto Trascrizione

-   Utilizza il grande pulsante **START** / **STOP** nella finestra principale.
-   Il pulsante START è abilitato solo se un profilo utente è attivo.
-   Durante il caricamento del modello (specialmente la prima volta o dopo un cambio), verrà mostrato uno spinner.

### Comandi Vocali

-   **Punteggiatura:** Se il modello Whisper (specialmente `large`) non inserisce la punteggiatura desiderata, puoi usare comandi vocali come "virgola", "punto", ecc. (definiti in `src/config.py` e gestiti da `TextProcessor`). La strategia attuale si affida principalmente a Whisper per la punteggiatura standard.
-   **"A capo" / "Nuova Riga":** Inserisce un ritorno a capo.
-   **"Paragrafo":** Inserisce un doppio ritorno a capo.
-   **"Ferma Dettatura" (e alias):** Arresta la trascrizione, equivalente a premere il pulsante STOP.
-   **Macro:** I comandi vocali definiti come trigger nelle macro del profilo attivo.

### Editor Interno ed Esterno

-   La modalità di output è definita nelle impostazioni del profilo attivo.
-   **Editor Interno:** Il testo appare nel campo di testo dell'applicazione. Può essere copiato o salvato in PDF.
-   **Applicazione Esterna:** Il testo viene "digitato" nell'applicazione che ha il focus al momento della trascrizione (es. un editor di testo, un'email, un browser). Assicurati che la finestra desiderata sia attiva.

### Salvataggio in PDF

Dal menu `File > Salva Editor come PDF...`, puoi salvare il contenuto corrente dell'editor interno in un file PDF.

## Architettura e Dettagli Tecnici

L'applicazione segue un'architettura modulare, separando la logica di business, l'interfaccia grafica e le utility. È stata implementata una base significativa in Python utilizzando PyQt6 per l'interfaccia grafica e Whisper per la trascrizione.

### Modulo Principale (`main.py`)

-   Punto di ingresso dell'applicazione (`if __name__ == '__main__':`).
-   Inizializza `QApplication`, `ProfileManager`, e `MainWindow`.
-   Gestisce l'avvio dell'event loop di Qt e la chiusura controllata dell'applicazione.
-   Include la gestione di base degli errori critici all'avvio.

### Configurazione (`config.py`)

-   Centralizza tutte le costanti globali, i percorsi dei file e delle directory, le impostazioni di default, i modelli Whisper disponibili, le mappe di comandi, e i parametri audio.
-   Determina dinamicamente i percorsi di salvataggio dei dati in base al sistema operativo (`~/Library/Application Support/NOME_APP/` su macOS).

### Logger (`utils/logger.py`)

-   Configura un logger standard Python (`logging`) per l'intera applicazione.
-   Permette la scrittura dei log sia su console (stdout) sia su file (`logs/app.log`).
-   Il formato e il livello di logging sono definiti in `config.py` e possono essere modificati tramite le impostazioni dell'app.

### Core Logic (`src/core/`)

Contiene la logica fondamentale dell'applicazione.

#### `profile_manager.py`

-   **Classe `ProfileManager`:**
    -   Logica per creare, caricare, salvare ed eliminare profili utente.
    -   Ogni profilo viene salvato come una serie di file JSON (settings.json, macros.json, vocabulary.json, pronunciation.json) in una sottocartella dedicata (dentro `~/Library/Application Support/TrascriviPro Avanzato/profiles/` su macOS).
    -   Gestisce anche le preferenze globali dell'applicazione (es. ultimo profilo usato, dispositivo audio, livello log), salvate in `preferences.json`.
    -   Utilizza `_get_available_profiles_internal()` per scansionare le cartelle dei profili e validarle.

#### `transcriber.py`

-   **Classe `Transcriber`:**
    -   Responsabile della cattura audio e della trascrizione.
    -   Utilizza `sounddevice` per accedere al microfono e catturare l'audio in blocchi.
    -   Mette i blocchi audio in una coda (`queue.Queue`).
    -   Un thread separato (`_process_audio_queue`) preleva l'audio dalla coda, lo accumula e lo invia a Whisper per la trascrizione quando vengono rilevate pause (silenzi) o quando il buffer raggiunge una dimensione massima.
    -   Carica e gestisce il modello Whisper (`whisper.load_model()`) utilizzando `self.model_lock` per la sincronizzazione.
    -   Implementa `reload_model_and_settings()` per aggiornare il modello e le impostazioni in base al profilo attivo.
    -   Utilizza il vocabolario personalizzato del profilo come `initial_prompt` per Whisper.
    -   Gestisce la registrazione opzionale dell'audio di debug in file `.wav`.
    -   Emette segnali (tramite callback) per nuove trascrizioni e aggiornamenti di stato.

#### `text_processor.py`

-   **Classe `TextProcessor`:**
    -   Riceve il testo grezzo trascritto da Whisper.
    -   Applica in sequenza:
        1.  Espansione delle **Macro** definite nel profilo attivo.
        2.  Applicazione delle **Regole di Correzione Pronuncia** definite nel profilo attivo.
        3.  Conversione delle parole chiave della **punteggiatura** e dei comandi "a capo" / "paragrafo" nei simboli/caratteri corretti.
        4.  Esegue una **capitalizzazione** di base (inizio frase, dopo punti di domanda/esclamativi, dopo newline).
        5.  Pulizia degli spazi superflui.
    -   Identifica **Comandi Speciali** (come "ferma dettatura") definiti in `config.py`.

#### `output_handler.py`

-   **Classe `OutputHandler`:**
    -   Gestisce l'invio del testo processato alla destinazione corretta.
    -   Può scrivere il testo processato nell'applicazione esterna attiva usando `pyautogui.typewrite()` (simulazione tastiera).
    -   Può scrivere il testo processato in un `QTextEdit` interno all'app.
    -   La modalità di output è configurabile per profilo.

### Interfaccia Grafica (`src/gui/`)

Costruita con PyQt6.

#### `main_window.py`

-   **Classe `MainWindow(QMainWindow)`:**
    -   Finestra principale dell'applicazione.
    -   Inizializza e coordina `ProfileManager`, `TextProcessor`, `OutputHandler`.
    -   Gestisce la creazione e il ciclo di vita del `TranscriptionThread`.
    -   Contiene i widget principali: pulsante START/STOP, etichetta di stato, combobox per i profili, editor interno.
    -   Crea e gestisce il menu dell'applicazione con accesso a: Gestione Profili, Impostazioni Profilo Attivo, Impostazioni App, Salva PDF, Info.
    -   Connette i segnali dell'interfaccia utente (click dei pulsanti, cambi nella combobox) alle azioni appropriate.
    -   Riceve segnali dal `TranscriptionThread` (nuova trascrizione, aggiornamenti di stato, errori) e aggiorna la UI di conseguenza.
    -   Implementa la logica per lo spinner di caricamento del modello.
    -   Gestisce la logica di abilitazione/disabilitazione dei controlli UI in base allo stato dell'applicazione (es. profilo caricato, trascrizione in corso).
    -   Include `_prepare_transcription_thread()` per una gestione robusta della creazione e pulizia dei thread di trascrizione.

#### `profile_dialogs.py`

Contiene le classi per i dialoghi modali utilizzati per la gestione dei profili e delle impostazioni:

-   **`ProfileManagementDialog`:** Per creare, eliminare, caricare, importare/esportare profili.
-   **`ProfileSettingsDialog`:** Per modificare le impostazioni del profilo attivo (modello, macro, vocabolario, ecc.).
-   **`AppSettingsDialog`:** Per configurare le impostazioni globali dell'app (dispositivo audio, livello di log). Utilizza `sounddevice.query_devices()` per popolare la lista dei microfoni disponibili.

### Gestione dei Thread

-   L'intera logica di cattura audio e trascrizione (`Transcriber`) viene eseguita in un `QThread` separato (`TranscriptionThread`) per evitare che l'interfaccia grafica si blocchi durante queste operazioni intensive.
-   La comunicazione tra `TranscriptionThread` e `MainWindow` avviene tramite segnali e slot Qt, un meccanismo sicuro per l'interazione tra thread in PyQt.
-   Viene utilizzata una `queue.Queue` per passare i dati audio dal callback di `sounddevice` (che viene eseguito in un thread di basso livello di `sounddevice`) al `_process_audio_queue` del `Transcriber` (che viene eseguito nel `TranscriptionThread`).
-   Un `threading.Lock` (`model_lock`) viene usato in `Transcriber` per proteggere l'accesso concorrente al modello Whisper durante il suo caricamento/ricaricamento.

### Persistenza Dati

-   **Profili Utente:** Salvati come cartelle e file JSON in `~/Library/Application Support/TrascriviPro Avanzato/profiles/`.
-   **Preferenze Applicazione:** Salvate come file JSON in `~/Library/Application Support/TrascriviPro Avanzato/preferences.json`.
-   **Log:** Salvati in `~/Library/Application Support/TrascriviPro Avanzato/logs/app.log`.
-   **Audio Debug:** File `.wav` salvati in `~/Library/Application Support/TrascriviPro Avanzato/logs/audio_debugs/`.

---

## Impacchettamento per macOS (Creazione App Installabile)

Per distribuire l'applicazione come un file `.app` stand-alone su macOS, utilizzeremo **PyInstaller**.

### Prerequisiti per l'Impacchettamento

-   Assicurati che l'applicazione funzioni correttamente eseguendola dall'ambiente virtuale.
-   Tutte le dipendenze devono essere installate nell'ambiente virtuale che userai per l'impacchettamento.

### Installazione di PyInstaller

Se non l'hai già fatto, installa PyInstaller nel tuo ambiente virtuale:

    pip install pyinstaller

### Creazione del File `.spec`

PyInstaller utilizza un file di specifica (`.spec`) per definire come l'applicazione deve essere impacchettata. È consigliabile generare un file `.spec` base e poi modificarlo, specialmente per applicazioni PyQt e quelle che usano modelli ML come Whisper.

1.  **Attiva il tuo ambiente virtuale.**
2.  **Naviga nella directory principale del progetto** (`TrascriviPro_Avanzato/`).
3.  **Esegui questo comando per generare un file `.spec` iniziale:**
    (Sostituisci `src/main.py` se il tuo entry point è diverso)

        pyi-makespec --windowed --name="TrascriviPro Avanzato" --icon="path/to/your/icon.icns" src/main.py

    *   `--windowed`: Indica che è un'applicazione GUI (non apre una console).
    *   `--name="TrascriviPro Avanzato"`: Il nome dell'app finale.
    *   `--icon="path/to/your/icon.icns"`: (Opzionale) Specifica un file icona `.icns` per l'app. Se non lo hai, puoi ometterlo per ora o crearlo successivamente.
    *   `src/main.py`: Il tuo script di ingresso principale.

    Questo creerà un file chiamato `TrascriviPro Avanzato.spec` (o simile) nella directory corrente.

### Modifica del File `.spec` (Cruciale)

Questo è il passo più importante e spesso richiede iterazioni. Apri il file `.spec` con un editor di testo. Dovrai probabilmente aggiungere o modificare le seguenti sezioni:

    # TrascriviPro Avanzato.spec

    # -*- mode: python ; coding: utf-8 -*-

    block_cipher = None

    a = Analysis(
        ['src/main.py'],  # Il tuo script di ingresso
        pathex=['/path/to/your/project/TrascriviPro_Avanzato'], # Percorso alla root del progetto
        binaries=[],
        datas=[
            # Includi la directory dei modelli di Whisper se non vengono trovati automaticamente
            # Il percorso esatto dei modelli dipende da come/dove Whisper li scarica.
            # Solitamente è in ~/.cache/whisper
            # Esempio (ADATTA QUESTO PERCORSO!):
            # ('/Users/TUO_UTENTE/.cache/whisper', 'whisper_models')
            #
            # Se hai altre risorse (immagini, file di dati non Python) che devono essere incluse:
            # ('path/to/your/resource_folder_in_src', 'destination_folder_name_in_app_bundle')
        ],
        hiddenimports=[
            'sounddevice', # Spesso necessario per sounddevice
            'pyautogui',
            'pynput', # Dipendenza di pyautogui, a volte necessaria esplicitarla
            '_sounddevice_data', # Potrebbe essere necessario
            # Aggiungi qui altri hidden imports che PyInstaller potrebbe non rilevare
            # Per PyQt6, di solito li rileva bene, ma controlla gli errori.
            'PyQt6.sip',
            'PyQt6.QtPrintSupport', # Se non viene incluso automaticamente
            'PyQt6.QtMultimedia', # Whisper o sounddevice potrebbero averne bisogno indirettamente
            # Per Whisper e le sue dipendenze (come Torch):
            'torch',
            'torchaudio',
            'torchvision', # Anche se non usato direttamente, a volte le installazioni di torch lo includono
            'whisper',
            'whisper.assets', # Se Whisper carica assets da lì
            'tiktoken_ext', # Per tiktoken, usato da Whisper
            # Dipendenze di Torch/Whisper che a volte sono problematiche
            'sklearn.utils._typedefs',
            'sklearn.neighbors._ball_tree',
            # ... e altre che potrebbero emergere durante il build o all'avvio dell'app
            # Controlla i log di build e gli errori all'avvio dell'app impacchettata.
        ],
        hookspath=[],
        hooksconfig={},
        runtime_hooks=[],
        excludes=[],
        win_no_prefer_redirects=False,
        win_private_assemblies=False,
        cipher=block_cipher,
        noarchive=False,
    )

    # --- AGGIUNTA IMPORTANTE per COLLETTARE I DATI DI WHISPER ---
    # Questa parte è cruciale se i modelli non vengono inclusi automaticamente.
    # Il modo più affidabile è trovare dove Whisper scarica i modelli
    # (di solito ~/.cache/whisper) e copiarli.
    # Tuttavia, whisper.load_model() dovrebbe scaricarli se non li trova al primo avvio dell'app impacchettata.
    # Un approccio alternativo è usare un hook per whisper.
    # Ma per iniziare, proviamo senza aggiunte complesse qui,
    # e se i modelli non caricano, rivediamo questa sezione.

    # --- Colleziona i dati per sounddevice se necessario ---
    # from PyInstaller.utils.hooks import collect_data_files
    # datas += collect_data_files('sounddevice', include_py_files=False)
    # datas += collect_data_files('openai-whisper', subdir='assets') # Per i file assets di Whisper


    pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,  # Assicurati che a.datas includa ciò che hai definito sopra
        [],
        name='TrascriviPro Avanzato',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True, # Se hai UPX installato e vuoi comprimere (opzionale)
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False, # False per app GUI
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None, # 'x86_64' o 'arm64' se vuoi forzare, altrimenti None per auto
        codesign_identity=None, # Per la firma del codice, vedi dopo
        entitlements_file=None, # Per la firma del codice, vedi dopo
        icon='path/to/your/icon.icns' # Ripeti l'icona qui
    )

    app = BUNDLE(
        exe,
        name='TrascriviPro Avanzato.app',
        icon='path/to/your/icon.icns', # E ancora qui per il bundle .app
        bundle_identifier=None, # Es: 'com.tuonome.trascriviproavanzato'
        # version='1.0.1' # Puoi specificare la versione qui
    )

**Note importanti sulla modifica del `.spec`:**

-   **`pathex`**: Assicurati che il percorso al tuo progetto sia corretto.
-   **`datas`**: Questa è la sezione per includere file non Python.
    -   **Modelli Whisper:** Il problema più comune con Whisper e PyInstaller è che i modelli non vengono inclusi. Whisper li scarica in `~/.cache/whisper`. PyInstaller non sa di questa directory.
        -   **Soluzione 1 (Raccomandata per Iniziare):** Non includere i modelli nel `datas`. Lascia che `whisper.load_model()` li scarichi al primo avvio dell'app impacchettata (l'utente vedrà il download). Questo mantiene il bundle dell'app più piccolo. L'app dovrà avere accesso a internet al primo avvio per scaricare il modello selezionato.
        -   **Soluzione 2 (Bundle più grande, offline):** Se vuoi includere i modelli:
            1.  Trova la directory `~/.cache/whisper`.
            2.  Aggiungi una tupla a `datas`: `('/Users/TUO_UTENTE/.cache/whisper', 'whisper_models_cache')`.
            3.  Poi, nel tuo codice Python (ad esempio in `config.py` o all'avvio del `Transcriber`), dovrai dire a Whisper di cercare i modelli in questa cartella impacchettata. Questo si può fare impostando la variabile d'ambiente `XDG_CACHE_HOME` _prima_ di importare `whisper`, in modo che punti a una sottodirectory dentro il bundle dell'app. Questo è più complesso.

                Esempio in `config.py` o `main.py` prima degli import di `whisper`:
                import os
                import sys
                if getattr(sys, 'frozen', False): # Se l'app è impacchettata
                    # Percorso relativo alla directory dei modelli impacchettata
                    application_path = os.path.dirname(sys.executable)
                    if sys.platform == "darwin": # macOS
                        # All'interno del bundle .app, sys.executable è in Contents/MacOS/
                        # Quindi dobbiamo salire di alcuni livelli per raggiungere Contents/Resources (ipotetico)
                        # o la root del bundle. È più semplice copiare i modelli nella stessa dir dell'eseguibile
                        # o in una sottodir ben definita se usi `datas`.
                        # Se hai ('/Users/TUO_UTENTE/.cache/whisper', 'whisper_models_cache') in datas,
                        # il percorso dentro l'app sarà 'whisper_models_cache'.
                        # models_dir_in_app = os.path.join(application_path, '..', 'Resources', 'whisper_models_cache') # Esempio con Resources
                        # Oppure se copiato vicino all'eseguibile:
                        # models_dir_in_app = os.path.join(application_path, 'whisper_models_cache')

                        # Whisper usa XDG_CACHE_HOME per trovare ~/.cache/whisper
                        # Potremmo dover sovrascrivere il percorso di download di whisper.
                        # os.environ['XDG_CACHE_HOME'] = os.path.join(application_path, 'cache_simulata')
                        # if not os.path.exists(os.path.join(os.environ['XDG_CACHE_HOME'], 'whisper')):
                        #    os.makedirs(os.path.join(os.environ['XDG_CACHE_HOME'], 'whisper'))
                        # Più semplicemente, si può passare `download_root` a `whisper.load_model(..., download_root=models_dir_in_app)`
                        # Questo richiede modifica a transcriber.py

            Per ora, consiglio la Soluzione 1 (download al primo avvio).
-   **`hiddenimports`**: Elenca qui i moduli che PyInstaller potrebbe non rilevare automaticamente. `sounddevice`, `_sounddevice_data`, `PyQt6.QtPrintSupport` sono candidati comuni. Per Whisper e Torch, potrebbero essercene molti; dovrai aggiungerli se l'app impacchettata dà errori di `ModuleNotFoundError`.
-   **`collect_data_files`**: A volte utile per pacchetti come `sounddevice` o `openai-whisper` se hanno file di dati non Python. Decommenta e adatta se necessario.
-   **`icon`**: Fornisci il percorso al tuo file `.icns`.
-   **`target_arch`**: Su macOS moderni, potresti voler creare build separate per `x86_64` (Intel) e `arm64` (Apple Silicon) o una build universale (più complessa con PyInstaller, solitamente richiede la compilazione separata e l'uso di `lipo`). Per iniziare, `None` lascerà che PyInstaller scelga l'architettura della macchina su cui stai compilando.

### Esecuzione di PyInstaller con il File `.spec`

Una volta che il file `.spec` è configurato:

1.  **Attiva il tuo ambiente virtuale.**
2.  **Naviga nella directory principale del progetto.**
3.  **Esegui PyInstaller:**
    `pyinstaller "TrascriviPro Avanzato.spec" --noconfirm`
    -   `--noconfirm`: Sovrascrive la directory `dist` e `build` senza chiedere.

    PyInstaller creerà una directory `build` (file temporanei) e una directory `dist`. All'interno di `dist`, troverai `TrascriviPro Avanzato.app`.

### Verifica e Distribuzione dell'App

1.  **Verifica:**
    -   Prova ad eseguire `TrascriviPro Avanzato.app` dalla directory `dist`.
    -   Testa tutte le funzionalità.
    -   Controlla se ci sono errori nella console all'avvio (puoi avviare l'app dal terminale per vedere l'output: `open dist/"TrascriviPro Avanzato.app" --args -c` o direttamente `./dist/"TrascriviPro Avanzato.app/Contents/MacOS/TrascriviPro Avanzato"`).
    -   **Permessi macOS:** La prima volta che l'app tenta di accedere al microfono o inviare input ad altre app, macOS chiederà i permessi. Questo è normale.
    -   **Caricamento Modelli Whisper:** Se non hai incluso i modelli, al primo avvio di una trascrizione con un nuovo modello, dovresti vedere un messaggio o un log che indica il download.
2.  **Risoluzione Problemi Comuni:**
    -   **`ModuleNotFoundError`**: Aggiungi il modulo mancante a `hiddenimports` nel file `.spec` e ricompila.
    -   **File non trovati (es. modelli Whisper, icone, dati)**: Assicurati che siano inclusi correttamente in `datas` nel file `.spec` o che il codice li cerchi nel posto giusto all'interno del bundle dell'app. Ricorda che i percorsi cambiano quando l'app è impacchettata. Usa `sys._MEIPASS` per accedere ai file inclusi nel bundle temporaneo durante l'esecuzione (se usi `--onedir` o `--onefile`).
    -   **Problemi con `sounddevice` o audio**: Assicurati che `ffmpeg` e `portaudio` siano accessibili o, se possibile, considera di impacchettarli (più complesso).
    -   **Librerie Dinamiche (`.dylib`) non trovate**: A volte PyInstaller non copia tutte le librerie necessarie, specialmente quelle di C/C++. Potrebbe essere necessario aggiungerle manualmente in `binaries` nel file `.spec` o usare `install_name_tool` per correggere i percorsi delle librerie.
3.  **Distribuzione:**
    -   Una volta che l'app `.app` funziona correttamente, puoi comprimerla in un file `.zip` o creare un'immagine disco `.dmg` per una distribuzione più professionale.
    -   Per creare un `.dmg`, puoi usare Utility Disco su macOS o strumenti da riga di comando come `hdiutil`. Esistono anche script o strumenti di terze parti che automatizzano questo processo (es. `create-dmg`).

### Icona dell'Applicazione (Opzionale ma Raccomandato)

1.  Crea un'icona in formato `.icns`. Puoi usare strumenti come "Image2Icon" o "Icon Composer" (parte di Xcode Graphics Tools), o convertire un'immagine PNG di alta risoluzione (es. 1024x1024px).
2.  Specifica il percorso al tuo file `.icns` nelle opzioni `--icon` di `pyi-makespec` e nelle sezioni `icon` di `EXE` e `BUNDLE` nel file `.spec`.

### Firma del Codice (Opzionale ma Raccomandato per Distribuzione)

Per evitare avvisi di sicurezza di Gatekeeper su macOS quando altri utenti scaricano la tua app, dovresti firmare l'applicazione con un Apple Developer ID.

1.  Avrai bisogno di un account Apple Developer Program.
2.  Una volta ottenuto un certificato "Developer ID Application", puoi specificarlo in `codesign_identity` nel file `.spec`.
    # Nel file .spec, dentro EXE:
    # codesign_identity='Developer ID Application: Tuo Nome (TEAMID)',
    # entitlements_file='entitlements.plist', # File opzionale per permessi specifici
3.  PyInstaller tenterà di firmare l'app durante il processo di build.
4.  Dopo la creazione del `.app`, puoi anche "notarizzare" l'app con Apple, un processo automatico che scansiona l'app alla ricerca di malware e, se superato, riduce ulteriormente gli avvisi di Gatekeeper.

Questo processo di firma e notarizzazione è più avanzato e non strettamente necessario se l'app è solo per uso personale o per utenti che sanno come bypassare gli avvisi di Gatekeeper.

---

## Troubleshooting e Problemi Noti

-   **Output Esterno (`pyautogui`):** Richiede una verifica approfondita dei permessi di Accessibilità su macOS per garantire il funzionamento. Attualmente, il testo viene trascritto e inviato a `pyautogui`, ma potrebbe non apparire nell'applicazione esterna se i permessi non sono corretti o se ci sono problemi di focus.
-   **Reattività "Tempo Reale":** L'output del testo avviene a segmenti (dopo pause o ogni tot secondi di parlato continuo). Un output parola per parola istantaneo con l'attuale libreria Whisper è complesso e non implementato. Le soglie attuali nel `Transcriber` cercano un bilanciamento.
-   **Comandi Vocali di Start:** Il comando vocale per avviare la trascrizione non è implementato (richiederebbe un ascolto costante di parole chiave, separato dal flusso principale di Whisper). Il comando di stop è parzialmente gestito.
-   **Rifinitura GUI:** Le interfacce per la gestione delle tabelle (macro, pronunce) potrebbero essere rese più user-friendly.
-   **Packaging e Distribuzione:** Il processo di creazione di un `.app` standalone con PyInstaller (o simili) che includa tutte le dipendenze (Python, PyQt6, PyTorch, Whisper, modelli) necessita di essere creato, testato e debuggato.
-   **Allucinazioni di Whisper / Punteggiatura / Token Speciali (`<|zh|>`)**:
    -   **Causa:** Modelli più piccoli (`tiny`, `base`, `small`) sono più inclini a errori. Pause lunghe, rumore, o audio poco chiaro possono confondere il modello. A volte Whisper rileva erroneamente segmenti in altre lingue o genera token speciali.
    -   **Soluzione:** Utilizzare modelli Whisper più grandi (`medium`, `large`) migliora significativamente l'accuratezza e la gestione della punteggiatura. Assicurare un input audio chiaro. Il `TextProcessor` pulisce alcuni token speciali.
    -   **Debug:** Attivare "Registra audio per debug" nelle impostazioni del profilo per analizzare i file `.wav` che causano problemi.
-   **Errore `OMP: Error #15: Initializing libiomp5.dylib, but found libomp.dylib already initialized.` (macOS):**
    -   **Causa:** Conflitto tra librerie OpenMP usate da PyTorch.
    -   **Soluzione:** A volte impostare `os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'` all'inizio di `main.py` può aiutare, ma è un workaround. La soluzione migliore è assicurarsi che le versioni di PyTorch e delle sue dipendenze siano compatibili.
-   **L'applicazione impacchettata non si avvia o crasha subito:**
    -   **Causa:** Spesso `ModuleNotFoundError` o file di dati mancanti.
    -   **Soluzione:** Controlla attentamente i log di build di PyInstaller e avvia l'app impacchettata dal terminale per vedere l'output di errore. Aggiungi `hiddenimports` o `datas` necessari al file `.spec`.
-   **Permessi macOS:** L'app richiederà permessi per il microfono e l'accessibilità (per `pyautogui`). L'utente dovrà concederli tramite le Preferenze di Sistema.

## Possibili Miglioramenti Futuri

-   **I. Miglioramenti Trascrizione/Accuratezza:**
    -   Implementare la Calibrazione Audio Assistita per aiutare gli utenti a popolare vocabolario e regole di pronuncia.
    -   Aggiungere Feedback Visivo della Voce (waveform/livello input) nella GUI.
    -   Considerare Soppressione del Rumore se necessario.
    -   Selezione Lingua Dinamica: Permettere a Whisper di rilevare automaticamente la lingua o fornire un menu più ampio di lingue supportate.
    -   Supporto `initial_prompt`: Permettere all'utente di specificare un `initial_prompt` per Whisper per migliorare ulteriormente l'accuratezza in contesti specifici.
-   **II. Funzionalità Testo/Comandi Avanzate:**
    -   Implementare Comandi Vocali di Formattazione Avanzati ("maiuscola X", "cancella ultima parola", ecc.).
    -   Implementare la "Modalità Comando" vs "Modalità Dettatura".
    -   Esplorare il supporto per Template/Campi da Compilare (molto complesso).
    -   Opzioni di formattazione più avanzate (es. grassetto, corsivo tramite comandi vocali).
    -   Un sistema di regole di punteggiatura più sofisticato se quello automatico di Whisper non è sufficiente per tutti i casi d'uso.
-   **III. Miglioramenti UI/UX:**
    -   Rifinare ulteriormente le GUI di gestione delle impostazioni (tabelle più interattive, validazione).
    -   Aggiungere Temi Personalizzabili (chiaro/scuro).
    -   Creare un Tutorial/Guida Rapida Integrata.
    -   Migliorare il feedback durante operazioni lunghe (es. download modelli Whisper).
    -   Aggiungere Notifiche di Sistema.
    -   Predisporre per Internazionalizzazione (i18n).
-   **IV. Packaging e Distribuzione:**
    -   Testare e finalizzare lo script di packaging con PyInstaller per creare un .app standalone affidabile per macOS.
    -   Creare un .dmg per una facile distribuzione.
    -   (Opzionale, per distribuzione ampia) Investigare la firma del codice e la notarizzazione Apple.
    -   Supporto Multi-Piattaforma: Estendere e testare l'applicazione per Windows e Linux.
-   **V. Altri Sviluppi:**
    -   Test Automatici: Implementazione di unit test e test di integrazione per migliorare la robustezza.
    -   Utilizzo di `whisper.cpp`: Per una potenziale maggiore efficienza e minori dipendenze rispetto alla versione Python di Whisper, anche se l'integrazione sarebbe più complessa.
    -   Plugin o API per Estensioni: Per permettere l'integrazione di funzionalità di terze parti.

## Contributi

Invitiamo a contribuire allo sviluppo di TrascriviPro Avanzato tramite pull request su GitHub per nuove funzionalità o correzioni di bug, o segnalando problemi tramite l'issue tracker.

# TrascriviPro Avanzato

**Versione:** 1.0.1 (come da `src/config.py`)
**Data Ultimo Aggiornamento Significativo:** 2024-05-20
**Autore:** [Il tuo nome o nome dell'organizzazione]

## Indice

1.  [Descrizione Generale](#descrizione-generale)
2.  [Funzionalità Principali](#funzionalità-principali)
3.  [Tecnologie Utilizzate](#tecnologie-utilizzate)
4.  [Struttura del Progetto](#struttura-del-progetto)
5.  [Installazione e Avvio](#installazione-e-avvio)
    - [5.1. Prerequisiti (per macOS, ambiente di sviluppo)](#51-prerequisiti-per-macos-ambiente-di-sviluppo)
    - [5.2. Creazione Ambiente Virtuale e Installazione Dipendenze (macOS)](#52-creazione-ambiente-virtuale-e-installazione-dipendenze-macos)
    - [5.3. Avvio dell'Applicazione (macOS, da sorgente)](#53-avvio-dellapplicazione-macos-da-sorgente)
    - [X. Note per l'Esecuzione su Windows (da Sorgente, Sperimentale)](#x-note-per-lesecuzione-su-windows-da-sorgente-sperimentale)
6.  [Guida all'Uso](#guida-alluso)
    - [Profili Utente](#profili-utente)
    - [Avvio e Arresto Trascrizione](#avvio-e-arresto-trascrizione)
    - [Comandi Vocali](#comandi-vocali)
    - [Editor Interno ed Esterno](#editor-interno-ed-esterno)
    - [Salvataggio in PDF](#salvataggio-in-pdf)
7.  [Architettura e Dettagli Tecnici](#architettura-e-dettagli-tecnici)
    - [Modulo Principale (`main.py`)](#modulo-principale-mainpy)
    - [Configurazione (`config.py`)](#configurazione-configpy)
    - [Logger (`utils/logger.py`)](#logger-utilsloggerpy)
    - [Core Logic (`src/core/`)](#core-logic-srccore)
      - [`profile_manager.py`](#profile_managerpy)
      - [`transcriber.py`](#transcriberpy)
      - [`text_processor.py`](#text_processorpy)
      - [`output_handler.py`](#output_handlerpy)
    - [Interfaccia Grafica (`src/gui/`)](#interfaccia-grafica-srcgui)
      - [`main_window.py`](#main_windowpy)
      - [`profile_dialogs.py`](#profile_dialogspy)
    - [Gestione dei Thread](#gestione-dei-thread)
    - [Persistenza Dati](#persistenza-dati)
8.  [Impacchettamento per macOS (Creazione App Installabile)](#impacchettamento-per-macos-creazione-app-installabile)
    - [Prerequisiti per l'Impacchettamento](#prerequisiti-per-limpacchettamento)
    - [Installazione di PyInstaller](#installazione-di-pyinstaller)
    - [Creazione del File `.spec`](#creazione-del-file-spec)
    - [Modifica del File `.spec` (Cruciale)](#modifica-del-file-spec-cruciale)
    - [Esecuzione di PyInstaller con il File `.spec`](#esecuzione-di-pyinstaller-con-il-file-spec)
    - [Verifica e Distribuzione dell'App](#verifica-e-distribuzione-dellapp)
    - [Icona dell'Applicazione (Opzionale ma Raccomandato)](#icona-dellapplicazione-opzionale-ma-raccomandato)
    - [Firma del Codice (Opzionale ma Raccomandato per Distribuzione)](#firma-del-codice-opzionale-ma-raccomandato-per-distribuzione)
9.  [Troubleshooting e Problemi Noti](#troubleshooting-e-problemi-noti)
10. [Possibili Miglioramenti Futuri](#possibili-miglioramenti-futuri)
11. [Contributi](#contributi)
12. [Licenza](#licenza)

---

## Descrizione Generale

**TrascriviPro Avanzato** è un'applicazione desktop per macOS progettata per offrire una soluzione di trascrizione vocale in tempo reale, locale e altamente personalizzabile. Sfruttando la potenza del modello Whisper di OpenAI (eseguito localmente per garantire la privacy), l'applicazione permette agli utenti di dettare testo direttamente in applicazioni esterne o in un editor integrato, con supporto per comandi vocali, profili utente multipli e un'ampia gamma di personalizzazioni.

L'obiettivo generale è fornire agli utenti macOS uno strumento di dettatura potente e flessibile che permetta di trasformare rapidamente il parlato in testo scritto, mantenendo il controllo completo sui propri dati e sulle impostazioni di trascrizione.

## Funzionalità Principali

-   **Trascrizione Vocale Locale in Tempo Reale:** Converte il parlato dell'utente in testo utilizzando `openai-whisper` per la trascrizione offline, garantendo privacy e nessun costo per API esterne. L'output del testo avviene a segmenti (dopo pause o ogni tot secondi di parlato continuo), non parola per parola istantaneamente.
-   **Output Flessibile:**
    -   Trascrizione diretta in qualsiasi applicazione esterna attiva (es. editor di testo, software di refertazione) tramite simulazione tastiera (`pyautogui`).
    -   Editor di testo integrato per la visualizzazione e la modifica del testo trascritto.
-   **Comandi Vocali:**
    -   Dettatura della punteggiatura (es. "virgola", "punto") che viene convertita nei simboli appropriati.
    -   Utilizzo di comandi di formattazione come "a capo", "nuova riga", "paragrafo".
    -   Comandi speciali come "ferma dettatura" per arrestare la trascrizione.
    -   Supporto futuro per comandi vocali di avvio della trascrizione.
-   **Personalizzazione Avanzata tramite Profili Utente:**
    -   Ogni utente può creare e gestire più profili con impostazioni personalizzate.
    -   Ogni profilo memorizza impostazioni specifiche per:
        -   **Macro (AutoText):** Comandi vocali personalizzati per inserire rapidamente blocchi di testo predefiniti.
        -   **Vocabolario Personalizzato:** Un elenco di parole/frasi (es. termini medici, tecnici) per migliorare l'accuratezza del riconoscimento di Whisper.
        -   **Regole di Correzione Pronuncia:** Mappature "testo parlato" -> "testo da scrivere" per correggere difetti di pronuncia o usare abbreviazioni.
        -   **Preferenze del modello Whisper** (es. tiny, base, small, medium, large).
        -   **Preferenza per l'output** (editor interno vs. esterno).
        -   Abilitazione della **registrazione audio opzionale per debug**.
-   **Import/Export Profili:** Facile condivisione e backup dei profili utente tramite file JSON (salvati in sottocartelle dedicate dentro la directory di supporto dell'app).
-   **Salvataggio in PDF:** Il testo dall'editor interno può essere esportato in formato PDF.
-   **Logging Dettagliato:** Registrazione dettagliata delle operazioni dell'app su file e console.
-   **Selezione del Dispositivo di Input Audio:** Possibilità di scegliere il microfono desiderato.

## Tecnologie Utilizzate

-   **Python:** Linguaggio di programmazione principale (versione 3.9+ raccomandata).
-   **PyQt6:** Framework per la creazione dell'interfaccia grafica utente (GUI).
-   **`openai-whisper`:** Libreria per la trascrizione vocale automatica (ASR) basata sui modelli Whisper di OpenAI, eseguita localmente.
-   **`sounddevice`:** Libreria per la cattura e la riproduzione audio multipiattaforma.
-   **`pyautogui`:** Libreria per controllare mouse e tastiera, utilizzata per inviare testo ad applicazioni esterne (richiede permessi di Accessibilità su macOS).
-   **JSON:** Formato utilizzato per il salvataggio dei profili utente, delle preferenze dell'applicazione e delle configurazioni.
-   **NumPy:** Utilizzata da `sounddevice` e `whisper` per la manipolazione di array numerici (audio).
-   **Wave:** Modulo standard Python per la lettura e scrittura di file audio `.wav`.

## Struttura del Progetto

La struttura principale del progetto è organizzata come segue:

    TrascriviPro_Avanzato/
    ├── src/                     # Codice sorgente dell'applicazione
    │   ├── __init__.py
    │   ├── main.py              # Punto di ingresso dell'applicazione
    │   ├── config.py            # Configurazioni globali, costanti, percorsi
    │   ├── core/                # Logica di business e funzionalità centrali
    │   │   ├── __init__.py
    │   │   ├── profile_manager.py # Gestione dei profili utente
    │   │   ├── transcriber.py     # Logica di cattura audio e trascrizione Whisper
    │   │   ├── text_processor.py  # Elaborazione testo (macro, comandi, punteggiatura)
    │   │   └── output_handler.py  # Gestione output testo (editor interno/esterno)
    │   ├── gui/                 # Componenti dell'interfaccia grafica (PyQt6)
    │   │   ├── __init__.py
    │   │   ├── main_window.py     # Finestra principale dell'applicazione
    │   │   └── profile_dialogs.py # Dialoghi per gestione profili e impostazioni
    │   └── utils/               # Utility varie (es. logger)
    │       ├── __init__.py
    │       └── logger.py          # Configurazione del sistema di logging
    ├── profiles/                # NON nel repository; directory creata in Application Support per i dati dei profili
    ├── logs/                    # NON nel repository; directory creata in Application Support per i file di log e debug audio
    ├── README.md                # Questo file
    └── requirements.txt         # File con le dipendenze del progetto
    └── setup_macos.spec         # (Dopo creazione) File di specifica per PyInstaller

Le directory `profiles/` e `logs/` vengono create dinamicamente dall'applicazione nella directory di supporto appropriata per macOS (`~/Library/Application Support/TrascriviPro Avanzato/`).

## 5. Installazione e Avvio

Questa applicazione è stata sviluppata e ottimizzata con l'obiettivo di diventare un'applicazione `.app` **installabile e nativa per macOS**. Le istruzioni seguenti si riferiscono all'esecuzione del codice sorgente in un ambiente di sviluppo, principalmente su macOS.

### 5.1. Prerequisiti (per macOS, ambiente di sviluppo)

-   **macOS:** L'ambiente di sviluppo e test primario.
-   **Python:** Versione 3.9 o superiore. Puoi verificarlo con `python3 --version`.
-   **Pip:** Gestore di pacchetti Python, solitamente installato con Python.
-   **FFmpeg:** Whisper richiede FFmpeg per la gestione dei formati audio.
    -   Installazione tramite [Homebrew](https://brew.sh/index_it) (consigliato su macOS):
        `brew install ffmpeg`
-   **PortAudio:** `sounddevice` dipende da PortAudio. Su macOS, di solito è gestito correttamente. Se necessario:
    `brew install portaudio`

### 5.2. Creazione Ambiente Virtuale e Installazione Dipendenze (macOS)

Per mantenere le dipendenze del progetto isolate, consiglio caldamente di usare un ambiente virtuale.

1.  **Clona il Repository:**
    `git clone https://github.com/Alexinfotech/trascrizione-facile.git`
    `cd trascrizione-facile`
2.  **Crea un ambiente virtuale** (lo chiamo `venv`):
    `python3 -m venv venv`
3.  **Attiva l'ambiente virtuale:**
    `source venv/bin/activate`
    (Il prompt del terminale mostrerà `(venv)` all'inizio).
4.  **Installa le dipendenze** dal file `requirements.txt`:
    `pip install -r requirements.txt`
    *Il file `requirements.txt` contiene tutte le librerie necessarie come PyQt6, openai-whisper, torch, torchaudio, sounddevice, pyautogui, e numpy.*

### 5.3. Avvio dell'Applicazione (macOS, da sorgente)

Con l'ambiente virtuale attivato e le dipendenze installate, dalla directory principale del progetto (`trascrizione-facile/`):
`python -m src.main`

L'applicazione dovrebbe avviarsi. I log verranno stampati sulla console e salvati nel file `app.log` nella directory di supporto dell'applicazione (`~/Library/Application Support/TrascriviPro Avanzato/logs/` su macOS).

### X. Note per l'Esecuzione su Windows (da Sorgente, Sperimentale)

Sebbene questa applicazione sia stata progettata e ottimizzata primariamente per macOS con l'intento di creare un'app .app installabile, è teoricamente possibile eseguire il codice sorgente anche su Windows. Tuttavia, questo richiede una configurazione manuale più complessa e non è garantito che tutte le funzionalità si comportino esattamente come su macOS senza specifici test e adattamenti.

Se desideri provare ad eseguire l'applicazione da sorgente su un PC Windows utilizzando, ad esempio, Visual Studio Code:

1.  **Clona il Repository su Windows:**
    `git clone https://github.com/Alexinfotech/trascrizione-facile.git`
    `cd trascrizione-facile`
2.  **Configura un Ambiente Python su Windows:**
    -   Installa Python 3.9+ per Windows da python.org (assicurati di aggiungere Python al PATH).
    -   Crea un ambiente virtuale:
        `python -m venv venv`
    -   Attiva l'ambiente virtuale (il comando è diverso su Windows):
        `.\venv\Scripts\activate`
3.  **Installa le Dipendenze Critiche per Windows:**
    -   **FFmpeg per Windows:**
        -   Scarica i binari di FFmpeg per Windows (es. da gyan.dev). Scegli una release build (non la nightly).
        -   Estrai l'archivio (es. in `C:\ffmpeg`).
        -   Aggiungi la cartella `bin` di FFmpeg (es. `C:\ffmpeg\bin`) al PATH di sistema di Windows. In alternativa, puoi copiare `ffmpeg.exe`, `ffplay.exe`, `ffprobe.exe` nella stessa cartella dello script Python principale o in una cartella già nel PATH. Questo è cruciale per Whisper.
    -   **PyTorch e Torchaudio per Windows:** L'installazione di PyTorch può essere specifica. Visita il sito ufficiale di PyTorch e usa il configuratore per ottenere il comando pip corretto per la tua configurazione (es. CPU-only o con supporto CUDA se hai una GPU NVIDIA).
        -   Esempio per CPU-only (verifica sempre sul sito di PyTorch per il comando più aggiornato):
            `pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu`
    -   **Altre Dipendenze Python:** Installa il resto delle dipendenze da `requirements.txt` (se hai adattato PyTorch) o manualmente:
        `pip install PyQt6 openai-whisper sounddevice pyautogui numpy`
        *(Se `requirements.txt` include una versione specifica di torch/torchaudio non adatta a Windows, installale separatamente come sopra e poi installa il resto).*
4.  **Esegui l'Applicazione:**
    -   Dal terminale (con l'ambiente virtuale attivo):
        `python -m src.main`
**Potenziali Aree di Modifica/Verifica per Windows:**
-   **Percorsi File:** La logica in `src/config.py` per `APP_BASE_DATA_PATH` tenta già di gestire Windows usando `%APPDATA%`. Verifica che i profili e i log vengano creati e letti correttamente (solitamente in `C:\Users\TUO_UTENTE\AppData\Roaming\TrascriviPro Avanzato\`).
-   **`sounddevice`:** La selezione del microfono e il suo funzionamento potrebbero richiedere verifiche.
-   **`pyautogui`:** L'interazione con altre applicazioni (output esterno) va testata. Potrebbe funzionare senza i permessi di Accessibilità richiesti da macOS, ma UAC o antivirus potrebbero interferire.
-   **Estetica GUI:** Piccole differenze visive sono normali tra macOS e Windows con PyQt6.
-   **Librerie C++ Ridistribuibili:** Alcune dipendenze potrebbero richiedere l'installazione di specifici pacchetti ridistribuibili di Microsoft Visual C++ se non già presenti.

## Guida all'Uso

### Profili Utente

-   **Gestione Profili:** Accedi dal menu `File > Gestisci Profili...` o dal pulsante "Gestisci Profili..." nella finestra principale.
    -   **Crea:** Inserisci un nome per un nuovo profilo. Verrà creato con impostazioni di default.
    -   **Carica:** Seleziona un profilo dalla lista e clicca "Carica Selezionato e Chiudi" (o doppio click) per attivarlo.
    -   **Elimina:** Rimuove permanentemente un profilo selezionato.
    -   **Importa/Esporta:** Permette di salvare un profilo in un file `.zip` o di importarne uno da un file `.zip`.
-   **Impostazioni Profilo Attivo:** Accedi dal menu `File > Impostazioni Profilo Attivo...`. Qui puoi configurare:
    -   **Nome Visualizzato:** Modifica il nome del profilo.
    -   **Modello Whisper:** Scegli la dimensione del modello (da `tiny` a `large`). Modelli più grandi sono più accurati ma richiedono più risorse e tempo per il caricamento iniziale.
    -   **Output Editor Interno:** Se spuntato, il testo trascritto appare nell'editor dell'app. Altrimenti, viene inviato all'applicazione esterna attiva.
    -   **Registra Audio Debug:** Salva l'audio catturato in file `.wav` nella directory dei log.
    -   **Macro:** Definisci comandi vocali personalizzati che espandono testo predefinito (es. "firma" -> "Dr. Mario Rossi").
    -   **Vocabolario:** Inserisci termini specifici (uno per riga) per migliorare il riconoscimento.
    -   **Regole di Correzione Pronuncia:** Correggi parole che Whisper potrebbe interpretare male (es. "parlato" -> "scritto").

### Avvio e Arresto Trascrizione

-   Utilizza il grande pulsante **START** / **STOP** nella finestra principale.
-   Il pulsante START è abilitato solo se un profilo utente è attivo.
-   Durante il caricamento del modello (specialmente la prima volta o dopo un cambio), verrà mostrato uno spinner.

### Comandi Vocali

-   **Punteggiatura:** Se il modello Whisper (specialmente `large`) non inserisce la punteggiatura desiderata, puoi usare comandi vocali come "virgola", "punto", ecc. (definiti in `src/config.py` e gestiti da `TextProcessor`). La strategia attuale si affida principalmente a Whisper per la punteggiatura standard.
-   **"A capo" / "Nuova Riga":** Inserisce un ritorno a capo.
-   **"Paragrafo":** Inserisce un doppio ritorno a capo.
-   **"Ferma Dettatura" (e alias):** Arresta la trascrizione, equivalente a premere il pulsante STOP.
-   **Macro:** I comandi vocali definiti come trigger nelle macro del profilo attivo.

### Editor Interno ed Esterno

-   La modalità di output è definita nelle impostazioni del profilo attivo.
-   **Editor Interno:** Il testo appare nel campo di testo dell'applicazione. Può essere copiato o salvato in PDF.
-   **Applicazione Esterna:** Il testo viene "digitato" nell'applicazione che ha il focus al momento della trascrizione (es. un editor di testo, un'email, un browser). Assicurati che la finestra desiderata sia attiva.

### Salvataggio in PDF

Dal menu `File > Salva Editor come PDF...`, puoi salvare il contenuto corrente dell'editor interno in un file PDF.

## Architettura e Dettagli Tecnici

L'applicazione segue un'architettura modulare, separando la logica di business, l'interfaccia grafica e le utility. È stata implementata una base significativa in Python utilizzando PyQt6 per l'interfaccia grafica e Whisper per la trascrizione.

### Modulo Principale (`main.py`)

-   Punto di ingresso dell'applicazione (`if __name__ == '__main__':`).
-   Inizializza `QApplication`, `ProfileManager`, e `MainWindow`.
-   Gestisce l'avvio dell'event loop di Qt e la chiusura controllata dell'applicazione.
-   Include la gestione di base degli errori critici all'avvio.

### Configurazione (`config.py`)

-   Centralizza tutte le costanti globali, i percorsi dei file e delle directory, le impostazioni di default, i modelli Whisper disponibili, le mappe di comandi, e i parametri audio.
-   Determina dinamicamente i percorsi di salvataggio dei dati in base al sistema operativo (`~/Library/Application Support/NOME_APP/` su macOS).

### Logger (`utils/logger.py`)

-   Configura un logger standard Python (`logging`) per l'intera applicazione.
-   Permette la scrittura dei log sia su console (stdout) sia su file (`logs/app.log`).
-   Il formato e il livello di logging sono definiti in `config.py` e possono essere modificati tramite le impostazioni dell'app.

### Core Logic (`src/core/`)

Contiene la logica fondamentale dell'applicazione.

#### `profile_manager.py`

-   **Classe `ProfileManager`:**
    -   Logica per creare, caricare, salvare ed eliminare profili utente.
    -   Ogni profilo viene salvato come una serie di file JSON (settings.json, macros.json, vocabulary.json, pronunciation.json) in una sottocartella dedicata (dentro `~/Library/Application Support/TrascriviPro Avanzato/profiles/` su macOS).
    -   Gestisce anche le preferenze globali dell'applicazione (es. ultimo profilo usato, dispositivo audio, livello log), salvate in `preferences.json`.
    -   Utilizza `_get_available_profiles_internal()` per scansionare le cartelle dei profili e validarle.

#### `transcriber.py`

-   **Classe `Transcriber`:**
    -   Responsabile della cattura audio e della trascrizione.
    -   Utilizza `sounddevice` per accedere al microfono e catturare l'audio in blocchi.
    -   Mette i blocchi audio in una coda (`queue.Queue`).
    -   Un thread separato (`_process_audio_queue`) preleva l'audio dalla coda, lo accumula e lo invia a Whisper per la trascrizione quando vengono rilevate pause (silenzi) o quando il buffer raggiunge una dimensione massima.
    -   Carica e gestisce il modello Whisper (`whisper.load_model()`) utilizzando `self.model_lock` per la sincronizzazione.
    -   Implementa `reload_model_and_settings()` per aggiornare il modello e le impostazioni in base al profilo attivo.
    -   Utilizza il vocabolario personalizzato del profilo come `initial_prompt` per Whisper.
    -   Gestisce la registrazione opzionale dell'audio di debug in file `.wav`.
    -   Emette segnali (tramite callback) per nuove trascrizioni e aggiornamenti di stato.

#### `text_processor.py`

-   **Classe `TextProcessor`:**
    -   Riceve il testo grezzo trascritto da Whisper.
    -   Applica in sequenza:
        1.  Espansione delle **Macro** definite nel profilo attivo.
        2.  Applicazione delle **Regole di Correzione Pronuncia** definite nel profilo attivo.
        3.  Conversione delle parole chiave della **punteggiatura** e dei comandi "a capo" / "paragrafo" nei simboli/caratteri corretti.
        4.  Esegue una **capitalizzazione** di base (inizio frase, dopo punti di domanda/esclamativi, dopo newline).
        5.  Pulizia degli spazi superflui.
    -   Identifica **Comandi Speciali** (come "ferma dettatura") definiti in `config.py`.

#### `output_handler.py`

-   **Classe `OutputHandler`:**
    -   Gestisce l'invio del testo processato alla destinazione corretta.
    -   Può scrivere il testo processato nell'applicazione esterna attiva usando `pyautogui.typewrite()` (simulazione tastiera).
    -   Può scrivere il testo processato in un `QTextEdit` interno all'app.
    -   La modalità di output è configurabile per profilo.

### Interfaccia Grafica (`src/gui/`)

Costruita con PyQt6.

#### `main_window.py`

-   **Classe `MainWindow(QMainWindow)`:**
    -   Finestra principale dell'applicazione.
    -   Inizializza e coordina `ProfileManager`, `TextProcessor`, `OutputHandler`.
    -   Gestisce la creazione e il ciclo di vita del `TranscriptionThread`.
    -   Contiene i widget principali: pulsante START/STOP, etichetta di stato, combobox per i profili, editor interno.
    -   Crea e gestisce il menu dell'applicazione con accesso a: Gestione Profili, Impostazioni Profilo Attivo, Impostazioni App, Salva PDF, Info.
    -   Connette i segnali dell'interfaccia utente (click dei pulsanti, cambi nella combobox) alle azioni appropriate.
    -   Riceve segnali dal `TranscriptionThread` (nuova trascrizione, aggiornamenti di stato, errori) e aggiorna la UI di conseguenza.
    -   Implementa la logica per lo spinner di caricamento del modello.
    -   Gestisce la logica di abilitazione/disabilitazione dei controlli UI in base allo stato dell'applicazione (es. profilo caricato, trascrizione in corso).
    -   Include `_prepare_transcription_thread()` per una gestione robusta della creazione e pulizia dei thread di trascrizione.

#### `profile_dialogs.py`

Contiene le classi per i dialoghi modali utilizzati per la gestione dei profili e delle impostazioni:

-   **`ProfileManagementDialog`:** Per creare, eliminare, caricare, importare/esportare profili.
-   **`ProfileSettingsDialog`:** Per modificare le impostazioni del profilo attivo (modello, macro, vocabolario, ecc.).
-   **`AppSettingsDialog`:** Per configurare le impostazioni globali dell'app (dispositivo audio, livello di log). Utilizza `sounddevice.query_devices()` per popolare la lista dei microfoni disponibili.

### Gestione dei Thread

-   L'intera logica di cattura audio e trascrizione (`Transcriber`) viene eseguita in un `QThread` separato (`TranscriptionThread`) per evitare che l'interfaccia grafica si blocchi durante queste operazioni intensive.
-   La comunicazione tra `TranscriptionThread` e `MainWindow` avviene tramite segnali e slot Qt, un meccanismo sicuro per l'interazione tra thread in PyQt.
-   Viene utilizzata una `queue.Queue` per passare i dati audio dal callback di `sounddevice` (che viene eseguito in un thread di basso livello di `sounddevice`) al `_process_audio_queue` del `Transcriber` (che viene eseguito nel `TranscriptionThread`).
-   Un `threading.Lock` (`model_lock`) viene usato in `Transcriber` per proteggere l'accesso concorrente al modello Whisper durante il suo caricamento/ricaricamento.

### Persistenza Dati

-   **Profili Utente:** Salvati come cartelle e file JSON in `~/Library/Application Support/TrascriviPro Avanzato/profiles/`.
-   **Preferenze Applicazione:** Salvate come file JSON in `~/Library/Application Support/TrascriviPro Avanzato/preferences.json`.
-   **Log:** Salvati in `~/Library/Application Support/TrascriviPro Avanzato/logs/app.log`.
-   **Audio Debug:** File `.wav` salvati in `~/Library/Application Support/TrascriviPro Avanzato/logs/audio_debugs/`.

---

## Impacchettamento per macOS (Creazione App Installabile)

Per distribuire l'applicazione come un file `.app` stand-alone su macOS, utilizzeremo **PyInstaller**.

### Prerequisiti per l'Impacchettamento

-   Assicurati che l'applicazione funzioni correttamente eseguendola dall'ambiente virtuale.
-   Tutte le dipendenze devono essere installate nell'ambiente virtuale che userai per l'impacchettamento.

### Installazione di PyInstaller

Se non l'hai già fatto, installa PyInstaller nel tuo ambiente virtuale:

    pip install pyinstaller

### Creazione del File `.spec`

PyInstaller utilizza un file di specifica (`.spec`) per definire come l'applicazione deve essere impacchettata. È consigliabile generare un file `.spec` base e poi modificarlo, specialmente per applicazioni PyQt e quelle che usano modelli ML come Whisper.

1.  **Attiva il tuo ambiente virtuale.**
2.  **Naviga nella directory principale del progetto** (`TrascriviPro_Avanzato/`).
3.  **Esegui questo comando per generare un file `.spec` iniziale:**
    (Sostituisci `src/main.py` se il tuo entry point è diverso)

        pyi-makespec --windowed --name="TrascriviPro Avanzato" --icon="path/to/your/icon.icns" src/main.py

    *   `--windowed`: Indica che è un'applicazione GUI (non apre una console).
    *   `--name="TrascriviPro Avanzato"`: Il nome dell'app finale.
    *   `--icon="path/to/your/icon.icns"`: (Opzionale) Specifica un file icona `.icns` per l'app. Se non lo hai, puoi ometterlo per ora o crearlo successivamente.
    *   `src/main.py`: Il tuo script di ingresso principale.

    Questo creerà un file chiamato `TrascriviPro Avanzato.spec` (o simile) nella directory corrente.

### Modifica del File `.spec` (Cruciale)

Questo è il passo più importante e spesso richiede iterazioni. Apri il file `.spec` con un editor di testo. Dovrai probabilmente aggiungere o modificare le seguenti sezioni:

    # TrascriviPro Avanzato.spec

    # -*- mode: python ; coding: utf-8 -*-

    block_cipher = None

    a = Analysis(
        ['src/main.py'],  # Il tuo script di ingresso
        pathex=['/path/to/your/project/TrascriviPro_Avanzato'], # Percorso alla root del progetto
        binaries=[],
        datas=[
            # Includi la directory dei modelli di Whisper se non vengono trovati automaticamente
            # Il percorso esatto dei modelli dipende da come/dove Whisper li scarica.
            # Solitamente è in ~/.cache/whisper
            # Esempio (ADATTA QUESTO PERCORSO!):
            # ('/Users/TUO_UTENTE/.cache/whisper', 'whisper_models')
            #
            # Se hai altre risorse (immagini, file di dati non Python) che devono essere incluse:
            # ('path/to/your/resource_folder_in_src', 'destination_folder_name_in_app_bundle')
        ],
        hiddenimports=[
            'sounddevice', # Spesso necessario per sounddevice
            'pyautogui',
            'pynput', # Dipendenza di pyautogui, a volte necessaria esplicitarla
            '_sounddevice_data', # Potrebbe essere necessario
            # Aggiungi qui altri hidden imports che PyInstaller potrebbe non rilevare
            # Per PyQt6, di solito li rileva bene, ma controlla gli errori.
            'PyQt6.sip',
            'PyQt6.QtPrintSupport', # Se non viene incluso automaticamente
            'PyQt6.QtMultimedia', # Whisper o sounddevice potrebbero averne bisogno indirettamente
            # Per Whisper e le sue dipendenze (come Torch):
            'torch',
            'torchaudio',
            'torchvision', # Anche se non usato direttamente, a volte le installazioni di torch lo includono
            'whisper',
            'whisper.assets', # Se Whisper carica assets da lì
            'tiktoken_ext', # Per tiktoken, usato da Whisper
            # Dipendenze di Torch/Whisper che a volte sono problematiche
            'sklearn.utils._typedefs',
            'sklearn.neighbors._ball_tree',
            # ... e altre che potrebbero emergere durante il build o all'avvio dell'app
            # Controlla i log di build e gli errori all'avvio dell'app impacchettata.
        ],
        hookspath=[],
        hooksconfig={},
        runtime_hooks=[],
        excludes=[],
        win_no_prefer_redirects=False,
        win_private_assemblies=False,
        cipher=block_cipher,
        noarchive=False,
    )

    # --- AGGIUNTA IMPORTANTE per COLLETTARE I DATI DI WHISPER ---
    # Questa parte è cruciale se i modelli non vengono inclusi automaticamente.
    # Il modo più affidabile è trovare dove Whisper scarica i modelli
    # (di solito ~/.cache/whisper) e copiarli.
    # Tuttavia, whisper.load_model() dovrebbe scaricarli se non li trova al primo avvio dell'app impacchettata.
    # Un approccio alternativo è usare un hook per whisper.
    # Ma per iniziare, proviamo senza aggiunte complesse qui,
    # e se i modelli non caricano, rivediamo questa sezione.

    # --- Colleziona i dati per sounddevice se necessario ---
    # from PyInstaller.utils.hooks import collect_data_files
    # datas += collect_data_files('sounddevice', include_py_files=False)
    # datas += collect_data_files('openai-whisper', subdir='assets') # Per i file assets di Whisper


    pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,  # Assicurati che a.datas includa ciò che hai definito sopra
        [],
        name='TrascriviPro Avanzato',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True, # Se hai UPX installato e vuoi comprimere (opzionale)
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False, # False per app GUI
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None, # 'x86_64' o 'arm64' se vuoi forzare, altrimenti None per auto
        codesign_identity=None, # Per la firma del codice, vedi dopo
        entitlements_file=None, # Per la firma del codice, vedi dopo
        icon='path/to/your/icon.icns' # Ripeti l'icona qui
    )

    app = BUNDLE(
        exe,
        name='TrascriviPro Avanzato.app',
        icon='path/to/your/icon.icns', # E ancora qui per il bundle .app
        bundle_identifier=None, # Es: 'com.tuonome.trascriviproavanzato'
        # version='1.0.1' # Puoi specificare la versione qui
    )

**Note importanti sulla modifica del `.spec`:**

-   **`pathex`**: Assicurati che il percorso al tuo progetto sia corretto.
-   **`datas`**: Questa è la sezione per includere file non Python.
    -   **Modelli Whisper:** Il problema più comune con Whisper e PyInstaller è che i modelli non vengono inclusi. Whisper li scarica in `~/.cache/whisper`. PyInstaller non sa di questa directory.
        -   **Soluzione 1 (Raccomandata per Iniziare):** Non includere i modelli nel `datas`. Lascia che `whisper.load_model()` li scarichi al primo avvio dell'app impacchettata (l'utente vedrà il download). Questo mantiene il bundle dell'app più piccolo. L'app dovrà avere accesso a internet al primo avvio per scaricare il modello selezionato.
        -   **Soluzione 2 (Bundle più grande, offline):** Se vuoi includere i modelli:
            1.  Trova la directory `~/.cache/whisper`.
            2.  Aggiungi una tupla a `datas`: `('/Users/TUO_UTENTE/.cache/whisper', 'whisper_models_cache')`.
            3.  Poi, nel tuo codice Python (ad esempio in `config.py` o all'avvio del `Transcriber`), dovrai dire a Whisper di cercare i modelli in questa cartella impacchettata. Questo si può fare impostando la variabile d'ambiente `XDG_CACHE_HOME` _prima_ di importare `whisper`, in modo che punti a una sottodirectory dentro il bundle dell'app. Questo è più complesso.

                Esempio in `config.py` o `main.py` prima degli import di `whisper`:
                import os
                import sys
                if getattr(sys, 'frozen', False): # Se l'app è impacchettata
                    # Percorso relativo alla directory dei modelli impacchettata
                    application_path = os.path.dirname(sys.executable)
                    if sys.platform == "darwin": # macOS
                        # All'interno del bundle .app, sys.executable è in Contents/MacOS/
                        # Quindi dobbiamo salire di alcuni livelli per raggiungere Contents/Resources (ipotetico)
                        # o la root del bundle. È più semplice copiare i modelli nella stessa dir dell'eseguibile
                        # o in una sottodir ben definita se usi `datas`.
                        # Se hai ('/Users/TUO_UTENTE/.cache/whisper', 'whisper_models_cache') in datas,
                        # il percorso dentro l'app sarà 'whisper_models_cache'.
                        # models_dir_in_app = os.path.join(application_path, '..', 'Resources', 'whisper_models_cache') # Esempio con Resources
                        # Oppure se copiato vicino all'eseguibile:
                        # models_dir_in_app = os.path.join(application_path, 'whisper_models_cache')

                        # Whisper usa XDG_CACHE_HOME per trovare ~/.cache/whisper
                        # Potremmo dover sovrascrivere il percorso di download di whisper.
                        # os.environ['XDG_CACHE_HOME'] = os.path.join(application_path, 'cache_simulata')
                        # if not os.path.exists(os.path.join(os.environ['XDG_CACHE_HOME'], 'whisper')):
                        #    os.makedirs(os.path.join(os.environ['XDG_CACHE_HOME'], 'whisper'))
                        # Più semplicemente, si può passare `download_root` a `whisper.load_model(..., download_root=models_dir_in_app)`
                        # Questo richiede modifica a transcriber.py

            Per ora, consiglio la Soluzione 1 (download al primo avvio).
-   **`hiddenimports`**: Elenca qui i moduli che PyInstaller potrebbe non rilevare automaticamente. `sounddevice`, `_sounddevice_data`, `PyQt6.QtPrintSupport` sono candidati comuni. Per Whisper e Torch, potrebbero essercene molti; dovrai aggiungerli se l'app impacchettata dà errori di `ModuleNotFoundError`.
-   **`collect_data_files`**: A volte utile per pacchetti come `sounddevice` o `openai-whisper` se hanno file di dati non Python. Decommenta e adatta se necessario.
-   **`icon`**: Fornisci il percorso al tuo file `.icns`.
-   **`target_arch`**: Su macOS moderni, potresti voler creare build separate per `x86_64` (Intel) e `arm64` (Apple Silicon) o una build universale (più complessa con PyInstaller, solitamente richiede la compilazione separata e l'uso di `lipo`). Per iniziare, `None` lascerà che PyInstaller scelga l'architettura della macchina su cui stai compilando.

### Esecuzione di PyInstaller con il File `.spec`

Una volta che il file `.spec` è configurato:

1.  **Attiva il tuo ambiente virtuale.**
2.  **Naviga nella directory principale del progetto.**
3.  **Esegui PyInstaller:**
    `pyinstaller "TrascriviPro Avanzato.spec" --noconfirm`
    -   `--noconfirm`: Sovrascrive la directory `dist` e `build` senza chiedere.

    PyInstaller creerà una directory `build` (file temporanei) e una directory `dist`. All'interno di `dist`, troverai `TrascriviPro Avanzato.app`.

### Verifica e Distribuzione dell'App

1.  **Verifica:**
    -   Prova ad eseguire `TrascriviPro Avanzato.app` dalla directory `dist`.
    -   Testa tutte le funzionalità.
    -   Controlla se ci sono errori nella console all'avvio (puoi avviare l'app dal terminale per vedere l'output: `open dist/"TrascriviPro Avanzato.app" --args -c` o direttamente `./dist/"TrascriviPro Avanzato.app/Contents/MacOS/TrascriviPro Avanzato"`).
    -   **Permessi macOS:** La prima volta che l'app tenta di accedere al microfono o inviare input ad altre app, macOS chiederà i permessi. Questo è normale.
    -   **Caricamento Modelli Whisper:** Se non hai incluso i modelli, al primo avvio di una trascrizione con un nuovo modello, dovresti vedere un messaggio o un log che indica il download.
2.  **Risoluzione Problemi Comuni:**
    -   **`ModuleNotFoundError`**: Aggiungi il modulo mancante a `hiddenimports` nel file `.spec` e ricompila.
    -   **File non trovati (es. modelli Whisper, icone, dati)**: Assicurati che siano inclusi correttamente in `datas` nel file `.spec` o che il codice li cerchi nel posto giusto all'interno del bundle dell'app. Ricorda che i percorsi cambiano quando l'app è impacchettata. Usa `sys._MEIPASS` per accedere ai file inclusi nel bundle temporaneo durante l'esecuzione (se usi `--onedir` o `--onefile`).
    -   **Problemi con `sounddevice` o audio**: Assicurati che `ffmpeg` e `portaudio` siano accessibili o, se possibile, considera di impacchettarli (più complesso).
    -   **Librerie Dinamiche (`.dylib`) non trovate**: A volte PyInstaller non copia tutte le librerie necessarie, specialmente quelle di C/C++. Potrebbe essere necessario aggiungerle manualmente in `binaries` nel file `.spec` o usare `install_name_tool` per correggere i percorsi delle librerie.
3.  **Distribuzione:**
    -   Una volta che l'app `.app` funziona correttamente, puoi comprimerla in un file `.zip` o creare un'immagine disco `.dmg` per una distribuzione più professionale.
    -   Per creare un `.dmg`, puoi usare Utility Disco su macOS o strumenti da riga di comando come `hdiutil`. Esistono anche script o strumenti di terze parti che automatizzano questo processo (es. `create-dmg`).

### Icona dell'Applicazione (Opzionale ma Raccomandato)

1.  Crea un'icona in formato `.icns`. Puoi usare strumenti come "Image2Icon" o "Icon Composer" (parte di Xcode Graphics Tools), o convertire un'immagine PNG di alta risoluzione (es. 1024x1024px).
2.  Specifica il percorso al tuo file `.icns` nelle opzioni `--icon` di `pyi-makespec` e nelle sezioni `icon` di `EXE` e `BUNDLE` nel file `.spec`.

### Firma del Codice (Opzionale ma Raccomandato per Distribuzione)

Per evitare avvisi di sicurezza di Gatekeeper su macOS quando altri utenti scaricano la tua app, dovresti firmare l'applicazione con un Apple Developer ID.

1.  Avrai bisogno di un account Apple Developer Program.
2.  Una volta ottenuto un certificato "Developer ID Application", puoi specificarlo in `codesign_identity` nel file `.spec`.
    # Nel file .spec, dentro EXE:
    # codesign_identity='Developer ID Application: Tuo Nome (TEAMID)',
    # entitlements_file='entitlements.plist', # File opzionale per permessi specifici
3.  PyInstaller tenterà di firmare l'app durante il processo di build.
4.  Dopo la creazione del `.app`, puoi anche "notarizzare" l'app con Apple, un processo automatico che scansiona l'app alla ricerca di malware e, se superato, riduce ulteriormente gli avvisi di Gatekeeper.

Questo processo di firma e notarizzazione è più avanzato e non strettamente necessario se l'app è solo per uso personale o per utenti che sanno come bypassare gli avvisi di Gatekeeper.

---

## Troubleshooting e Problemi Noti

-   **Output Esterno (`pyautogui`):** Richiede una verifica approfondita dei permessi di Accessibilità su macOS per garantire il funzionamento. Attualmente, il testo viene trascritto e inviato a `pyautogui`, ma potrebbe non apparire nell'applicazione esterna se i permessi non sono corretti o se ci sono problemi di focus.
-   **Reattività "Tempo Reale":** L'output del testo avviene a segmenti (dopo pause o ogni tot secondi di parlato continuo). Un output parola per parola istantaneo con l'attuale libreria Whisper è complesso e non implementato. Le soglie attuali nel `Transcriber` cercano un bilanciamento.
-   **Comandi Vocali di Start:** Il comando vocale per avviare la trascrizione non è implementato (richiederebbe un ascolto costante di parole chiave, separato dal flusso principale di Whisper). Il comando di stop è parzialmente gestito.
-   **Rifinitura GUI:** Le interfacce per la gestione delle tabelle (macro, pronunce) potrebbero essere rese più user-friendly.
-   **Packaging e Distribuzione:** Il processo di creazione di un `.app` standalone con PyInstaller (o simili) che includa tutte le dipendenze (Python, PyQt6, PyTorch, Whisper, modelli) necessita di essere creato, testato e debuggato.
-   **Allucinazioni di Whisper / Punteggiatura / Token Speciali (`<|zh|>`)**:
    -   **Causa:** Modelli più piccoli (`tiny`, `base`, `small`) sono più inclini a errori. Pause lunghe, rumore, o audio poco chiaro possono confondere il modello. A volte Whisper rileva erroneamente segmenti in altre lingue o genera token speciali.
    -   **Soluzione:** Utilizzare modelli Whisper più grandi (`medium`, `large`) migliora significativamente l'accuratezza e la gestione della punteggiatura. Assicurare un input audio chiaro. Il `TextProcessor` pulisce alcuni token speciali.
    -   **Debug:** Attivare "Registra audio per debug" nelle impostazioni del profilo per analizzare i file `.wav` che causano problemi.
-   **Errore `OMP: Error #15: Initializing libiomp5.dylib, but found libomp.dylib already initialized.` (macOS):**
    -   **Causa:** Conflitto tra librerie OpenMP usate da PyTorch.
    -   **Soluzione:** A volte impostare `os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'` all'inizio di `main.py` può aiutare, ma è un workaround. La soluzione migliore è assicurarsi che le versioni di PyTorch e delle sue dipendenze siano compatibili.
-   **L'applicazione impacchettata non si avvia o crasha subito:**
    -   **Causa:** Spesso `ModuleNotFoundError` o file di dati mancanti.
    -   **Soluzione:** Controlla attentamente i log di build di PyInstaller e avvia l'app impacchettata dal terminale per vedere l'output di errore. Aggiungi `hiddenimports` o `datas` necessari al file `.spec`.
-   **Permessi macOS:** L'app richiederà permessi per il microfono e l'accessibilità (per `pyautogui`). L'utente dovrà concederli tramite le Preferenze di Sistema.

## Possibili Miglioramenti Futuri

-   **I. Miglioramenti Trascrizione/Accuratezza:**
    -   Implementare la Calibrazione Audio Assistita per aiutare gli utenti a popolare vocabolario e regole di pronuncia.
    -   Aggiungere Feedback Visivo della Voce (waveform/livello input) nella GUI.
    -   Considerare Soppressione del Rumore se necessario.
    -   Selezione Lingua Dinamica: Permettere a Whisper di rilevare automaticamente la lingua o fornire un menu più ampio di lingue supportate.
    -   Supporto `initial_prompt`: Permettere all'utente di specificare un `initial_prompt` per Whisper per migliorare ulteriormente l'accuratezza in contesti specifici.
-   **II. Funzionalità Testo/Comandi Avanzate:**
    -   Implementare Comandi Vocali di Formattazione Avanzati ("maiuscola X", "cancella ultima parola", ecc.).
    -   Implementare la "Modalità Comando" vs "Modalità Dettatura".
    -   Esplorare il supporto per Template/Campi da Compilare (molto complesso).
    -   Opzioni di formattazione più avanzate (es. grassetto, corsivo tramite comandi vocali).
    -   Un sistema di regole di punteggiatura più sofisticato se quello automatico di Whisper non è sufficiente per tutti i casi d'uso.
-   **III. Miglioramenti UI/UX:**
    -   Rifinare ulteriormente le GUI di gestione delle impostazioni (tabelle più interattive, validazione).
    -   Aggiungere Temi Personalizzabili (chiaro/scuro).
    -   Creare un Tutorial/Guida Rapida Integrata.
    -   Migliorare il feedback durante operazioni lunghe (es. download modelli Whisper).
    -   Aggiungere Notifiche di Sistema.
    -   Predisporre per Internazionalizzazione (i18n).
-   **IV. Packaging e Distribuzione:**
    -   Testare e finalizzare lo script di packaging con PyInstaller per creare un .app standalone affidabile per macOS.
    -   Creare un .dmg per una facile distribuzione.
    -   (Opzionale, per distribuzione ampia) Investigare la firma del codice e la notarizzazione Apple.
    -   Supporto Multi-Piattaforma: Estendere e testare l'applicazione per Windows e Linux.
-   **V. Altri Sviluppi:**
    -   Test Automatici: Implementazione di unit test e test di integrazione per migliorare la robustezza.
    -   Utilizzo di `whisper.cpp`: Per una potenziale maggiore efficienza e minori dipendenze rispetto alla versione Python di Whisper, anche se l'integrazione sarebbe più complessa.
    -   Plugin o API per Estensioni: Per permettere l'integrazione di funzionalità di terze parti.

## Contributi

Invitiamo a contribuire allo sviluppo di TrascriviPro Avanzato tramite pull request su GitHub per nuove funzionalità o correzioni di bug, o segnalando problemi tramite l'issue tracker.

## Licenza

