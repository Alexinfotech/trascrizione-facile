# src/gui/main_window.py
import sys
import logging
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QComboBox, QStatusBar, QMenuBar, QMessageBox,
    QFileDialog, QGroupBox
)
from PyQt6.QtGui import QAction, QFont, QCloseEvent
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QObject, QDateTime # Aggiunto QObject

from src.config import (
    APP_NAME, VERSION,
    COMMAND_STOP_RECORDING,
    INTERNAL_EDITOR_ENABLED_DEFAULT, LOG_LEVEL
)
from src.utils.logger import app_logger
from src.core.profile_manager import ProfileManager
from src.core.transcriber import Transcriber
from src.core.text_processor import TextProcessor
from src.core.output_handler import OutputHandler
from src.gui.profile_dialogs import ProfileManagementDialog, ProfileSettingsDialog, AppSettingsDialog

from typing import Optional

# --- Thread di Trascrizione ---
class TranscriptionThread(QThread):
    new_transcription = pyqtSignal(str)
    status_update = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    initialization_complete = pyqtSignal(bool, str)
    # finished = pyqtSignal() # Standard di QThread, non serve dichiararlo qui se non per type hinting

    def __init__(self, profile_manager: ProfileManager, parent: Optional[QObject] = None): # QObject per parent
        super().__init__(parent)
        self.profile_manager = profile_manager
        self.is_running_flag = False 
        self.transcriber_instance: Optional[Transcriber] = None
        self._initialization_has_failed = False # Flag per tracciare fallimento init

    def run(self):
        self.is_running_flag = True
        self._initialization_has_failed = False # Resetta all'inizio di run
        app_logger.info("TranscriptionThread: run() avviato. Inizializzazione Transcriber...")
        try:
            app_logger.debug("TranscriptionThread: Creazione nuova istanza Transcriber.")
            self.transcriber_instance = Transcriber(
                profile_manager=self.profile_manager,
                on_transcription_callback=self.new_transcription.emit,
                on_status_update_callback=self.status_update.emit
            )
            
            if not self.transcriber_instance.model:
                profile_name = self.profile_manager.get_current_profile_display_name() or "Sconosciuto"
                error_msg = f"Modello Whisper non caricato per profilo '{profile_name}'. Trascrizione impossibile."
                app_logger.error(f"TranscriptionThread: {error_msg}")
                self.initialization_complete.emit(False, error_msg)
                self._initialization_has_failed = True # Segna fallimento
                return 

            app_logger.info("TranscriptionThread: Transcriber inizializzato e modello pronto.")
            if not self.transcriber_instance.start_listening():
                mic_error_msg = "Fallimento avvio ascolto microfono. Controlla permessi e dispositivo audio."
                app_logger.error(f"TranscriptionThread: {mic_error_msg}")
                self.initialization_complete.emit(False, mic_error_msg) 
                self._initialization_has_failed = True # Segna fallimento
                return
            
            self.initialization_complete.emit(True, "Ascolto avviato...")
            
            while self.is_running_flag:
                self.msleep(100) # Loop principale del thread, controlla is_running_flag

        except RuntimeError as e: # Es. problemi specifici di librerie come sounddevice
            error_msg = f"Errore di runtime in TranscriptionThread: {e}"
            app_logger.critical(f"TranscriptionThread: {error_msg}", exc_info=True)
            self.initialization_complete.emit(False, error_msg) # Notifica fallimento init
            self._initialization_has_failed = True
        except Exception as e: # Qualsiasi altra eccezione
            error_msg = f"Errore critico in TranscriptionThread: {e}"
            app_logger.critical(f"TranscriptionThread: {error_msg}", exc_info=True)
            # Se l'init era già passata, emetti error_signal, altrimenti initialization_complete(False)
            if not self._initialization_has_failed: # Se l'errore avviene dopo un'inizializzazione ok
                self.error_signal.emit(error_msg)
            else: # Se l'errore avviene durante l'inizializzazione (o dopo un fallimento già emesso)
                 self.initialization_complete.emit(False, error_msg)
            self._initialization_has_failed = True
        finally:
            if self.transcriber_instance and self.transcriber_instance.is_listening:
                app_logger.info("TranscriptionThread: Finally - Assicuro stop di Transcriber.")
                self.transcriber_instance.stop_listening()
            self.is_running_flag = False # Assicura che il flag sia Falso all'uscita
            app_logger.info("TranscriptionThread: Metodo run() concluso.")
            # Il segnale 'finished' viene emesso automaticamente da QThread quando run() termina.

    def request_stop(self):
        app_logger.info("TranscriptionThread: Ricevuta richiesta di stop (imposto is_running_flag = False).")
        self.is_running_flag = False # Il loop in run() rileverà questo

