# src/core/text_processor.py
import re
from typing import Optional

from src.config import SPECIAL_COMMANDS # Per is_special_command
from src.utils.logger import app_logger
from src.core.profile_manager import ProfileManager

# Comandi di formattazione espliciti che il TextProcessor gestirà.
# Le chiavi DEVONO essere minuscole.
EXPLICIT_FORMATTING_COMMANDS = {
    "a capo": "\n",
    "nuova riga": "\n",
    "paragrafo": "\n\n",
    # "tab": "\t", # Decidi se mantenere "tab" come comando esplicito
    # "tabulazione": "\t"
}
# Ordina per lunghezza decrescente per un matching corretto (es. "nuova riga" prima di "riga" se esistesse)
SORTED_EXPLICIT_FORMATTING_KEYS = sorted(EXPLICIT_FORMATTING_COMMANDS.keys(), key=len, reverse=True)


class TextProcessor:
    def __init__(self, profile_manager: ProfileManager):
        self.profile_manager = profile_manager
        app_logger.debug("TextProcessor (versione semplificata per punteggiatura automatica Whisper) inizializzato.")

    def is_special_command(self, text: str) -> bool:
        """Controlla se il testo è un comando speciale definito in config.py (es. stop)."""
        return text.strip().lower() in SPECIAL_COMMANDS

    def process_text(self, raw_text: str) -> str:
        """
        Processa il testo grezzo da Whisper.
        Con questa strategia, ci si affida a Whisper per la punteggiatura standard.
        Questo processore gestisce:
        1. Macro.
        2. Regole di correzione pronuncia.
        3. Comandi vocali espliciti ("a capo", "paragrafo").
        4. Capitalizzazione di base.
        """
        if not raw_text:
            app_logger.debug("TextProcessor: Ricevuto testo grezzo vuoto.")
            return ""

        if not self.profile_manager.current_profile_safe_name:
            app_logger.warning("TextProcessor: Nessun profilo attivo. Restituisco testo grezzo (solo strip).")
            return raw_text.strip()

        current_profile_display_name = self.profile_manager.get_current_profile_display_name() or \
                                       self.profile_manager.current_profile_safe_name
        
        # Inizia con il testo grezzo, dopo un primo strip.
        # La conversione a minuscolo verrà fatta solo per il matching di comandi/macro/regole,
        # cercando di preservare la capitalizzazione originale di Whisper.
        processed_text = raw_text.strip()
        
        app_logger.info(f"TextProcessor per profilo '{current_profile_display_name}': Originale (strip)='{processed_text}'")

        # --- 1. Applicazione Macro ---
        # Le macro vengono applicate prima, poiché potrebbero inserire testo che include
        # parole chiave per la correzione della pronuncia o comandi di formattazione.
        macros = self.profile_manager.get_macros() # Chiavi già in minuscolo
        if macros:
            text_before_macros = processed_text
            sorted_macro_triggers = sorted(macros.keys(), key=len, reverse=True)
            for trigger_lower in sorted_macro_triggers:
                # Cerca il trigger in modo case-insensitive nel testo corrente
                pattern = re.compile(r'\b' + re.escape(trigger_lower) + r'\b', re.IGNORECASE)
                expansion = macros[trigger_lower]
                # La sostituzione avviene sul testo 'processed_text' che mantiene la sua capitalizzazione.
                # L'espansione viene inserita così com'è.
                processed_text = pattern.sub(expansion, processed_text)
            if text_before_macros != processed_text:
                 app_logger.debug(f"Testo dopo macro: {repr(processed_text)}")

        # --- 2. Applicazione Regole di Correzione Pronuncia ---
        pronunciation_rules = self.profile_manager.get_pronunciation_rules() # Chiavi già in minuscolo
        if pronunciation_rules:
            text_before_pronunciation = processed_text
            sorted_pronunciation_spoken_lower = sorted(pronunciation_rules.keys(), key=len, reverse=True)
            for spoken_form_lower in sorted_pronunciation_spoken_lower:
                written_form = pronunciation_rules[spoken_form_lower]
                pattern = re.compile(r'\b' + re.escape(spoken_form_lower) + r'\b', re.IGNORECASE)
                processed_text = pattern.sub(written_form, processed_text)
            if text_before_pronunciation != processed_text:
                app_logger.debug(f"Testo dopo correzione pronuncia: {repr(processed_text)}")

        # Se il testo è diventato vuoto dopo macro/pronuncia, esci.
        if not processed_text.strip():
            app_logger.info("Testo vuoto dopo macro/correzioni pronuncia.")
            return ""

        # --- 3. Gestione Comandi di Formattazione Espliciti ("a capo", "paragrafo") ---
        # Questi comandi sono specifici e sovrascrivono il testo se lo matchano.
        # È importante che il matching sia preciso.
        
        # Primo, controlla se l'INTERO testo (ignorando spazi e case) è un comando esplicito.
        text_lower_stripped = processed_text.strip().lower()
        if text_lower_stripped in EXPLICIT_FORMATTING_COMMANDS:
            symbol = EXPLICIT_FORMATTING_COMMANDS[text_lower_stripped]
            app_logger.debug(f"Rilevato comando di formattazione esplicito solitario: '{text_lower_stripped}' -> '{repr(symbol)}'.")
            return symbol # Restituisce solo il simbolo (\n o \n\n)

        # Altrimenti, cerca i comandi all'interno del testo.
        # Questo è più complesso perché dobbiamo gestire gli spazi correttamente.
        # Useremo una tecnica di split e join controllata.
        
        # Crea un pattern regex che matcha qualsiasi dei comandi espliciti o sequenze di non-spazi (parole)
        # o sequenze di spazi. L'ordine in SORTED_EXPLICIT_FORMATTING_KEYS è importante.
        command_regex_parts = [r'\b' + re.escape(key) + r'\b' for key in SORTED_EXPLICIT_FORMATTING_KEYS]
        # Pattern per matchare parole (non comandi e non spazi) o spazi
        # \S+ matcha non-spazi, \s+ matcha spazi.
        # L'ordine qui è importante: comandi prima, poi non-spazi, poi spazi.
        tokenizer_pattern = re.compile(r'|'.join(command_regex_parts) + r'|(\S+)|(\s+)', re.IGNORECASE)
        
        tokens = tokenizer_pattern.findall(processed_text)
        # findall con gruppi restituirà tuple. Dobbiamo appiattire e filtrare.
        # Ogni tupla avrà un solo elemento non vuoto (corrispondente al gruppo che ha matchato).
        processed_tokens: List[str] = []
        
        # Ricostruisci la lista dei token effettivi (parole, comandi, spazi)
        # Questo approccio di tokenizzazione con regex è potente ma può essere complesso.
        # Alternativa più semplice e robusta per pochi comandi: sostituzioni regex iterative.
        
        # Scegliamo sostituzioni regex iterative per "a capo" e "paragrafo"
        # perché sono meno di altri comandi di punteggiatura e la logica è più semplice.
        temp_text = processed_text
        for spoken_command in SORTED_EXPLICIT_FORMATTING_KEYS:
            symbol = EXPLICIT_FORMATTING_COMMANDS[spoken_command]
            # Sostituisci il comando, cercando di gestire gli spazi attorno in modo sensato.
            # Pattern: (opzionale testo prima)(spazio opz)COMANDO(spazio opz)(opzionale testo dopo)
            # Sostituisce " comando " con "simbolo", "testo comando " con "testosimbolo ", " comando testo" con "simbolo testo"
            
            # Sostituzione 1: comando con spazi da entrambi i lati
            pattern1 = re.compile(r'\s+' + re.escape(spoken_command) + r'\s+', re.IGNORECASE)
            temp_text = pattern1.sub(symbol, temp_text) # " ciao a capo ciao " -> " ciao\nciao "

            # Sostituzione 2: comando alla fine con spazio prima
            pattern2 = re.compile(r'\s+' + re.escape(spoken_command) + r'$', re.IGNORECASE)
            temp_text = pattern2.sub(symbol, temp_text) # " ciao a capo" -> " ciao\n"
            
            # Sostituzione 3: comando all'inizio con spazio dopo
            pattern3 = re.compile(r'^' + re.escape(spoken_command) + r'\s+', re.IGNORECASE)
            temp_text = pattern3.sub(symbol, temp_text) # "a capo ciao " -> "\nciao "

        processed_text = temp_text
        app_logger.debug(f"Testo dopo sostituzione comandi formattazione: {repr(processed_text)}")


        # --- 4. Pulizia Finale degli Spazi ---
        # Questa fase è cruciale per l'aspetto finale del testo.
        if processed_text:
            # Rimuovi spazi multipli (eccetto \n, \t se presenti)
            processed_text = re.sub(r'[ \t]+', ' ', processed_text)
            
            # Gestisci spazi attorno a newline e tab
            # " \n " -> "\n"; "test \n test" -> "test\ntest"
            processed_text = re.sub(r'\s*([\n\t])\s*', r'\1', processed_text)
            
            # Rimuovi spazi all'inizio/fine, ma preserva un singolo \n o \n\n se è tutto ciò che rimane.
            stripped_text = processed_text.strip()
            if not stripped_text and processed_text in EXPLICIT_FORMATTING_COMMANDS.values():
                # Se lo strip ha rimosso tutto, ma il testo originale (non strippato) era un \n o \n\n,
                # allora mantieni quel carattere.
                pass # processed_text è già \n o \n\n
            else:
                processed_text = stripped_text
        
        app_logger.debug(f"Testo dopo pulizia spazi finale: {repr(processed_text)}")

        # --- 5. Capitalizzazione Finale ---
        # Applica solo se c'è testo e non è solo un carattere di controllo come \n.
        if processed_text and not (len(processed_text) <= 2 and all(c in '\n\t\r' for c in processed_text)):
            # Capitalizza il primo carattere alfabetico della stringa
            # Cerca il primo carattere che sia una lettera (considerando anche accentate)
            first_letter_match = re.search(r'[a-zA-Zà-üÀ-Ü]', processed_text)
            if first_letter_match:
                idx = first_letter_match.start()
                processed_text = processed_text[:idx] + processed_text[idx].upper() + processed_text[idx+1:]

            # Capitalizza dopo . ! ? (se inseriti da Whisper) seguito da uno o più spazi e una lettera minuscola
            processed_text = re.sub(r'([.!?]\s+)([a-zà-ü])', 
                                    lambda match_obj: match_obj.group(1) + match_obj.group(2).upper(), 
                                    processed_text)
            
            # Capitalizza dopo i nostri comandi \n o \t (e eventuali spazi residui) seguito da una lettera minuscola
            processed_text = re.sub(r'([\n\t]+\s*)([a-zà-ü])', 
                                    lambda match_obj: match_obj.group(1) + match_obj.group(2).upper(), 
                                    processed_text)
        
        app_logger.info(f"TextProcessor output finale: {repr(processed_text)}")
        return processed_text


