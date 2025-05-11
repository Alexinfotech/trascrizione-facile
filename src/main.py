# src/main.py
import sys
import os # os è importato ma non direttamente usato; potrebbe essere per KMP_DUPLICATE_LIB_OK

# Importa QApplication e QMessageBox da PyQt6
from PyQt6.QtWidgets import QApplication, QMessageBox

# Importa i componenti principali dell'applicazione
# È buona norma importare prima i moduli del progetto, poi quelli di terze parti se necessario.
from src.config import APP_NAME, VERSION # Importa APP_NAME e VERSION per i messaggi
from src.utils.logger import app_logger # Importa l'istanza del logger già configurata
from src.core.profile_manager import ProfileManager
from src.gui.main_window import MainWindow

# Gestione opzionale di variabili d'ambiente specifiche per PyTorch/macOS
# Questa riga è spesso usata per risolvere problemi con librerie MKL su macOS.
# Va usata con cautela e solo se si riscontrano errori specifici relativi a "OMP: Error #15".
# In generale, è meglio risolvere il problema alla radice se possibile (es. aggiornando PyTorch o le dipendenze).
# os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

def run_application():
    """
    Funzione principale per avviare e gestire l'applicazione TrascriviPro.
    """
    # Logga l'avvio dell'applicazione usando il nome e la versione da config.py
    app_logger.info(f"--- AVVIO APPLICAZIONE: {APP_NAME} v{VERSION} ---")
    app_logger.info(f"Python version: {sys.version}")
    app_logger.info(f"Platform: {sys.platform}")
    app_logger.info(f"Qt Version (for PyQt): {QApplication.libraryPaths()}") # Può dare info utili

    # Crea l'istanza di QApplication. Deve essere creata prima di qualsiasi widget Qt.
    # sys.argv permette di passare argomenti da riga di comando all'applicazione Qt.
    app = QApplication(sys.argv)

    # --- Blocco Try-Except per la gestione degli errori critici all'avvio ---
    try:
        # 1. Inizializza il ProfileManager
        # Questo gestirà il caricamento/salvataggio dei profili utente e delle preferenze.
        app_logger.debug("Inizializzazione ProfileManager...")
        profile_manager = ProfileManager()
        app_logger.info("ProfileManager inizializzato con successo.")

        # 2. Controlla se esistono profili. Se no, la MainWindow guiderà l'utente.
        if not profile_manager.get_available_profiles():
            app_logger.info("Nessun profilo utente esistente. La MainWindow gestirà la creazione del primo profilo.")
        else:
            app_logger.info(f"Profili disponibili trovati: {profile_manager.get_available_profiles()}")
            if profile_manager.get_current_profile_display_name():
                app_logger.info(f"Profilo corrente caricato all'avvio: {profile_manager.get_current_profile_display_name()}")
            else:
                app_logger.info("Nessun profilo specifico caricato come corrente all'avvio (verrà selezionato il primo disponibile o gestito dalla GUI).")


        # 3. Crea e mostra la Finestra Principale
        # Passa l'istanza del profile_manager alla MainWindow.
        app_logger.debug("Creazione MainWindow...")
        main_window = MainWindow(profile_manager)
        app_logger.info("MainWindow creata.")
        main_window.show()
        app_logger.info("Finestra principale mostrata. Avvio event loop di Qt.")

        # 4. Avvia l'event loop di Qt
        # L'applicazione rimarrà in esecuzione qui finché la finestra principale non verrà chiusa.
        exit_code = app.exec()
        app_logger.info(f"Event loop di Qt terminato. Codice di uscita: {exit_code}")
        
        # sys.exit() è chiamato fuori dal try-except-finally per assicurare che
        # il blocco finally venga eseguito prima dell'uscita effettiva.
        # Il codice di uscita da app.exec() viene propagato.

    except RuntimeError as e:
        # Errori di runtime specifici, ad esempio fallimento caricamento modello Whisper,
        # o problemi con librerie essenziali.
        error_message = f"Errore critico di runtime all'avvio: {e}"
        app_logger.critical(error_message, exc_info=True)
        QMessageBox.critical(None, f"Errore Critico - {APP_NAME}",
                             f"Impossibile avviare l'applicazione a causa di un errore critico:\n\n{e}\n\n"
                             "Controlla il file di log per maggiori dettagli.")
        sys.exit(1) # Esce con codice di errore

    except Exception as e:
        # Qualsiasi altra eccezione non gestita durante l'inizializzazione.
        error_message = f"Errore non gestito e imprevisto durante l'avvio: {e}"
        app_logger.critical(error_message, exc_info=True)
        QMessageBox.critical(None, f"Errore Imprevisto - {APP_NAME}",
                             f"Si è verificato un errore imprevisto durante l'avvio:\n\n{e}\n\n"
                             "L'applicazione potrebbe non funzionare correttamente. Controlla il file di log.")
        sys.exit(1) # Esce con codice di errore
    
    # Non c'è un blocco finally qui perché il log di terminazione è gestito
    # dal segnale aboutToQuit della QApplication connesso a on_app_quit in MainWindow.
    # Se l'app esce a causa di un'eccezione qui sopra, il log di terminazione "normale"
    # non verrà scritto, ma l'errore critico sì.

    sys.exit(exit_code if 'exit_code' in locals() else 0)


if __name__ == '__main__':
    # Questo è il punto di ingresso standard per un'applicazione Python.
    run_application()