# --- Finestra Principale ---
class MainWindow(QMainWindow):
    def __init__(self, profile_manager: ProfileManager):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} - v{VERSION}")
        self.setGeometry(100, 100, 850, 700)

        self.profile_manager = profile_manager
        self.text_processor = TextProcessor(self.profile_manager)
        self.internal_editor_widget = QTextEdit()
        self.output_handler = OutputHandler(internal_editor_widget=self.internal_editor_widget)
        
        self.transcription_thread: Optional[TranscriptionThread] = None
        self._is_operation_in_progress = False # Flag per prevenire operazioni UI sovrapposte

        self.loading_spinner_timer = QTimer(self)
        self.loading_spinner_timer.timeout.connect(self._update_loading_spinner)
        self.spinner_chars = ["|", "/", "-", "\\"]
        self.spinner_index = 0
        self.base_loading_message = "" 

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.init_ui()
        self.create_menu()
        self.connect_signals()
        
        self.load_profiles_into_combo() # Questo caricherà anche il profilo di default o il primo

        if not self.profile_manager.get_current_profile_display_name() and not self.profile_combo.count():
            app_logger.info("Nessun profilo esistente. Apertura dialogo gestione profili.")
            self.update_ui_for_no_profile() # Assicura che la UI sia nello stato corretto
            QTimer.singleShot(100, self.open_profile_manager_dialog_if_none_exist)

        app_logger.info(f"{APP_NAME} GUI inizializzata.")
        QApplication.instance().aboutToQuit.connect(self.on_app_quit)

    def open_profile_manager_dialog_if_none_exist(self):
        if not self.profile_manager.get_available_profiles():
            QMessageBox.information(self, "Benvenuto!",
                                    f"Nessun profilo utente trovato.\n"
                                    "È necessario creare almeno un profilo per iniziare.\n\n"
                                    "Clicca 'OK' per aprire la gestione profili.")
            self.open_profile_manager_dialog() # Apre il dialogo per creare/importare

    def _prepare_transcription_thread(self):
        app_logger.debug("MainWindow: Inizio _prepare_transcription_thread.")
        if self.transcription_thread:
            app_logger.info("MainWindow: _prepare_transcription_thread - Trovato thread esistente.")
            
            # Disconnetti i segnali dal vecchio thread PRIMA di tentare di fermarlo o dereferenziarlo.
            # Questo previene che i suoi segnali (specialmente 'finished') vengano gestiti
            # dopo che self.transcription_thread potrebbe essere stato riassegnato.
            try:
                app_logger.debug("MainWindow: _prepare_transcription_thread - Tentativo disconnessione segnali thread precedente.")
                self.transcription_thread.new_transcription.disconnect(self.handle_new_transcription_from_thread)
                self.transcription_thread.status_update.disconnect(self.update_status_from_thread)
                self.transcription_thread.error_signal.disconnect(self.show_error_message_from_thread)
                self.transcription_thread.initialization_complete.disconnect(self._handle_thread_initialization_complete)
                self.transcription_thread.finished.disconnect(self._on_transcription_thread_finished) # Cruciale
                app_logger.debug("MainWindow: _prepare_transcription_thread - Segnali disconnessi.")
            except TypeError:
                app_logger.debug("MainWindow: _prepare_transcription_thread - Nessun segnale da disconnettere (o errore tipo).")
            except Exception as e:
                app_logger.error(f"MainWindow: _prepare_transcription_thread - Eccezione durante disconnessione segnali: {e}")

            if self.transcription_thread.isRunning():
                app_logger.info("MainWindow: _prepare_transcription_thread - Thread esistente in esecuzione. Richiedo stop.")
                self.transcription_thread.request_stop()
                if not self.transcription_thread.wait(2500): # Timeout leggermente aumentato
                    app_logger.warning("MainWindow: _prepare_transcription_thread - Timeout attesa terminazione thread precedente.")
                else:
                    app_logger.info("MainWindow: _prepare_transcription_thread - Thread precedente terminato correttamente.")
            
            self.transcription_thread = None # Assicura che sia None prima di crearne uno nuovo
            app_logger.debug("MainWindow: _prepare_transcription_thread - self.transcription_thread impostato a None dopo pulizia.")

        if not self.profile_manager.current_profile_safe_name:
            app_logger.warning("MainWindow: _prepare_transcription_thread - Nessun profilo attivo, non creo nuovo thread.")
            self.update_ui_for_no_profile()
            return

        app_logger.info("MainWindow: _prepare_transcription_thread - Creazione nuova istanza TranscriptionThread.")
        self.transcription_thread = TranscriptionThread(profile_manager=self.profile_manager, parent=self)
        # Connetti i segnali del NUOVO thread
        self.transcription_thread.new_transcription.connect(self.handle_new_transcription_from_thread)
        self.transcription_thread.status_update.connect(self.update_status_from_thread)
        self.transcription_thread.error_signal.connect(self.show_error_message_from_thread)
        self.transcription_thread.initialization_complete.connect(self._handle_thread_initialization_complete)
        self.transcription_thread.finished.connect(self._on_transcription_thread_finished)
        app_logger.debug("MainWindow: _prepare_transcription_thread - Nuova istanza TranscriptionThread configurata e pronta.")


    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        top_layout = QHBoxLayout()
        self.profile_label = QLabel("Profilo Attivo: Nessuno")
        top_layout.addWidget(self.profile_label)
        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumWidth(250)
        self.profile_combo.setToolTip("Seleziona il profilo utente attivo")
        top_layout.addWidget(self.profile_combo)
        self.manage_profiles_button = QPushButton("Gestisci Profili...")
        self.manage_profiles_button.setToolTip("Crea, carica, elimina, importa/esporta profili utente")
        top_layout.addWidget(self.manage_profiles_button)
        top_layout.addStretch()
        main_layout.addLayout(top_layout)
        self.toggle_button = QPushButton("START")
        self.toggle_button.setFixedHeight(50)
        self.toggle_button.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        self.set_button_style_start()
        self.toggle_button.setEnabled(False) # Disabilitato finché un profilo non è caricato
        main_layout.addWidget(self.toggle_button)
        self.status_label_gui = QLabel("Stato: Pronto")
        self.status_label_gui.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label_gui.setFont(QFont("Arial", 11))
        main_layout.addWidget(self.status_label_gui)
        editor_groupbox = QGroupBox("Editor Interno")
        editor_layout = QVBoxLayout()
        self.internal_editor_widget.setPlaceholderText(
            "Il testo trascritto apparirà qui se la modalità 'Editor Interno' è attiva per il profilo corrente.\n"
            "Altrimenti, il testo verrà inviato all'applicazione esterna attiva."
        )
        self.internal_editor_widget.setReadOnly(True) # Inizialmente read-only
        self.internal_editor_widget.setFont(QFont("Arial", 12))
        editor_layout.addWidget(self.internal_editor_widget)
        editor_groupbox.setLayout(editor_layout)
        main_layout.addWidget(editor_groupbox)
        self.update_status_bar("Pronto.")

    def update_status_bar(self, message: str):
        if hasattr(self, 'status_bar') and self.status_bar: # Controllo esistenza status_bar
            self.status_bar.showMessage(message, 7000) # Mostra per 7 secondi

    def set_button_style_start(self):
        self.toggle_button.setText("START")
        self.toggle_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; border-radius: 8px; padding: 10px;} QPushButton:hover { background-color: #45a049; } QPushButton:disabled { background-color: #B0B0B0; color: #707070; }")

    def set_button_style_stop(self):
        self.toggle_button.setText("STOP")
        self.toggle_button.setStyleSheet("QPushButton { background-color: #f44336; color: white; border-radius: 8px; padding: 10px;} QPushButton:hover { background-color: #da190b; }")

    def create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        self.manage_profiles_action = QAction("&Gestisci Profili...", self)
        file_menu.addAction(self.manage_profiles_action)
        self.app_settings_action = QAction("&Impostazioni Applicazione...", self)
        file_menu.addAction(self.app_settings_action)
        self.profile_settings_action = QAction("Impostazioni &Profilo Attivo...", self)
        file_menu.addAction(self.profile_settings_action)
        self.profile_settings_action.setEnabled(False) # Abilitato solo se un profilo è attivo
        file_menu.addSeparator()
        save_pdf_action = QAction("Salva Editor come &PDF...", self)
        save_pdf_action.triggered.connect(self.save_editor_as_pdf)
        file_menu.addAction(save_pdf_action)
        file_menu.addSeparator()
        exit_action = QAction("&Esci", self)
        exit_action.triggered.connect(self.close) # Chiama QMainWindow.close()
        file_menu.addAction(exit_action)
        help_menu = menubar.addMenu("&Aiuto")
        about_action = QAction("&Informazioni su...", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def connect_signals(self):
        self.toggle_button.clicked.connect(self.toggle_transcription_ui_logic)
        self.manage_profiles_button.clicked.connect(self.open_profile_manager_dialog)
        self.manage_profiles_action.triggered.connect(self.open_profile_manager_dialog)
        self.app_settings_action.triggered.connect(self.open_app_settings_dialog)
        self.profile_settings_action.triggered.connect(self.open_current_profile_settings_dialog)
        self.profile_combo.currentIndexChanged.connect(self.on_profile_changed_from_combo)

    def load_profiles_into_combo(self):
        self.profile_combo.blockSignals(True) # Blocca segnali per evitare chiamate multiple a on_profile_changed
        current_selected_text_before_clear = self.profile_combo.currentText()
        self.profile_combo.clear()
        
        profiles_display_names = self.profile_manager.get_available_profiles()
        app_logger.debug(f"MainWindow: Caricamento profili in ComboBox: {profiles_display_names}")

        if profiles_display_names:
            for display_name in profiles_display_names:
                self.profile_combo.addItem(display_name)

            target_selection_name = self.profile_manager.get_current_profile_display_name()
            # Se non c'è un profilo corrente nel manager, prova a usare quello selezionato prima del clear
            if not target_selection_name and current_selected_text_before_clear:
                if current_selected_text_before_clear in profiles_display_names:
                     target_selection_name = current_selected_text_before_clear
            
            found_idx = -1
            if target_selection_name: # Se abbiamo un nome target, cercalo
                found_idx = self.profile_combo.findText(target_selection_name)
            
            if found_idx != -1: # Trovato
                self.profile_combo.setCurrentIndex(found_idx)
            elif self.profile_combo.count() > 0: # Non trovato o nessun target, seleziona il primo
                self.profile_combo.setCurrentIndex(0)
            
            # Forziamo la gestione del cambio profilo se l'indice è valido e diverso da prima,
            # o se il profilo nel manager non corrisponde a quello nella combo.
            current_combo_idx = self.profile_combo.currentIndex()
            if current_combo_idx >= 0: # Se c'è una selezione valida nella combo
                # Se il profilo selezionato nella combo è diverso da quello selezionato prima del clear,
                # o se non c'è nessun dato di profilo caricato nel manager,
                # o se il nome del profilo nel manager non corrisponde a quello nella combo,
                # allora forza un aggiornamento.
                if self.profile_combo.itemText(current_combo_idx) != current_selected_text_before_clear or \
                   not self.profile_manager.current_profile_data or \
                   (self.profile_manager.get_current_profile_display_name() != self.profile_combo.itemText(current_combo_idx)):
                    # Chiama on_profile_changed_from_combo via QTimer per permettere alla UI di aggiornarsi
                    QTimer.singleShot(0, lambda idx=current_combo_idx: self.on_profile_changed_from_combo(idx))
                else:
                    # Il profilo nella combo è lo stesso di prima e corrisponde a quello nel manager.
                    # Aggiorna solo la UI se necessario (es. se era "Nessuno").
                    self.update_ui_for_current_profile()
            else: # Nessuna selezione valida nella combo (lista vuota)
                self.update_ui_for_no_profile()
        else: # Nessun profilo disponibile
            self.update_ui_for_no_profile()
        
        self.profile_combo.blockSignals(False) # Riabilita i segnali

    def on_profile_changed_from_combo(self, index: int):
        if self._is_operation_in_progress:
            app_logger.warning("MainWindow: Cambio profilo ignorato, operazione UI in corso.")
            # Potrebbe essere necessario reimpostare l'indice della combo a quello precedente
            # se l'operazione in corso era critica, ma per ora logghiamo.
            return

        self._is_operation_in_progress = True # Inizia operazione
        self.toggle_button.setEnabled(False)  # Disabilita temporaneamente il bottone START/STOP

        if index < 0 or self.profile_combo.count() == 0:
            app_logger.info("MainWindow: on_profile_changed_from_combo: indice non valido o ComboBox vuota.")
            self.update_ui_for_no_profile()
            self._is_operation_in_progress = False # Fine operazione
            return

        display_name_to_load = self.profile_combo.itemText(index)
        current_active_profile_display_name = self.profile_manager.get_current_profile_display_name()

        # Se il profilo selezionato è già quello attivo nel manager, non ricaricare, ma prepara il thread
        if current_active_profile_display_name == display_name_to_load and self.profile_manager.current_profile_data:
            app_logger.info(f"MainWindow: Profilo '{display_name_to_load}' è già attivo. Preparo thread e aggiorno UI.")
            self._prepare_transcription_thread() # Assicura che il thread sia pronto per questo profilo
            self.update_ui_for_current_profile() # Aggiorna la UI (es. editor read-only, stato)
            self._is_operation_in_progress = False # Fine operazione
            self.toggle_button.setEnabled(True) # Riabilita START/STOP
            return

        app_logger.info(f"MainWindow: Tentativo di caricare profilo '{display_name_to_load}' da ComboBox.")
        self._prepare_transcription_thread() # Prepara il thread (fermerà quello vecchio se esiste)
        
        if self.profile_manager.load_profile(display_name_to_load):
            app_logger.info(f"MainWindow: Profilo '{display_name_to_load}' caricato con successo.")
            self.update_ui_for_current_profile() # Aggiorna la UI con le info del nuovo profilo
        else:
            QMessageBox.critical(self, "Errore Caricamento Profilo",
                                 f"Impossibile caricare il profilo '{display_name_to_load}'.")
            self.update_ui_for_no_profile() # Torna allo stato "nessun profilo"
            self.load_profiles_into_combo() # Ricarica la combo per riflettere lo stato attuale
        
        self._is_operation_in_progress = False # Fine operazione
        self.toggle_button.setEnabled(self.profile_manager.current_profile_safe_name is not None)


    def update_ui_for_no_profile(self):
        app_logger.info("MainWindow: Aggiornamento UI per 'Nessun Profilo'.")
        self.profile_label.setText("Profilo Attivo: Nessuno")
        self.update_status_bar("Nessun profilo. Creane uno o importane uno.")
        self.status_label_gui.setText("Stato: Nessun Profilo Attivo")
        self.profile_settings_action.setEnabled(False)
        self.toggle_button.setEnabled(False)
        self.set_button_style_start() # Bottone START, disabilitato
        self.internal_editor_widget.setReadOnly(True); self.internal_editor_widget.clear()
        self.output_handler.set_output_mode(False) # Nessun output se non c'è profilo
        
        if self.transcription_thread and self.transcription_thread.isRunning():
            app_logger.info("MainWindow: update_ui_for_no_profile - Fermo thread di trascrizione attivo.")
            self.transcription_thread.request_stop()
            if not self.transcription_thread.wait(1000): # Breve attesa
                 app_logger.warning("MainWindow: Timeout attesa stop thread (update_ui_for_no_profile).")
        # Non impostare self.transcription_thread a None qui, _prepare_transcription_thread lo gestirà.


    def update_ui_for_current_profile(self):
        display_name = self.profile_manager.get_current_profile_display_name()
        if not display_name: # Se per qualche motivo il nome non è disponibile, torna a "no profile"
            self.update_ui_for_no_profile(); return

        app_logger.info(f"MainWindow: Aggiornamento UI per profilo '{display_name}'.")
        self.profile_label.setText(f"Profilo Attivo: {display_name}")
        
        # Controlla se un thread è in esecuzione (cioè se la trascrizione è attiva)
        is_thread_running = self.transcription_thread and self.transcription_thread.isRunning()
        if not is_thread_running:
            if not self.loading_spinner_timer.isActive(): # Non sovrascrivere lo spinner
                self.status_label_gui.setText(f"Stato: Profilo: {display_name} | Pronto.")
            self.set_button_style_start() # Bottone mostra "START"
        else: # Trascrizione attiva
            current_status = self.status_label_gui.text().replace('Stato: ', '')
            if "Caricamento" in current_status or "Ascolto" in current_status: # Mantiene lo stato di caricamento/ascolto
                 self.update_status_bar(f"Profilo: {display_name} | {current_status}")
            else: # Se lo stato era diverso, imposta "Ascolto"
                self.update_status_bar(f"Profilo: {display_name} | Ascolto...")
            self.set_button_style_stop() # Bottone mostra "STOP"

        self.profile_settings_action.setEnabled(True) # Abilita impostazioni profilo
        self.toggle_button.setEnabled(True) # Abilita START/STOP

        use_internal = self.profile_manager.get_profile_setting("output_to_internal_editor", INTERNAL_EDITOR_ENABLED_DEFAULT)
        self.output_handler.set_output_mode(use_internal, self.internal_editor_widget)
        self.internal_editor_widget.setReadOnly(not use_internal) # Editor scrivibile solo se in modalità interna
        
        # Assicura che il thread sia pronto per il profilo corrente
        # Questo è importante se il profilo è cambiato o se le impostazioni sono state aggiornate
        self._prepare_transcription_thread() 


    def toggle_transcription_ui_logic(self):
        if self._is_operation_in_progress:
            app_logger.warning("MainWindow: Click su START/STOP ignorato, operazione UI già in corso.")
            return
        if not self.profile_manager.current_profile_safe_name:
            QMessageBox.warning(self, "Profilo Mancante", "Seleziona o crea un profilo prima di avviare la trascrizione.")
            return

        self._is_operation_in_progress = True # Inizia operazione critica
        self.toggle_button.setEnabled(False)  # Disabilita il bottone durante la transizione

        if not self.transcription_thread or not self.transcription_thread.isRunning():
            # --- AVVIO TRASCRIZIONE ---
            app_logger.info("MainWindow: Richiesto AVVIO trascrizione.")
            self._prepare_transcription_thread() # Assicura che il thread sia pulito e pronto
            if not self.transcription_thread: # Se _prepare non ha potuto creare un thread (es. no profilo)
                app_logger.error("MainWindow: Impossibile avviare, TranscriptionThread non preparato (es. nessun profilo).")
                QMessageBox.critical(self, "Errore Avvio", "Impossibile preparare il thread di trascrizione.")
                self._is_operation_in_progress = False # Fine operazione
                self.toggle_button.setEnabled(self.profile_manager.current_profile_safe_name is not None)
                self.set_button_style_start()
                return
            
            # Lo stato "Avvio in corso..." o "Caricamento modello..." viene impostato da TranscriptionThread
            # tramite il segnale status_update -> update_status_from_thread
            self.transcription_thread.start() # Avvia il thread (chiama il suo metodo run())
            # Il bottone e _is_operation_in_progress verranno gestiti da _handle_thread_initialization_complete
        else: 
            # --- STOP TRASCRIZIONE ---
            app_logger.info("MainWindow: Richiesto STOP trascrizione.")
            self.update_status_from_thread("Arresto in corso...") # Aggiorna subito lo stato UI
            self.transcription_thread.request_stop() # Dice al thread di fermarsi
            
            # NON attendere qui con self.transcription_thread.wait() perché bloccherebbe la UI.
            # Il segnale 'finished' del thread chiamerà _on_transcription_thread_finished
            # che si occuperà di resettare _is_operation_in_progress e il bottone.
            # Se il thread impiega troppo a fermarsi, l'utente potrebbe percepire un blocco.
            # Per ora, ci fidiamo che il thread termini in modo ragionevole.
            # Il bottone rimane disabilitato finché _on_transcription_thread_finished non lo riabilita.


    def _handle_thread_initialization_complete(self, success: bool, message: str):
        app_logger.info(f"MainWindow: Segnale initialization_complete. Successo={success}, Msg='{message}'")
        
        # Solo agire se questo segnale proviene dal thread attualmente attivo
        if not self.sender() == self.transcription_thread:
            app_logger.warning("MainWindow: initialization_complete ricevuto da un thread obsoleto. Ignoro.")
            return

        if success:
            self.set_button_style_stop() # Bottone diventa STOP
            self.update_status_from_thread(message) # Es. "Ascolto avviato..."
        else: # Inizializzazione fallita
            current_status_text = self.status_label_gui.text()
            # Mostra QMessageBox solo se il messaggio non è già contenuto (per evitare duplicati da status_label)
            # e se il messaggio indica un errore non banale.
            if message not in current_status_text:
                 if "Errore" in message or "Fallimento" in message : # Mostra solo se è un errore chiaro
                    QMessageBox.critical(self, "Errore Avvio Trascrizione", message)
            self.set_button_style_start() # Bottone torna a START
            self.update_status_from_thread(f"Fallito: {message[:80]}...") # Aggiorna stato UI
            # Il thread dovrebbe essersi già fermato o fermarsi a breve.
            # _on_transcription_thread_finished resetterà _is_operation_in_progress e riabiliterà il bottone.
        
        # Se l'operazione era un avvio (come dovrebbe essere per initialization_complete)
        # e il segnale proviene dal thread corrente, possiamo considerare l'operazione "avvio" conclusa.
        if self._is_operation_in_progress and self.sender() == self.transcription_thread:
            self._is_operation_in_progress = False
            self.toggle_button.setEnabled(True) # Riabilita il bottone (ora START o STOP)


    def _on_transcription_thread_finished(self):
        app_logger.info("MainWindow: Inizio _on_transcription_thread_finished.")
        
        # Non fare check con self.sender() qui, perché il thread potrebbe essere già stato
        # dereferenziato da _prepare_transcription_thread se un'altra azione è avvenuta rapidamente.
        # La disconnessione fatta in _prepare_transcription_thread dovrebbe prevenire chiamate multiple.
        
        was_init_failed = False
        # Controlla se il thread che ha emesso 'finished' aveva fallito l'inizializzazione
        # Per fare questo, dovremmo passare lo stato dal thread o usare un flag
        # ma per ora, controlliamo self.transcription_thread se esiste ancora (potrebbe non essere affidabile)
        # Per semplicità, guardiamo lo stato della GUI. Se non è "Ascolto", probabilmente c'era un problema.
        # Il flag _initialization_has_failed nel thread è più robusto.
        # Poiché non possiamo accedere a self.sender()._initialization_has_failed direttamente,
        # ci affidiamo allo stato UI o a logica precedente.
        # Consideriamo che se il thread finisce e non era in stato "Ascolto", c'era un problema.
        if "Ascolto" not in self.status_label_gui.text(): # Stima approssimativa
             was_init_failed = True 
        app_logger.debug(f"MainWindow: _on_transcription_thread_finished - was_init_failed (stimato)={was_init_failed}")
        
        # self.transcription_thread è già stato impostato a None e segnali disconnessi
        # da _prepare_transcription_thread se un nuovo thread è stato preparato.
        # Se invece è uno stop normale, self.transcription_thread dovrebbe essere ancora l'istanza che ha finito.
        # Lo impostiamo a None qui per essere sicuri dopo uno stop.
        if self.transcription_thread and not self.transcription_thread.isRunning(): # Assicurati che sia effettivamente finito
            self.transcription_thread = None
            app_logger.debug("MainWindow: _on_transcription_thread_finished - self.transcription_thread impostato a None.")


        self._is_operation_in_progress = False # Fine operazione critica
        app_logger.debug(f"MainWindow: _on_transcription_thread_finished - _is_operation_in_progress impostato a False.")
        self.set_button_style_start() # Bottone torna a START
        
        can_start_again = self.profile_manager.current_profile_safe_name is not None
        self.toggle_button.setEnabled(can_start_again) # Riabilita il bottone
        app_logger.debug(f"MainWindow: _on_transcription_thread_finished - toggle_button abilitato: {can_start_again}")
        
        current_status_text = self.status_label_gui.text()
        if not was_init_failed and not ("Errore" in current_status_text or "Fallito" in current_status_text):
            self.update_status_from_thread("Trascrizione Stoppata.")
        elif not ("Errore" in current_status_text or "Fallito" in current_status_text):
             self.update_status_from_thread("Pronto.") # O un messaggio di fallimento se init fallita
        
        app_logger.info("MainWindow: Fine _on_transcription_thread_finished.")

    def _update_loading_spinner(self):
        if self.loading_spinner_timer.isActive():
            self.spinner_index = (self.spinner_index + 1) % len(self.spinner_chars)
            spinner_char = self.spinner_chars[self.spinner_index]
            self.status_label_gui.setText(f"Stato: {self.base_loading_message} {spinner_char}")

    def update_status_from_thread(self, message: str):
        if "Caricamento modello Whisper" in message:
            if not self.loading_spinner_timer.isActive():
                self.base_loading_message = message 
                self.spinner_index = 0
                self._update_loading_spinner() 
                self.loading_spinner_timer.start(200) 
                app_logger.debug("MainWindow: Spinner caricamento modello avviato.")
            app_logger.info(f"MainWindow: GUI Status Update (messaggio base per spinner): {message}")
            return 
        elif (("Modello" in message and "pronto" in message) or \
             ("Errore caricamento modello" in message) or \
             ("Fallito:" in message and ("Avvio" in self.status_label_gui.text() or "Caricamento" in self.status_label_gui.text() )) ) and \
             self.loading_spinner_timer.isActive():
            self.loading_spinner_timer.stop()
            app_logger.debug("MainWindow: Spinner caricamento modello fermato.")

        self.status_label_gui.setText(f"Stato: {message}")
        app_logger.info(f"MainWindow: GUI Status Update: {message}")
        
        is_stopped_or_error_or_failed = "Stoppata" in message or \
                              "terminato" in message.lower() or \
                              "Errore" in message or \
                              "Fallito" in message or \
                              "Fallimento" in message

        # Se il messaggio indica uno stop/errore/fallimento E il bottone è ancora "STOP"
        if is_stopped_or_error_or_failed and self.toggle_button.text() == "STOP":
            self.set_button_style_start() # Reimposta il bottone a "START"
        
        # Se il thread non è in esecuzione (o non esiste) e non siamo in uno stato di errore/fallimento
        # E il messaggio non è già "Trascrizione Stoppata" o "Pronto"
        # Allora imposta lo stato a "Pronto".
        if not (self.transcription_thread and self.transcription_thread.isRunning()):
            if not is_stopped_or_error_or_failed and "Stoppata" not in message and "Pronto" not in message:
                if self.profile_manager.current_profile_safe_name:
                    self.status_label_gui.setText(f"Stato: Profilo: {self.profile_manager.get_current_profile_display_name()} | Pronto.")
                else:
                    self.status_label_gui.setText("Stato: Pronto.")
        
        # Riabilita il bottone se non c'è un'operazione in corso e c'è un profilo
        if not self._is_operation_in_progress:
             self.toggle_button.setEnabled(self.profile_manager.current_profile_safe_name is not None)


    def handle_new_transcription_from_thread(self, raw_text: str):
        app_logger.debug(f"MainWindow: Testo grezzo da thread: {repr(raw_text)}")
        if not self.profile_manager.current_profile_safe_name: return # Non processare se non c'è profilo

        # Gestione semplificata comandi base (es. "a capo") se necessario qui,
        # ma la maggior parte della logica dovrebbe essere in TextProcessor.
        if raw_text.strip().lower() == "a capo": # Esempio di comando diretto se TextProcessor non lo copre per qualche motivo
            app_logger.info("MainWindow: 'a capo' rilevato, invio newline a OutputHandler.")
            self.output_handler.type_text("\n")
            self.update_status_bar("Comando: A Capo")
            return
        
        if self.text_processor.is_special_command(raw_text):
            command = raw_text.strip().lower()
            if command in COMMAND_STOP_RECORDING: # Usa la lista da config
                app_logger.info(f"MainWindow: Comando vocale STOP ('{command}') ricevuto.")
                if self.transcription_thread and self.transcription_thread.isRunning():
                     self.toggle_transcription_ui_logic() # Chiama la stessa logica del click su STOP
                return

        processed_text = self.text_processor.process_text(raw_text)
        if processed_text is not None: # TextProcessor può restituire None o stringa vuota
            self.output_handler.type_text(processed_text)
            display_text = processed_text.replace("\n", " ").replace("\r", " ").strip()
            if display_text: self.update_status_bar(f"Trascritto: '{display_text[:50]}...'")
        elif raw_text.strip(): # Se raw_text non era vuoto ma processed_text lo è
            app_logger.warning(f"MainWindow: raw_text '{repr(raw_text)}' -> processed_text nullo/vuoto. Nessun output.")

    def show_error_message_from_thread(self, message: str):
        app_logger.error(f"MainWindow: Errore critico da thread (via error_signal): {message}")
        QMessageBox.critical(self, "Errore Trascrizione", str(message))
        
        # Resetta lo stato UI in caso di errore critico dal thread
        self._is_operation_in_progress = False
        self.set_button_style_start()
        self.toggle_button.setEnabled(self.profile_manager.current_profile_safe_name is not None)
        self.status_label_gui.setText("Stato: Errore.")
        if self.loading_spinner_timer.isActive(): self.loading_spinner_timer.stop()


    def show_about_dialog(self):
        QMessageBox.about(self, f"Informazioni su {APP_NAME}",
                          f"{APP_NAME} v{VERSION}\n\n"
                          "Applicazione desktop per la trascrizione vocale.\n"
                          "Sviluppata con Python, PyQt6 e Whisper.")

    def save_editor_as_pdf(self):
        if not self.internal_editor_widget.toPlainText().strip():
            QMessageBox.information(self, "Editor Vuoto", "Non c'è testo da salvare.")
            return
        default_filename = f"Trascrizione_{QDateTime.currentDateTime().toString('yyyyMMdd_HHmmss')}.pdf"
        save_file_path, _ = QFileDialog.getSaveFileName(self, "Salva Editor come PDF", default_filename, "File PDF (*.pdf)")
        if not save_file_path: return

        app_logger.info(f"Tentativo salvataggio PDF in: {save_file_path}")
        try:
            from PyQt6.QtPrintSupport import QPrinter # Import locale per questa funzione
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(save_file_path)
            doc = self.internal_editor_widget.document()
            doc.print(printer) # Metodo corretto
            QMessageBox.information(self, "PDF Salvato", f"File PDF salvato in:\n{save_file_path}")
            app_logger.info(f"PDF salvato con successo: {save_file_path}")
        except ImportError:
             QMessageBox.critical(self, "Errore Modulo", "Modulo QtPrintSupport non trovato. Impossibile salvare in PDF.")
             app_logger.error("Modulo QtPrintSupport non trovato per salvataggio PDF.")
        except Exception as e:
            QMessageBox.critical(self, "Errore Salvataggio PDF", f"Impossibile salvare il PDF: {e}")
            app_logger.error(f"Errore salvataggio PDF: {e}", exc_info=True)

    def open_profile_manager_dialog(self):
        if self._is_operation_in_progress: # Non aprire se un'altra op UI è in corso
            QMessageBox.information(self, "Operazione in Corso", "Attendi il completamento dell'operazione corrente.")
            return
        
        if self.transcription_thread and self.transcription_thread.isRunning():
            reply = QMessageBox.question(self, "Trascrizione Attiva", "Fermare la trascrizione per gestire i profili?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.toggle_transcription_ui_logic() # Ferma la trascrizione
                # Dobbiamo attendere che la trascrizione sia effettivamente ferma PRIMA di aprire il dialogo.
                # Usiamo un QTimer per controllare lo stato.
                self.check_stop_before_profile_dialog_timer = QTimer(self)
                self.check_stop_before_profile_dialog_timer.timeout.connect(self._check_and_show_profile_management_dialog)
                self.check_stop_before_profile_dialog_timer.start(100) # Controlla ogni 100ms
            else: return # L'utente ha scelto No
        else: # Trascrizione non attiva, apri subito il dialogo
            self._show_profile_management_dialog_after_stop()

    def _check_and_show_profile_management_dialog(self):
        # Questo metodo viene chiamato dal QTimer
        if (self.transcription_thread and self.transcription_thread.isRunning()) or self._is_operation_in_progress:
            # Se la trascrizione è ancora in esecuzione o un'altra operazione è in corso, attendi ancora.
            # Il timer continuerà a chiamare questo metodo.
            app_logger.debug("_check_and_show_profile_management_dialog: Attesa stop trascrizione/operazione...")
        else:
            # Trascrizione fermata e nessuna operazione in corso, ferma il timer e apri il dialogo.
            if hasattr(self, 'check_stop_before_profile_dialog_timer'):
                self.check_stop_before_profile_dialog_timer.stop()
                del self.check_stop_before_profile_dialog_timer # Pulisci il timer
            app_logger.debug("_check_and_show_profile_management_dialog: Trascrizione fermata, apro dialogo profili.")
            self._show_profile_management_dialog_after_stop()

    def _show_profile_management_dialog_after_stop(self):
        dialog = ProfileManagementDialog(self.profile_manager, self)
        # Connetti i segnali del dialogo per aggiornare la MainWindow
        dialog.profile_changed_signal.connect(self.handle_profile_load_or_delete_from_dialog) # Se un profilo è caricato/eliminato
        dialog.profile_list_updated_signal.connect(self.load_profiles_into_combo) # Se la lista dei profili cambia
        dialog.exec() # Mostra il dialogo modale

    def handle_profile_load_or_delete_from_dialog(self):
        app_logger.info("MainWindow: Segnale profile_changed da ProfileManagementDialog ricevuto.")
        self.load_profiles_into_combo() # Ricarica la combo e gestisce il cambio profilo
        # update_ui_for_current_profile() sarà chiamato da load_profiles_into_combo o on_profile_changed

    def open_app_settings_dialog(self):
        dialog = AppSettingsDialog(self.profile_manager, self)
        dialog.settings_changed_signal.connect(self.handle_app_settings_changed)
        dialog.exec()

    def handle_app_settings_changed(self):
        app_logger.info("MainWindow: Segnale cambio impostazioni globali applicazione.")
        # Aggiorna livello log
        new_log_level_str = self.profile_manager.get_global_preference("global_log_level", LOG_LEVEL)
        try:
            numeric_level = getattr(logging, new_log_level_str.upper(), None)
            if numeric_level is not None:
                app_logger.setLevel(numeric_level)
                for handler in app_logger.handlers: handler.setLevel(numeric_level)
                if hasattr(app_logger, 'level_name_from_config'): # Aggiorna l'attributo custom
                    app_logger.level_name_from_config = new_log_level_str.upper()
                app_logger.info(f"Livello log applicazione aggiornato a: {new_log_level_str}")
            else: app_logger.error(f"Livello log non valido ricevuto da preferenze: {new_log_level_str}")
        except Exception as e: app_logger.error(f"Errore durante l'aggiornamento del livello di log: {e}", exc_info=True)

        # Gestisci cambio dispositivo audio
        new_device_id_pref = self.profile_manager.get_global_preference("selected_audio_device_id")
        
        current_transcriber_device_id = None
        if self.transcription_thread and self.transcription_thread.transcriber_instance:
             current_transcriber_device_id = self.transcription_thread.transcriber_instance.selected_audio_device_id
        
        # Se il dispositivo è cambiato, o se non c'era un transcriber prima, bisogna preparare un nuovo thread.
        if current_transcriber_device_id != new_device_id_pref or not self.transcription_thread:
            app_logger.info(f"Rilevato cambio dispositivo audio (da {current_transcriber_device_id} a {new_device_id_pref}) o thread non esistente. Preparo nuovo thread.")
            was_listening = self.transcription_thread and self.transcription_thread.isRunning()
            
            self._prepare_transcription_thread() # Ferma vecchio thread (se esiste), ne prepara uno nuovo.
                                             # Il nuovo Transcriber userà il nuovo ID dispositivo.
            if was_listening: # Se stava ascoltando, informa l'utente che deve riavviare
                self.update_status_from_thread("Dispositivo audio cambiato. Premi START per riavviare.")
                # Lo stato del bottone (testo START/STOP) dovrebbe essere gestito da _prepare_transcription_thread
                # e/o dai segnali del thread. Se _prepare ferma un thread, _on_transcription_thread_finished
                # dovrebbe impostare il bottone a START.
            else:
                app_logger.info("Preferenza dispositivo audio aggiornata. Verrà usata al prossimo avvio della trascrizione.")
        elif self.transcription_thread and self.transcription_thread.transcriber_instance: # Nessun cambio ID, ma ricarica preferenza nel transcriber esistente
            self.transcription_thread.transcriber_instance._load_global_audio_device_preference()
            app_logger.info("Preferenza dispositivo audio ricaricata nel transcriber esistente (nessun cambio di ID).")


    def open_current_profile_settings_dialog(self):
        if not self.profile_manager.current_profile_safe_name:
            QMessageBox.warning(self, "Nessun Profilo", "Nessun profilo attivo da configurare.")
            return
        
        was_listening = self.transcription_thread and self.transcription_thread.isRunning()
        if was_listening:
             QMessageBox.information(self, "Trascrizione Attiva", 
                                     "La trascrizione è attiva.\nLe modifiche al modello Whisper o alla lingua "
                                     "avranno effetto al prossimo avvio della trascrizione.")
        
        dialog = ProfileSettingsDialog(self.profile_manager, self)
        # Passa lo stato 'was_listening' al gestore del segnale
        dialog.profile_settings_changed_signal.connect(
            lambda: self.handle_profile_settings_change_from_dialog(was_listening_before_dialog=was_listening)
        )
        dialog.exec()
            
    def handle_profile_settings_change_from_dialog(self, was_listening_before_dialog: bool = False):
        app_logger.info("MainWindow: Segnale cambio impostazioni profilo ricevuto.")
        self.load_profiles_into_combo() # Ricarica la combo (il nome potrebbe essere cambiato)
                                    # Questo a sua volta potrebbe chiamare on_profile_changed_from_combo
                                    # che chiama _prepare_transcription_thread e update_ui_for_current_profile
        
        # Se il profilo corrente è ancora lo stesso (non eliminato e ricaricato)
        # e la trascrizione era attiva, l'utente potrebbe aver bisogno di riavviare.
        current_display_name = self.profile_manager.get_current_profile_display_name()
        if current_display_name == self.profile_combo.currentText(): # Il profilo è ancora quello
            app_logger.info(f"MainWindow: Profilo '{current_display_name}' riconfigurato. Preparo thread.")
            self._prepare_transcription_thread() # Prepara il thread con le nuove impostazioni
            self.update_ui_for_current_profile() # Aggiorna la UI
            
            # Se stava ascoltando e ora il thread non è più in esecuzione (perché _prepare lo ha fermato)
            if was_listening_before_dialog and not (self.transcription_thread and self.transcription_thread.isRunning()):
                self.update_status_from_thread("Impostazioni profilo aggiornate. Premi START.")


    def closeEvent(self, event: QCloseEvent):
        app_logger.info("MainWindow: Evento closeEvent ricevuto.")
        if self._is_operation_in_progress:
            app_logger.warning("MainWindow: Tentativo di chiusura durante operazione UI critica. Ignoro temporaneamente.")
            # Potremmo voler dare un feedback all'utente, ma per ora logghiamo e ignoriamo.
            event.ignore(); return

        if self.transcription_thread and self.transcription_thread.isRunning():
            reply = QMessageBox.question(self, 'Conferma Uscita', 
                                         "La trascrizione è attiva. Fermarla e uscire dall'applicazione?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                app_logger.info("MainWindow: Utente ha scelto di fermare la trascrizione e uscire.")
                self._is_operation_in_progress = True; self.toggle_button.setEnabled(False) # Blocca UI
                self.transcription_thread.request_stop()
                if not self.transcription_thread.wait(2500): # Attendi un po' per la chiusura pulita
                    app_logger.warning("MainWindow: Timeout attesa chiusura thread durante closeEvent.")
                # Non chiamare on_app_quit qui, viene chiamato da aboutToQuit
                event.accept() # Permetti la chiusura
            else: # L'utente ha scelto No
                app_logger.info("MainWindow: Uscita annullata dall'utente.")
                event.ignore() # Impedisci la chiusura
        else: # Trascrizione non attiva, accetta la chiusura
            app_logger.info("MainWindow: Trascrizione non attiva, chiusura permessa.")
            event.accept()

    def on_app_quit(self):
        # Questo metodo viene chiamato automaticamente quando l'applicazione sta per chiudere,
        # DOPO che closeEvent ha permesso la chiusura.
        app_logger.info("MainWindow: Segnale aboutToQuit. Eseguo pulizia finale.")
        self._is_operation_in_progress = True # Previene ulteriori interazioni
        
        # Assicurati che il thread sia fermo se per qualche motivo è ancora referenziato e attivo
        if self.transcription_thread and self.transcription_thread.isRunning():
            app_logger.info("MainWindow: on_app_quit - Fermo thread di trascrizione residuo.")
            self.transcription_thread.request_stop()
            self.transcription_thread.wait(1500) # Breve attesa finale
        self.transcription_thread = None # Dereferenzia
        
        if hasattr(self, 'profile_manager') and self.profile_manager:
            self.profile_manager._save_app_preferences() # Salva le preferenze globali
        app_logger.info(f"--- {APP_NAME} v{VERSION} TERMINATO (on_app_quit) ---")

if __name__ == '__main__':
    # Blocco di test per avviare solo la MainWindow
    app = QApplication(sys.argv)
    try:
        test_pm = ProfileManager() # Crea un ProfileManager per il test
    except Exception as e:
        QMessageBox.critical(None, "Errore Critico Avvio Test ProfileManager", f"Errore durante inizializzazione ProfileManager: {e}")
        sys.exit(1)

    # Crea un profilo di test se non ne esistono
    if not test_pm.get_available_profiles():
        success_create, msg_create = test_pm.create_profile("ProfiloDiTestPerMain")
        if not success_create or not test_pm.load_profile("ProfiloDiTestPerMain"):
            QMessageBox.critical(None, "Errore Creazione Profilo Test", f"Impossibile creare/caricare profilo di test: {msg_create}")
            # Non uscire, la MainWindow dovrebbe gestire lo stato senza profili
    elif not test_pm.get_current_profile_display_name(): # Se esistono profili ma nessuno è caricato
        available_profiles = test_pm.get_available_profiles()
        if available_profiles and not test_pm.load_profile(available_profiles[0]):
             QMessageBox.warning(None, "Errore Caricamento Profilo Default", f"Impossibile caricare il primo profilo disponibile: {available_profiles[0]}")

    try:
        main_win = MainWindow(test_pm) # Passa il ProfileManager alla MainWindow
    except Exception as e:
        QMessageBox.critical(None, "Errore Critico Avvio Test MainWindow", f"Errore durante inizializzazione MainWindow: {e}")
        sys.exit(1)
        
    main_win.show()
    sys.exit(app.exec())