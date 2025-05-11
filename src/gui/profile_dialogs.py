# src/gui/profile_dialogs.py
import json # Non usato direttamente, ma ProfileManager lo usa
import shutil
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMessageBox, QDialogButtonBox, QScrollArea,
    QWidget, QFormLayout, QTableWidget, QTableWidgetItem, QAbstractItemView,
    QComboBox, QCheckBox, QGroupBox, QInputDialog, QTextEdit, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from src.core.profile_manager import ProfileManager
from src.utils.logger import app_logger
from src.config import (
    AVAILABLE_WHISPER_MODELS, DEFAULT_WHISPER_MODEL, DEFAULT_LANGUAGE,
    PROFILE_SETTINGS_FILENAME, LOG_LEVEL, INTERNAL_EDITOR_ENABLED_DEFAULT
)
from typing import Optional, List, Dict, Any # Aggiunto Any
import logging # Per getattr in AppSettingsDialog (anche se gestito in MainWindow)
import sounddevice as sd


# --- Dialogo per la Gestione Generale dei Profili ---
class ProfileManagementDialog(QDialog):
    profile_changed_signal = pyqtSignal()
    profile_list_updated_signal = pyqtSignal()

    def __init__(self, profile_manager: ProfileManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.profile_manager = profile_manager
        self.setWindowTitle("Gestione Profili Utente")
        self.setMinimumSize(650, 480)
        self.setModal(True)

        main_layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._load_selected_and_accept)
        self.list_widget.setToolTip("Doppio click su un profilo per caricarlo e chiudere questa finestra.")
        main_layout.addWidget(self.list_widget)

        profile_ops_layout = QHBoxLayout()
        self.create_button = QPushButton("Crea Nuovo...")
        self.create_button.clicked.connect(self._create_new_profile) # Rinominato per chiarezza interna
        profile_ops_layout.addWidget(self.create_button)

        self.delete_button = QPushButton("Elimina Selezionato")
        self.delete_button.clicked.connect(self._delete_selected_profile) # Rinominato
        profile_ops_layout.addWidget(self.delete_button)

        profile_ops_layout.addStretch()

        self.import_button = QPushButton("Importa Profilo da ZIP...")
        self.import_button.clicked.connect(self._import_profile) # Rinominato
        profile_ops_layout.addWidget(self.import_button)

        self.export_button = QPushButton("Esporta Profilo Selezionato in ZIP...")
        self.export_button.clicked.connect(self._export_selected_profile) # Rinominato
        profile_ops_layout.addWidget(self.export_button)
        main_layout.addLayout(profile_ops_layout)

        action_buttons_layout = QHBoxLayout()
        action_buttons_layout.addStretch()

        self.load_button = QPushButton("Carica Selezionato e Chiudi")
        self.load_button.clicked.connect(self._load_selected_and_accept)
        action_buttons_layout.addWidget(self.load_button)

        self.close_dialog_button = QPushButton("Chiudi")
        self.close_dialog_button.clicked.connect(self.reject)
        action_buttons_layout.addWidget(self.close_dialog_button)
        main_layout.addLayout(action_buttons_layout)

        self.populate_profile_list()
        self._update_button_states()
        self.list_widget.currentItemChanged.connect(self._update_button_states)

    def populate_profile_list(self):
        self.list_widget.clear()
        profiles_display_names = self.profile_manager.get_available_profiles()
        app_logger.debug(f"ProfileManagementDialog: Popolamento lista profili con: {profiles_display_names}")
        for display_name in profiles_display_names:
            item = QListWidgetItem(display_name)
            self.list_widget.addItem(item)

        current_display_name = self.profile_manager.get_current_profile_display_name()
        if current_display_name:
            items = self.list_widget.findItems(current_display_name, Qt.MatchFlag.MatchExactly)
            if items:
                self.list_widget.setCurrentItem(items[0])
        elif self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
        self._update_button_states() # Assicura che i pulsanti siano aggiornati dopo il popolamento

    def _get_selected_display_name(self) -> Optional[str]:
        current_item = self.list_widget.currentItem()
        return current_item.text() if current_item else None

    def _update_button_states(self):
        selected_profile_name = self._get_selected_display_name()
        is_profile_selected = selected_profile_name is not None

        self.delete_button.setEnabled(is_profile_selected)
        self.export_button.setEnabled(is_profile_selected)
        self.load_button.setEnabled(is_profile_selected)

    def _create_new_profile(self):
        profile_display_name, ok = QInputDialog.getText(
            self, "Crea Nuovo Profilo",
            "Inserisci il nome visualizzato per il nuovo profilo:",
            QLineEdit.EchoMode.Normal, "Nuovo Profilo"
        )
        if ok and profile_display_name:
            profile_display_name = profile_display_name.strip()
            if not profile_display_name:
                QMessageBox.warning(self, "Nome Vuoto", "Il nome del profilo non può essere vuoto.")
                return

            success, error_msg = self.profile_manager.create_profile(profile_display_name)
            if success:
                app_logger.info(f"Profilo '{profile_display_name}' creato con successo tramite GUI.")
                QMessageBox.information(self, "Profilo Creato", f"Profilo '{profile_display_name}' creato.")
                self.populate_profile_list()
                self.profile_list_updated_signal.emit()
                items = self.list_widget.findItems(profile_display_name, Qt.MatchFlag.MatchExactly)
                if items: self.list_widget.setCurrentItem(items[0])
            else:
                QMessageBox.critical(self, "Errore Creazione Profilo",
                                     f"Impossibile creare il profilo '{profile_display_name}':\n{error_msg or 'Dettagli non disponibili.'}")
        elif ok: # Nome vuoto ma premuto OK
             QMessageBox.warning(self, "Nome Vuoto", "Il nome del profilo non può essere vuoto.")


    def _delete_selected_profile(self):
        display_name = self._get_selected_display_name()
        if not display_name:
            QMessageBox.warning(self, "Nessuna Selezione", "Nessun profilo selezionato da eliminare.")
            return

        reply = QMessageBox.question(
            self, "Conferma Eliminazione",
            f"Sei sicuro di voler eliminare definitivamente il profilo '{display_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel
        )
        if reply == QMessageBox.StandardButton.Yes:
            was_current_profile = (self.profile_manager.get_current_profile_display_name() == display_name)
            success, error_msg = self.profile_manager.delete_profile(display_name)
            if success:
                app_logger.info(f"Profilo '{display_name}' eliminato con successo tramite GUI.")
                QMessageBox.information(self, "Profilo Eliminato", f"Profilo '{display_name}' eliminato.")
                self.populate_profile_list() # Aggiorna la lista visualizzata
                self.profile_list_updated_signal.emit()
                if was_current_profile:
                    # Se il profilo eliminato era quello attivo, MainWindow dovrà gestirlo
                    self.profile_changed_signal.emit()
            else:
                QMessageBox.critical(self, "Errore Eliminazione Profilo",
                                     f"Impossibile eliminare il profilo '{display_name}':\n{error_msg or 'Dettagli non disponibili.'}")

    def _load_selected_and_accept(self):
        display_name = self._get_selected_display_name()
        if not display_name:
            QMessageBox.warning(self, "Nessuna Selezione", "Nessun profilo selezionato da caricare.")
            return

        if self.profile_manager.load_profile(display_name):
            app_logger.info(f"Profilo '{display_name}' caricato tramite ProfileManagementDialog.")
            self.profile_changed_signal.emit() # Segnala che il profilo attivo è cambiato
            self.accept() # Chiude il dialogo con successo
        else:
            QMessageBox.critical(self, "Errore Caricamento Profilo",
                                 f"Impossibile caricare il profilo '{display_name}'. Controlla i log.")

    def _export_selected_profile(self):
        display_name = self._get_selected_display_name()
        if not display_name:
            QMessageBox.warning(self, "Nessuna Selezione", "Nessun profilo selezionato per l'esportazione.")
            return

        safe_name_for_file = self.profile_manager._sanitize_profile_name_for_folder(display_name)
        default_filename = f"{safe_name_for_file}_profilo_{datetime.now().strftime('%Y%m%d')}.zip"
        
        save_file_path, _ = QFileDialog.getSaveFileName(
            self, "Esporta Profilo Selezionato in File ZIP", default_filename, "File ZIP (*.zip)"
        )
        if not save_file_path: return

        # ProfileManager deve fornire il percorso della cartella del profilo.
        profile_source_path = self.profile_manager._get_profile_path_from_safe_name(
            self.profile_manager._sanitize_profile_name_for_folder(display_name)
        )
        if not profile_source_path.is_dir():
            QMessageBox.critical(self, "Errore Esportazione", f"Cartella sorgente del profilo '{display_name}' non trovata.")
            return

        try:
            archive_base_name = Path(save_file_path).with_suffix('')
            # root_dir è la directory genitore della cartella del profilo.
            # base_dir è il nome della cartella del profilo stessa.
            shutil.make_archive(str(archive_base_name), 'zip', root_dir=profile_source_path.parent, base_dir=profile_source_path.name)
            final_zip_path = str(archive_base_name) + ".zip"
            app_logger.info(f"Profilo '{display_name}' esportato in '{final_zip_path}'")
            QMessageBox.information(self, "Esportazione Completata", f"Profilo esportato con successo in:\n{final_zip_path}")
        except Exception as e:
            app_logger.error(f"Errore durante l'esportazione del profilo '{display_name}': {e}", exc_info=True)
            QMessageBox.critical(self, "Errore Esportazione", f"Impossibile esportare il profilo:\n{e}")

    def _import_profile(self):
        zip_file_path, _ = QFileDialog.getOpenFileName(self, "Importa Profilo da File ZIP", "", "File ZIP (*.zip)")
        if not zip_file_path: return

        suggested_profile_name = Path(zip_file_path).stem.replace("_profilo", "").replace("_profile", "")
        new_profile_display_name, ok = QInputDialog.getText(
            self, "Nome per Profilo Importato",
            "Inserisci un nome visualizzato per il profilo da importare:",
            QLineEdit.EchoMode.Normal, suggested_profile_name
        )
        if not (ok and new_profile_display_name and new_profile_display_name.strip()):
            if ok: QMessageBox.warning(self, "Nome Vuoto", "Il nome del profilo non può essere vuoto.")
            return

        new_profile_display_name = new_profile_display_name.strip()
        if self.profile_manager.profile_display_name_exists(new_profile_display_name):
            QMessageBox.warning(self, "Nome Profilo Esistente", f"Un profilo chiamato '{new_profile_display_name}' esiste già.")
            return

        target_safe_folder_name = self.profile_manager._sanitize_profile_name_for_folder(new_profile_display_name)
        target_profile_path = self.profile_manager.profiles_dir / target_safe_folder_name

        if target_profile_path.exists(): # Doppia verifica
            QMessageBox.critical(self, "Errore Importazione", f"La cartella di destinazione '{target_safe_folder_name}' esiste già.")
            return

        try:
            target_profile_path.mkdir(parents=True)
            shutil.unpack_archive(zip_file_path, target_profile_path, 'zip')
            app_logger.info(f"File ZIP '{zip_file_path}' scompattato in '{target_profile_path}'.")

            # Aggiorna display_name nel file settings.json importato
            settings_data = self.profile_manager._load_profile_file(target_profile_path, PROFILE_SETTINGS_FILENAME, {})
            settings_data["display_name"] = new_profile_display_name # Forza il nuovo nome
            # Assicura valori di default se mancanti nel profilo importato
            settings_data.setdefault("whisper_model", DEFAULT_WHISPER_MODEL)
            settings_data.setdefault("language", DEFAULT_LANGUAGE)
            settings_data.setdefault("output_to_internal_editor", INTERNAL_EDITOR_ENABLED_DEFAULT)
            settings_data.setdefault("enable_audio_debug_recording", False)
            self.profile_manager._save_profile_file(target_profile_path, PROFILE_SETTINGS_FILENAME, settings_data)

            QMessageBox.information(self, "Importazione Completata", f"Profilo '{new_profile_display_name}' importato.")
            self.populate_profile_list()
            self.profile_list_updated_signal.emit()
        except Exception as e:
            app_logger.error(f"Errore durante l'importazione da '{zip_file_path}': {e}", exc_info=True)
            QMessageBox.critical(self, "Errore Importazione", f"Impossibile importare il profilo:\n{e}")
            if target_profile_path.exists(): shutil.rmtree(target_profile_path, ignore_errors=True)