if __name__ == '__main__':
    app_logger.info("Avvio test TextProcessor (versione semplificata per punteggiatura automatica Whisper)...")

    class MockProfileManager: # Uguale al precedente
        def __init__(self):
            self.current_profile_safe_name = "test_profile_simple"
            self._macros = {}
            self._pronunciation_rules = {}
            self._settings = {"display_name": "Test Profile Semplice"}
        def get_current_profile_display_name(self): return self._settings.get("display_name")
        def get_macros(self): return self._macros
        def add_macro(self, trigger, expansion): self._macros[trigger.lower()] = expansion
        def get_pronunciation_rules(self): return self._pronunciation_rules
        def add_pronunciation_rule(self, spoken, written): self._pronunciation_rules[spoken.lower()] = written

    pm = MockProfileManager()
    processor = TextProcessor(profile_manager=pm)
    pm.add_macro("firma dottore", "Dr. Mario Rossi\nSpecialista in Cardiologia")
    pm.add_pronunciation_rule("otorino laringo iatra", "otorinolaringoiatra")

    tests = [
        # Comandi di formattazione espliciti
        ("a capo", "\n"),
        ("  A CAPO  ", "\n"),
        ("test a capo", "Test\n"), # Dopo "Test", "a capo" da solo diventa \n
        ("test a capo altra parola", "Test\naltra parola"),
        ("paragrafo", "\n\n"),
        ("test paragrafo test", "Test\n\ntest"),
        ("  paragrafo  ", "\n\n"),
        # Macro e regole di pronuncia
        ("controllo otorino laringo iatra", "Controllo otorinolaringoiatra"),
        ("saluti firma dottore", "Saluti Dr. Mario Rossi\nSpecialista in Cardiologia"),
        # Testo con punteggiatura da Whisper (simulata)
        ("questa è una frase.", "Questa è una frase."),
        ("come stai?", "Come stai?"),
        ("ottimo!", "Ottimo!"),
        ("frase uno. a capo frase due.", "Frase uno.\nFrase due."),
        ("frase uno.paragrafo frase due.", "Frase uno.\n\nFrase due."), # Spazio mancante, ma paragrafo dovrebbe funzionare
        ("testo normale senza comandi", "Testo normale senza comandi"),
        # Casi limite
        ("", ""),
        ("    ", ""),
        ("   a capo   ", "\n"), # Spazi esterni devono essere rimossi
        ("   test   a capo   test   ", "Test\ntest"),
        ("Test con    spazi    multipli", "Test con spazi multipli"),
        # Test con comandi misti e punteggiatura Whisper
        ("Referto del paziente. firma dottore a capo Data odierna.", "Referto del paziente. Dr. Mario Rossi\nSpecialista in Cardiologia\nData odierna."),
        ("Punto interrogativo a capo", "Punto interrogativo\n"), # "punto interrogativo" non è un comando esplicito qui
        ("Test.A capo", "Test.\n"), # Senza spazio dopo il punto
        ("Test,a capo", "Test,\n"), # Senza spazio dopo la virgola
    ]

    print("\n--- Esecuzione Test TextProcessor (Versione Semplificata Finale) ---")
    all_tests_passed = True
    for i, (original, expected) in enumerate(tests):
        print(f"\n--- Test {i+1} ---")
        print(f"Originale Whisper (simulato): '{original}'")
        result = processor.process_text(original)
        print(f"Processato: {repr(result)} (Atteso: {repr(expected)})")
        if result != expected:
            print(f"!!!! TEST FALLITO !!!!")
            all_tests_passed = False

    if all_tests_passed:
        print("\nSUCCESS: Tutti i test principali (versione semplificata finale) sono passati!")
    else:
        print("\nFAILURE: Alcuni test principali (versione semplificata finale) sono falliti.")

    print("\n--- Test TextProcessor completati ---")