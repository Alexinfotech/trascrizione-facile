# src/core/output_handler.py
import pyautogui
import time # Per eventuali piccole pause, sebbene non usate attivamente ora
from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QTextCursor # Importa QTextCursor per operazioni sul cursore
from typing import Optional

from src.utils.logger import app_logger

class OutputHandler:
    def __init__(self, internal_editor_widget: Optional[QTextEdit] = None):
        self.internal_editor: Optional[QTextEdit] = internal_editor_widget
        self.use_internal_editor: bool = False
        app_logger.info("OutputHandler inizializzato.")

    def set_output_mode(self, use_internal: bool, internal_editor_widget: Optional[QTextEdit] = None):
        self.use_internal_editor = use_internal
        if internal_editor_widget is not None:
            self.internal_editor = internal_editor_widget

        if self.use_internal_editor:
            if self.internal_editor is None:
                app_logger.warning("Modalità editor interno selezionata ma widget QTextEdit non fornito.")
            else:
                app_logger.info("Output impostato su editor interno.")
        else:
            app_logger.info("Output impostato su applicazione esterna (pyautogui).")

    def type_text(self, text: str):
        if text is None:
            app_logger.debug("OutputHandler: type_text chiamato con testo None.")
            return
        if not text and text != "\n": # Permetti a "\n" di passare, ma non a ""
            app_logger.debug("OutputHandler: type_text chiamato con testo vuoto (non newline).")
            return

        if self.use_internal_editor and self.internal_editor:
            self._type_to_internal_editor(text)
        else:
            self._type_to_external_app(text)

    def _type_to_internal_editor(self, text: str):
        if self.internal_editor is None:
            app_logger.error("Tentativo di scrivere su editor interno, ma il widget non è disponibile.")
            return
        try:
            cursor = self.internal_editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End) # Vai alla fine del testo

            current_doc_text = self.internal_editor.toPlainText()
            needs_leading_space = False

            # --- INIZIO LOGICA SPAZIATURA MIGLIORATA + LOGGING DETTAGLIATO ---
            text_starts_with_space_like = text.startswith((' ', '\n', '\t'))
            last_char_is_space_like_or_paren = False
            last_char_val = "N/A (editor vuoto o primo inserimento)"

            if current_doc_text: # Se c'è già del testo
                last_char_val = current_doc_text[-1]
                last_char_is_space_like_or_paren = last_char_val in (' ', '\n', '\t', '(')
                
                app_logger.debug(f"OutputHandler Check Spazio PRE-DECISIONE: text='{repr(text)}', "
                                 f"text_starts_space_like={text_starts_with_space_like}, "
                                 f"last_char_in_editor='{repr(last_char_val)}', "
                                 f"last_char_is_space_like_or_paren={last_char_is_space_like_or_paren}")

                if not text_starts_with_space_like and not last_char_is_space_like_or_paren:
                    needs_leading_space = True
            else: # Editor era vuoto prima di questo inserimento
                app_logger.debug(f"OutputHandler Check Spazio PRE-DECISIONE (editor era vuoto): text='{repr(text)}', "
                                 f"text_starts_space_like={text_starts_with_space_like}")
            
            # Log della decisione iniziale su needs_leading_space
            app_logger.debug(f"OutputHandler Check Spazio DECISIONE INIZIALE: needs_leading_space={needs_leading_space} per text='{repr(text)}'")

            # Se il testo da inserire è solo un newline, non aggiungere spazi iniziali.
            if text == "\n":
                if needs_leading_space: # Se era stato deciso di aggiungere uno spazio...
                    app_logger.debug(f"OutputHandler: text è newline ('\\n'), needs_leading_space resettato da True a False.")
                needs_leading_space = False # Sovrascrive la decisione precedente
            
            if needs_leading_space:
                cursor.insertText(" ")
                app_logger.info("OutputHandler: SPAZIO PRINCIPALE INSERITO.") # LOG MODIFICATO A INFO
            else:
                # Logghiamo perché lo spazio non è stato inserito, se non è un newline
                if text != "\n":
                    if not current_doc_text:
                        app_logger.debug(f"OutputHandler: Spazio principale non inserito (editor era vuoto). Text: '{repr(text)}'")
                    elif text_starts_with_space_like:
                        app_logger.debug(f"OutputHandler: Spazio principale non inserito (testo inizia già con carattere tipo spazio). Text: '{repr(text)}'")
                    elif last_char_is_space_like_or_paren:
                        app_logger.debug(f"OutputHandler: Spazio principale non inserito (ultimo carattere editor era tipo spazio o '('). Last char: '{repr(last_char_val)}'. Text: '{repr(text)}'")
                    else:
                        # Questo caso indica che needs_leading_space è False ma nessuna delle condizioni sopra lo spiega.
                        # Potrebbe essere perché text era "\n" e poi è cambiato, o un bug.
                        app_logger.warning(f"OutputHandler: Spazio principale NON inserito, e le ragioni standard non sembrano applicarsi. "
                                           f"needs_leading_space={needs_leading_space}, text='{repr(text)}', "
                                           f"last_char_val='{repr(last_char_val)}', editor_vuoto={not bool(current_doc_text)}, "
                                           f"text_starts_space_like={text_starts_with_space_like}, "
                                           f"last_char_is_space_like_or_paren={last_char_is_space_like_or_paren}")
            # --- FINE LOGICA SPAZIATURA MIGLIORATA + LOGGING DETTAGLIATO ---

            cursor.insertText(text) # Inserisce il testo così com'è
            app_logger.info(f"Testo '{repr(text)}' inserito nell'editor interno.") # Questo log è già buono

            self.internal_editor.setTextCursor(cursor) # Applica il cursore
            self.internal_editor.ensureCursorVisible()

        except Exception as e:
            app_logger.error(f"Errore scrittura su editor interno: {e}", exc_info=True)

    def _type_to_external_app(self, text: str):
        try:
            pyautogui.typewrite(text, interval=0.01)
            app_logger.info(f"Testo '{repr(text)}' digitato con pyautogui.")
        except Exception as e:
            app_logger.error(f"Errore durante la digitazione con pyautogui: {e}", exc_info=True)