# --- Dialogo per le Impostazioni del Profilo Attivo ---
class ProfileSettingsDialog(QDialog):
    profile_settings_changed_signal = pyqtSignal()

    def __init__(self, profile_manager: ProfileManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.profile_manager = profile_manager
        self.setModal(True)

        current_display_name = self.profile_manager.get_current_profile_display_name()
        if not self.profile_manager.current_profile_safe_name or not current_display_name:
            app_logger.error("ProfileSettingsDialog: Tentativo di apertura senza un profilo attivo valido.")
            QTimer.singleShot(0, lambda: QMessageBox.critical(self, "Errore", "Nessun profilo attivo per la configurazione."))
            QTimer.singleShot(0, self.reject)
            return

        self.setWindowTitle(f"Impostazioni Profilo: {current_display_name}")
        self.setMinimumSize(600, 700)

        main_layout = QVBoxLayout(self)
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)

        content_widget = QWidget()
        scroll_area.setWidget(content_widget)
        settings_layout = QVBoxLayout(content_widget)

        # General Settings
        general_group = QGroupBox("Impostazioni Generali del Profilo")
        general_form_layout = QFormLayout()
        self.display_name_edit = QLineEdit(current_display_name)
        general_form_layout.addRow("Nome Visualizzato Profilo:", self.display_name_edit)
        self.model_combo = QComboBox()
        self.model_combo.addItems(AVAILABLE_WHISPER_MODELS)
        self.model_combo.setCurrentText(self.profile_manager.get_profile_setting("whisper_model", DEFAULT_WHISPER_MODEL))
        general_form_layout.addRow("Modello Whisper:", self.model_combo)
        self.output_internal_editor_check = QCheckBox("Scrivi nell'editor interno dell'app")
        self.output_internal_editor_check.setChecked(self.profile_manager.get_profile_setting("output_to_internal_editor", INTERNAL_EDITOR_ENABLED_DEFAULT))
        general_form_layout.addRow(self.output_internal_editor_check)
        self.record_audio_check = QCheckBox("Registra audio per debug (in logs/audio_debugs)")
        self.record_audio_check.setChecked(self.profile_manager.get_profile_setting("enable_audio_debug_recording", False))
        general_form_layout.addRow(self.record_audio_check)
        general_group.setLayout(general_form_layout)
        settings_layout.addWidget(general_group)

        # Macros
        macros_group = self._create_table_groupbox(
            "Macro (Comandi Vocali -> Testo Predefinito)",
            ["Comando Vocale (trigger)", "Testo da Inserire"],
            "macros_table", self._populate_macros_table, self._add_macro_row, self._remove_macro_row
        )
        settings_layout.addWidget(macros_group)

        # Vocabulary
        vocab_group = QGroupBox("Vocabolario Personalizzato (una parola o frase per riga)")
        vocab_layout = QVBoxLayout()
        self.vocab_text_edit = QTextEdit()
        self.vocab_text_edit.setPlaceholderText("Inserisci termini specifici, nomi propri, ecc., per aiutare il riconoscimento.")
        self.vocab_text_edit.setFont(QFont("Monaco", 10))
        self.vocab_text_edit.setMinimumHeight(100)
        self._populate_vocab_text_edit()
        vocab_layout.addWidget(self.vocab_text_edit)
        vocab_group.setLayout(vocab_layout)
        settings_layout.addWidget(vocab_group)

        # Pronunciation Rules
        pron_group = self._create_table_groupbox(
            "Regole di Correzione Pronuncia (Parlato -> Scritto)",
            ["Testo Parlato (come lo dici tu)", "Testo da Scrivere (corretto)"],
            "pron_table", self._populate_pron_table, self._add_pron_rule_row, self._remove_pron_rule_row
        )
        settings_layout.addWidget(pron_group)
        
        settings_layout.addStretch()

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self._accept_changes)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

    def _create_table_groupbox(self, title, headers, table_attr_name, populate_method, add_method, remove_method):
        group = QGroupBox(title)
        layout = QVBoxLayout()
        table_widget = QTableWidget(0, len(headers))
        table_widget.setHorizontalHeaderLabels(headers)
        table_widget.horizontalHeader().setStretchLastSection(True)
        table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table_widget.setAlternatingRowColors(True)
        table_widget.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | 
                                     QAbstractItemView.EditTrigger.SelectedClicked | 
                                     QAbstractItemView.EditTrigger.EditKeyPressed)
        setattr(self, table_attr_name, table_widget)
        populate_method()
        layout.addWidget(table_widget)
        buttons_layout = QHBoxLayout()
        add_button = QPushButton(f"Aggiungi {'Regola' if 'pron' in table_attr_name else 'Macro'}")
        add_button.clicked.connect(add_method)
        buttons_layout.addWidget(add_button)
        remove_button = QPushButton(f"Rimuovi {'Regola' if 'pron' in table_attr_name else 'Macro'} Selezionata")
        remove_button.clicked.connect(remove_method)
        buttons_layout.addWidget(remove_button)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        group.setLayout(layout)
        return group

    def _populate_macros_table(self):
        macros = self.profile_manager.get_macros()
        self.macros_table.setRowCount(0)
        for trigger, expansion in sorted(macros.items()): # Ordina per trigger per coerenza
            row = self.macros_table.rowCount()
            self.macros_table.insertRow(row)
            self.macros_table.setItem(row, 0, QTableWidgetItem(trigger))
            self.macros_table.setItem(row, 1, QTableWidgetItem(expansion))

    def _populate_vocab_text_edit(self):
        self.vocab_text_edit.setPlainText("\n".join(self.profile_manager.get_vocabulary()))

    def _populate_pron_table(self):
        rules = self.profile_manager.get_pronunciation_rules()
        self.pron_table.setRowCount(0)
        for spoken, written in sorted(rules.items()): # Ordina per forma parlata
            row = self.pron_table.rowCount()
            self.pron_table.insertRow(row)
            self.pron_table.setItem(row, 0, QTableWidgetItem(spoken))
            self.pron_table.setItem(row, 1, QTableWidgetItem(written))

    def _add_macro_row(self): self._add_table_row(self.macros_table, "nuovo_comando", "testo espansione")
    def _remove_macro_row(self): self._remove_table_row(self.macros_table)
    def _add_pron_rule_row(self): self._add_table_row(self.pron_table, "parlato", "scritto")
    def _remove_pron_rule_row(self): self._remove_table_row(self.pron_table)

    def _add_table_row(self, table: QTableWidget, default_col1: str, default_col2: str):
        row = table.rowCount()
        table.insertRow(row)
        table.setItem(row, 0, QTableWidgetItem(default_col1))
        table.setItem(row, 1, QTableWidgetItem(default_col2))
        table.scrollToBottom()
        table.selectRow(row)
        table.editItem(table.item(row, 0))

    def _remove_table_row(self, table: QTableWidget):
        current_row = table.currentRow()
        if current_row >= 0:
            table.removeRow(current_row)

    def _accept_changes(self):
        app_logger.info(f"Salvataggio impostazioni per profilo '{self.profile_manager.get_current_profile_display_name()}'.")
        new_display_name = self.display_name_edit.text().strip()
        if not new_display_name:
            QMessageBox.warning(self, "Nome Vuoto", "Il nome visualizzato del profilo non può essere vuoto.")
            return

        current_original_display_name = self.profile_manager.get_current_profile_display_name()
        if new_display_name.lower() != (current_original_display_name.lower() if current_original_display_name else "") and \
           self.profile_manager.profile_display_name_exists(new_display_name):
            QMessageBox.warning(self, "Nome Esistente", f"Un profilo chiamato '{new_display_name}' esiste già.")
            return
        
        self.profile_manager.set_profile_setting("display_name", new_display_name)
        self.profile_manager.set_profile_setting("whisper_model", self.model_combo.currentText())
        self.profile_manager.set_profile_setting("output_to_internal_editor", self.output_internal_editor_check.isChecked())
        self.profile_manager.set_profile_setting("enable_audio_debug_recording", self.record_audio_check.isChecked())

        new_macros = {self.macros_table.item(r, 0).text(): self.macros_table.item(r, 1).text()
                      for r in range(self.macros_table.rowCount()) if self.macros_table.item(r,0) and self.macros_table.item(r,0).text().strip()}
        self.profile_manager.update_macros(new_macros)
        
        self.profile_manager.update_vocabulary(self.vocab_text_edit.toPlainText().splitlines())
        
        new_pron_rules = {self.pron_table.item(r, 0).text(): self.pron_table.item(r, 1).text()
                          for r in range(self.pron_table.rowCount()) if self.pron_table.item(r,0) and self.pron_table.item(r,0).text().strip()}
        self.profile_manager.update_pronunciation_rules(new_pron_rules)

        if self.profile_manager.save_current_profile_data():
            app_logger.info("Impostazioni profilo salvate.")
            QMessageBox.information(self, "Impostazioni Salvate", "Le modifiche al profilo sono state salvate.")
            self.profile_settings_changed_signal.emit()
            self.accept()
        else:
            QMessageBox.critical(self, "Errore Salvataggio", "Impossibile salvare le modifiche al profilo.")


