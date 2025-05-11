# src/utils/logger.py
import logging
import sys
from pathlib import Path # Path è già usato nella versione originale di config.py per LOG_FILE

# Importa le configurazioni rilevanti da src.config
try:
    from src.config import LOG_FILE, LOG_LEVEL, APP_NAME
except ImportError:
    # Fallback nel caso config.py non sia accessibile o le costanti non siano definite
    # Questo è più per robustezza durante lo sviluppo o in caso di problemi di importazione.
    # In un'app funzionante, config.py dovrebbe essere sempre accessibile.
    print("ATTENZIONE: Impossibile importare configurazioni da src.config per il logger. Uso valori di fallback.")
    fallback_log_dir = Path.cwd() / "logs_fallback"
    fallback_log_dir.mkdir(exist_ok=True)
    LOG_FILE = fallback_log_dir / "app_fallback.log"
    LOG_LEVEL = "INFO"
    APP_NAME = "TrascriviProApp_Fallback"

# Definisci il formato del log qui per chiarezza
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - [%(module)s.%(funcName)s:%(lineno)d] - %(message)s'

def setup_logger(logger_name: str = APP_NAME,
                 log_file_path: Path = LOG_FILE,
                 level_name: str = LOG_LEVEL) -> logging.Logger:
    """
    Configura e restituisce un'istanza del logger per l'applicazione.
    """
    logger = logging.getLogger(logger_name)

    # Imposta il livello del logger. Se il livello non è valido, usa INFO.
    try:
        numeric_level = getattr(logging, level_name.upper())
        if not isinstance(numeric_level, int): # getattr potrebbe restituire qualcos'altro se level_name non è un nome di livello valido
            raise ValueError(f"Livello di log non valido: {level_name}")
        logger.setLevel(numeric_level)
    except (AttributeError, ValueError) as e:
        print(f"ATTENZIONE: Livello di log '{level_name}' non valido o non trovato: {e}. Imposto a INFO.")
        logger.setLevel(logging.INFO)
        level_name = "INFO" # Aggiorna level_name per coerenza con l'attributo sotto


    # Evita di aggiungere handler multipli se la funzione viene chiamata più volte
    if logger.hasHandlers():
        logger.handlers.clear()

    # Crea il formatter
    formatter = logging.Formatter(LOG_FORMAT)

    # Handler per scrivere su file
    try:
        # Assicurati che la directory del file di log esista
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logger.getEffectiveLevel()) # L'handler dovrebbe avere lo stesso livello del logger o inferiore
        logger.addHandler(file_handler)
    except Exception as e:
        # Questo è un problema serio, stampalo sulla console standard
        # perché il logger potrebbe non essere ancora completamente configurato.
        sys.stderr.write(f"ERRORE CRITICO: Impossibile creare file handler per il log a {log_file_path}: {e}\n")

    # Handler per scrivere sulla console (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logger.getEffectiveLevel()) # Anche per la console
    logger.addHandler(console_handler)

    # Aggiungiamo un attributo per recuperare il nome del livello dalla config,
    # utile per il dialogo delle impostazioni per mostrare il livello corrente.
    logger.level_name_from_config = level_name.upper()

    logger.info(f"Logger '{logger_name}' configurato. Livello effettivo: {logging.getLevelName(logger.getEffectiveLevel())}. File di log: {log_file_path}")
    return logger

# Istanza globale del logger per l'applicazione
# Viene configurato quando il modulo logger.py viene importato per la prima volta.
app_logger = setup_logger()

if __name__ == '__main__':
    # Esempio di utilizzo per testare il logger
    print(f"Test logger. Livello impostato: {app_logger.level_name_from_config}")
    print(f"Livello effettivo del logger: {logging.getLevelName(app_logger.getEffectiveLevel())}")
    
    app_logger.debug("Questo è un messaggio di debug (visibile se LOG_LEVEL è DEBUG).")
    app_logger.info("Questo è un messaggio informativo.")
    app_logger.warning("Questo è un avviso.")
    app_logger.error("Questo è un errore.")
    app_logger.critical("Questo è un errore critico.")

    # Test cambio livello al volo (simula quello che farebbe AppSettingsDialog)
    print("\n--- Cambio livello log a DEBUG (solo per questo test, non persistente) ---")
    # Nota: questa modifica diretta non è come l'app lo farebbe; l'app
    # modificherebbe la preferenza e poi MainWindow.handle_app_settings_changed
    # chiamerebbe app_logger.setLevel e handler.setLevel.
    # Per un test semplice qui, modifichiamo direttamente l'istanza.
    app_logger.setLevel(logging.DEBUG)
    for handler in app_logger.handlers: # Importante aggiornare anche gli handler
        handler.setLevel(logging.DEBUG)
    app_logger.level_name_from_config = "DEBUG" # Simula aggiornamento
    
    print(f"Nuovo livello effettivo del logger: {logging.getLevelName(app_logger.getEffectiveLevel())}")
    app_logger.debug("Ora questo messaggio di debug DOVREBBE essere visibile.")
    app_logger.info("Messaggio informativo dopo cambio livello.")

    # Ripristina a un livello più comune per non inondare i log se il test viene eseguito più volte
    # Questa è solo una precauzione per il blocco if __name__ == '__main__'
    app_logger.setLevel(logging.INFO)
    for handler in app_logger.handlers:
        handler.setLevel(logging.INFO)
    app_logger.level_name_from_config = "INFO"