if __name__ == '__main__':
    # Mantieni la parte __main__ per testare OutputHandler isolatamente se necessario,
    # ma per il problema attuale, il test integrato nell'app è più rilevante.
    # Assicurati che il logger sia configurato se esegui questo stand-alone.
    # from src.config import LOG_LEVEL, APP_NAME, LOGS_DIR
    # from src.utils.logger import setup_logger
    # if not LOGS_DIR.exists(): LOGS_DIR.mkdir(parents=True, exist_ok=True)
    # app_logger = setup_logger(logger_name=APP_NAME + "-TestOH", log_file_path=LOGS_DIR / "test_output_handler.log", level_name="DEBUG")
    
    app_logger.info("Avvio test OutputHandler (versione con logging spaziatura dettagliato)...")

    # --- Test PyAutoGUI ---
    handler_external = OutputHandler()
    handler_external.set_output_mode(False)

    print("\n--- Test PyAutoGUI ---")
    print("ATTENZIONE: Assicurati che un editor di testo abbia il focus per i prossimi test!")
    test_strings_pyautogui = [
        "Test output esterno 1. ", "Altra riga con a capo.\nE ancora.",
        "\n", "Test dopo un singolo a capo.", "Fine test pyautogui.\n\n"
    ]
    # for i, s in enumerate(test_strings_pyautogui):
    #     print(f"Test PyAutoGUI {i+1}: tra 3 secondi, digiterò: {repr(s)}")
    #     time.sleep(3)
    #     handler_external.type_text(s)
    print("--- Test PyAutoGUI saltati in questa esecuzione (decommentare per testare). ---")
    
    # --- Test Editor Interno (simulato con logging) ---
    print("\n--- Test Editor Interno (simulato con logging) ---")
    # Per testare questo blocco, è necessario un ambiente Qt.
    # Per ora, ci affidiamo ai log generati dall'app completa.
    # Se necessario, si può decommentare e adattare questo per test isolati.
    
    # Esempio di simulazione logica senza GUI completa:
    class MockQTextEdit:
        def __init__(self): self.text_content = ""
        def toPlainText(self): return self.text_content
        def textCursor(self): return MockQTextCursor(self)
        def setTextCursor(self, cursor): pass
        def ensureCursorVisible(self): pass

    class MockQTextCursor:
        def __init__(self, editor): self.editor = editor; self.pos = len(editor.text_content)
        def movePosition(self, op):
            if op == QTextCursor.MoveOperation.End: self.pos = len(self.editor.text_content)
        def insertText(self, text_to_insert):
            self.editor.text_content = self.editor.text_content[:self.pos] + text_to_insert + self.editor.text_content[self.pos:]
            self.pos += len(text_to_insert)

    mock_editor = MockQTextEdit()
    handler_internal_test = OutputHandler(internal_editor_widget=mock_editor)
    handler_internal_test.set_output_mode(True, internal_editor_widget=mock_editor)

    app_logger.info("--- Inizio test simulato OutputHandler con MockQTextEdit ---")
    test_segments = [
        "Prima frase.",
        "Seconda frase.", # Atteso spazio tra "frase." e "Seconda"
        "\n",
        "Dopo un a capo.",
        "Test(parentesi)",
        "Altro testo", # Atteso spazio tra ")Test(parentesi)" e "Altro" (no, tra parentesi) e "testo"
        "Fine."
    ]
    for segment in test_segments:
        app_logger.info(f"Simulazione type_text con: {repr(segment)}")
        handler_internal_test.type_text(segment)
        app_logger.info(f"Stato editor simulato: {repr(mock_editor.toPlainText())}\n")
    
    app_logger.info("--- Test simulato OutputHandler completato ---")
    print("\nControlla i log per i dettagli sulla spaziatura (cerca 'OutputHandler Check Spazio' e 'SPAZIO PRINCIPALE').")
    print("--- Test OutputHandler completati. ---")