# --- Dialogo per le Impostazioni Globali dell'App ---
class AppSettingsDialog(QDialog):
    settings_changed_signal = pyqtSignal()

    def __init__(self, profile_manager: ProfileManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.profile_manager = profile_manager
        self.setWindowTitle("Impostazioni Globali Applicazione")
        self.setModal(True)
        self.setMinimumWidth(500) # Un po' più largo per nomi dispositivi lunghi

        layout = QVBoxLayout(self)

        log_level_group = QGroupBox("Impostazioni di Logging")
        log_form = QFormLayout()
        self.log_level_combo = QComboBox()
        self.log_levels_available = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        self.log_level_combo.addItems(self.log_levels_available)
        current_log_level = self.profile_manager.get_global_preference("global_log_level", LOG_LEVEL).upper()
        if current_log_level in self.log_levels_available:
            self.log_level_combo.setCurrentText(current_log_level)
        else:
            self.log_level_combo.setCurrentText(LOG_LEVEL)
        log_form.addRow("Livello di dettaglio Log:", self.log_level_combo)
        log_level_group.setLayout(log_form)
        layout.addWidget(log_level_group)

        audio_input_group = QGroupBox("Dispositivo di Input Audio Predefinito")
        audio_form = QFormLayout()
        self.audio_device_combo = QComboBox()
        self.audio_device_combo.setToolTip("Seleziona il microfono da usare per la trascrizione.\nLa modifica avrà effetto al prossimo avvio della trascrizione o cambio profilo.")
        self._populate_audio_devices()
        audio_form.addRow("Microfono:", self.audio_device_combo)
        audio_input_group.setLayout(audio_form)
        layout.addWidget(audio_input_group)

        layout.addStretch()
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self._accept_app_settings)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _populate_audio_devices(self):
        self.audio_device_combo.clear()
        current_selection_restored = False
        try:
            devices = sd.query_devices()
            input_devices_data: List[Dict[str, Any]] = []
            
            app_logger.debug(f"Dispositivi audio trovati da sounddevice: {devices}")

            # Aggiungi opzione "Default di Sistema" per prima
            self.audio_device_combo.addItem("Default di Sistema (consigliato)", userData=None) # userData=None per il default
            
            for i, device_info in enumerate(devices): # device_info è un dict
                if isinstance(device_info, dict) and device_info.get('max_input_channels', 0) > 0:
                    # Costruisci un nome più leggibile, includendo l'host API se disponibile
                    host_api_name = sd.query_hostapis(device_info['hostapi'])['name'] if 'hostapi' in device_info else 'N/A'
                    display_name = f"{device_info['name']} (ID: {device_info['index']}, API: {host_api_name})"
                    
                    # Evita duplicati basati su ID
                    if not any(d['id'] == device_info['index'] for d in input_devices_data):
                        input_devices_data.append({'display': display_name, 'id': device_info['index']})
            
            app_logger.debug(f"Dispositivi di input audio filtrati e formattati: {input_devices_data}")

            saved_device_id = self.profile_manager.get_global_preference("selected_audio_device_id")
            app_logger.debug(f"ID dispositivo audio salvato nelle preferenze: {saved_device_id}")

            # Popola la combo box
            for dev_data in input_devices_data:
                self.audio_device_combo.addItem(dev_data['display'], userData=dev_data['id'])
                if saved_device_id is not None and dev_data['id'] == saved_device_id:
                    # Trova l'indice dell'item appena aggiunto
                    idx_to_select = self.audio_device_combo.findData(dev_data['id'])
                    if idx_to_select != -1:
                        self.audio_device_combo.setCurrentIndex(idx_to_select)
                        current_selection_restored = True
                        app_logger.debug(f"Ripristinata selezione dispositivo: {dev_data['display']}")
            
            if not current_selection_restored: # Se l'ID salvato non è stato trovato o era None
                 self.audio_device_combo.setCurrentIndex(0) # Seleziona "Default di Sistema"
                 app_logger.debug(f"Nessuna corrispondenza per ID salvato o ID era None. Selezionato 'Default di Sistema'.")
            
            if self.audio_device_combo.count() == 1 and self.audio_device_combo.itemData(0) is None: # Solo "Default"
                app_logger.warning("Nessun dispositivo di input audio specifico trovato, solo 'Default di Sistema'.")
        
        except Exception as e:
            app_logger.error(f"Errore durante il recupero o popolamento dei dispositivi audio: {e}", exc_info=True)
            self.audio_device_combo.clear()
            self.audio_device_combo.addItem("Errore caricamento dispositivi", userData=None)
            self.audio_device_combo.setEnabled(False)

    def _accept_app_settings(self):
        new_log_level_str = self.log_level_combo.currentText()
        self.profile_manager.save_global_preference("global_log_level", new_log_level_str)
        app_logger.info(f"Livello log globale salvato come: {new_log_level_str}.")
        
        selected_device_id = self.audio_device_combo.currentData() # userData (ID o None)
        self.profile_manager.save_global_preference("selected_audio_device_id", selected_device_id)
        if selected_device_id is not None:
            app_logger.info(f"ID Dispositivo audio preferito salvato: {selected_device_id} ({self.audio_device_combo.currentText()}).")
        else:
            app_logger.info("Dispositivo audio preferito impostato a 'Default di Sistema'.")

        self.settings_changed_signal.emit()
        self.accept()