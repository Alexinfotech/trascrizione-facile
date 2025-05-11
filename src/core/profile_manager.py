# src/core/profile_manager.py
import json
import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple

from src.config import (
    PROFILES_DIR, APP_PREFERENCES_FILE, LOG_LEVEL,
    MACROS_FILENAME, VOCABULARY_FILENAME, PRONUNCIATION_RULES_FILENAME, PROFILE_SETTINGS_FILENAME,
    DEFAULT_WHISPER_MODEL, DEFAULT_LANGUAGE, INTERNAL_EDITOR_ENABLED_DEFAULT
)
from src.utils.logger import app_logger

class ProfileManager:
    def __init__(self):
        self.profiles_dir: Path = PROFILES_DIR
        self.app_prefs_file: Path = APP_PREFERENCES_FILE

        if not self.app_prefs_file.parent.exists():
            app_logger.warning(f"La directory base delle preferenze {self.app_prefs_file.parent} non esiste. Tentativo di crearla.")
            try:
                self.app_prefs_file.parent.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                app_logger.error(f"Impossibile creare la directory base delle preferenze: {e}", exc_info=True)
        
        if not self.profiles_dir.exists():
            app_logger.warning(f"La directory dei profili {self.profiles_dir} non esiste. Tentativo di crearla.")
            try:
                self.profiles_dir.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                app_logger.error(f"Impossibile creare la directory dei profili: {e}", exc_info=True)

        self.current_profile_safe_name: Optional[str] = None
        self.current_profile_data: Dict[str, Any] = {}
        self.global_app_preferences: Dict[str, Any] = {}
        self._load_app_preferences()

    # --- INIZIO CORREZIONE: Aggiunta di _get_available_profiles_internal ---
    def _get_available_profiles_internal(self) -> Dict[str, str]:
        """
        Scansiona la directory dei profili e restituisce una mappa {safe_name: display_name}.
        Questo è un metodo helper interno. Per l'uso esterno, get_available_profiles() restituisce List[str].
        """
        profiles_map: Dict[str, str] = {}
        if self.profiles_dir.exists() and self.profiles_dir.is_dir():
            for item_path in self.profiles_dir.iterdir():
                if item_path.is_dir():  # Ogni sottocartella è un potenziale profilo
                    # Leggi il display_name dal file settings.json del profilo
                    settings_data = self._load_profile_file(item_path, PROFILE_SETTINGS_FILENAME, {})
                    display_name = settings_data.get("display_name")
                    
                    # Verifica minima di validità: deve avere un display_name
                    if display_name and isinstance(display_name, str) and display_name.strip():
                        profiles_map[item_path.name] = display_name.strip() # item_path.name è il safe_name (nome cartella)
                    else:
                        app_logger.warning(
                            f"Cartella profilo '{item_path.name}' ignorata: display_name mancante o non valido in '{PROFILE_SETTINGS_FILENAME}'.")
        app_logger.debug(f"_get_available_profiles_internal trovati: {profiles_map}")
        return profiles_map
    # --- FINE CORREZIONE ---

    def _load_app_preferences(self):
        default_prefs = {
            "last_used_profile_safe_name": None,
            "selected_audio_device_id": None,
            "global_log_level": LOG_LEVEL
        }
        try:
            if self.app_prefs_file and self.app_prefs_file.exists():
                with open(self.app_prefs_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        self.global_app_preferences = default_prefs.copy()
                    else:
                        self.global_app_preferences = json.loads(content)
                        for key, value in default_prefs.items():
                            self.global_app_preferences.setdefault(key, value)
            else:
                self.global_app_preferences = default_prefs.copy()
        except Exception as e:
            app_logger.error(f"Errore caricamento preferenze app: {e}. Uso default.", exc_info=True)
            self.global_app_preferences = default_prefs.copy()

        last_profile_safe_name = self.global_app_preferences.get("last_used_profile_safe_name")
        if last_profile_safe_name:
            app_logger.info(f"Tentativo di caricare l'ultimo profilo usato (safe_name): {last_profile_safe_name}")
            # Usa _get_available_profiles_internal per ottenere il display_name
            available_profiles_map = self._get_available_profiles_internal() # CORRETTO: ora esiste
            display_name_to_load = available_profiles_map.get(last_profile_safe_name)

            if display_name_to_load:
                if self.load_profile(display_name_to_load): # load_profile usa display_name
                    app_logger.info(f"Ultimo profilo '{display_name_to_load}' caricato con successo.")
                else:
                    app_logger.warning(f"Impossibile caricare l'ultimo profilo '{display_name_to_load}' (safe_name: {last_profile_safe_name}).")
                    self.global_app_preferences["last_used_profile_safe_name"] = None
            else:
                app_logger.warning(f"Safe_name dell'ultimo profilo '{last_profile_safe_name}' non trovato tra i profili disponibili. Resetto.")
                self.global_app_preferences["last_used_profile_safe_name"] = None
        else:
            app_logger.info("Nessun ultimo profilo salvato o impossibile determinarlo.")


    def _save_app_preferences(self):
        if not self.app_prefs_file:
            app_logger.error("Percorso file preferenze app non definito. Impossibile salvare.")
            return False
        try:
            self.app_prefs_file.parent.mkdir(parents=True, exist_ok=True)
            if self.current_profile_safe_name:
                self.global_app_preferences["last_used_profile_safe_name"] = self.current_profile_safe_name
            else:
                self.global_app_preferences["last_used_profile_safe_name"] = None
            with open(self.app_prefs_file, 'w', encoding='utf-8') as f:
                json.dump(self.global_app_preferences, f, indent=4, ensure_ascii=False)
            app_logger.info(f"Preferenze app salvate in {self.app_prefs_file}")
            return True
        except Exception as e:
            app_logger.error(f"Errore salvataggio preferenze app in {self.app_prefs_file}: {e}", exc_info=True)
            return False

    def get_global_preference(self, key: str, default: Any = None) -> Any:
        return self.global_app_preferences.get(key, default)

    def save_global_preference(self, key: str, value: Any):
        self.global_app_preferences[key] = value
        self._save_app_preferences()

    def _sanitize_profile_name_for_folder(self, display_name: str) -> str:
        name = display_name.strip()
        name = "".join(c if c.isalnum() or c in [' ', '-', '_'] else '_' for c in name)
        name = name.replace(' ', '_')
        while "__" in name: name = name.replace("__", "_")
        name = name.strip('_') 
        if not name: name = "profilo_senza_nome"
        return name[:50].lower()

    def _get_profile_path_from_safe_name(self, safe_name: str) -> Path:
        return self.profiles_dir / safe_name

    def _load_profile_file(self, profile_dir_path: Path, filename: str, default_value: Any = None) -> Any:
        file_path = profile_dir_path / filename
        actual_default = default_value
        if actual_default is None:
            if filename == VOCABULARY_FILENAME: actual_default = []
            elif filename in [PROFILE_SETTINGS_FILENAME, MACROS_FILENAME, PRONUNCIATION_RULES_FILENAME]: actual_default = {}
            else: actual_default = {} 
        
        if file_path.exists() and file_path.is_file():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        app_logger.warning(f"File profilo '{file_path}' è vuoto. Uso default: {actual_default}.")
                        return actual_default
                    return json.loads(content)
            except json.JSONDecodeError:
                app_logger.error(f"Errore decodifica JSON per '{file_path}'. Uso default: {actual_default}.", exc_info=True)
                return actual_default
            except Exception as e:
                app_logger.error(f"Errore imprevisto caricamento file profilo '{file_path}': {e}", exc_info=True)
                return actual_default
        else:
            app_logger.debug(f"File profilo '{file_path}' non trovato. Uso default: {actual_default}.")
            return actual_default

    def _save_profile_file(self, profile_dir_path: Path, filename: str, data: Any) -> bool:
        if not profile_dir_path.exists():
            try:
                profile_dir_path.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                app_logger.error(f"Impossibile creare directory profilo '{profile_dir_path}' per salvare '{filename}': {e}", exc_info=True)
                return False
        
        file_path = profile_dir_path / filename
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            app_logger.debug(f"File '{filename}' salvato per profilo '{profile_dir_path.name}'.")
            return True
        except Exception as e:
            app_logger.error(f"Errore salvataggio file profilo '{file_path}': {e}", exc_info=True)
            return False

    def _get_display_name_from_safe_name(self, safe_name: str) -> Optional[str]:
        # Questo metodo ora usa _get_available_profiles_internal per coerenza
        profiles_map = self._get_available_profiles_internal()
        return profiles_map.get(safe_name)


    def get_available_profiles(self) -> List[str]:
        """Restituisce una lista ordinata di nomi visualizzati unici dei profili validi."""
        profiles_map = self._get_available_profiles_internal() # Usa il metodo helper
        unique_display_names = sorted(list(set(profiles_map.values())))
        app_logger.debug(f"Profili disponibili (display names): {unique_display_names}")
        return unique_display_names

    def profile_display_name_exists(self, display_name: str) -> bool:
        normalized_display_name = display_name.strip().lower()
        if not normalized_display_name: return False
        # _get_available_profiles_internal() restituisce {safe_name: display_name}
        # Dobbiamo controllare i valori (display_name)
        for existing_display_name in self._get_available_profiles_internal().values():
            if existing_display_name.lower() == normalized_display_name:
                return True
        return False

    def create_profile(self, display_name: str) -> Tuple[bool, Optional[str]]:
        display_name = display_name.strip()
        if not display_name:
            msg = "Il nome visualizzato del profilo non può essere vuoto."
            app_logger.warning(msg); return False, msg
        if self.profile_display_name_exists(display_name):
            msg = f"Un profilo con nome visualizzato '{display_name}' esiste già."
            app_logger.warning(msg); return False, msg

        safe_folder_name = self._sanitize_profile_name_for_folder(display_name)
        profile_path = self.profiles_dir / safe_folder_name
        if profile_path.exists():
            msg = f"Conflitto: la cartella di profilo '{safe_folder_name}' (per '{display_name}') esiste già."
            app_logger.error(msg); return False, msg
            
        try:
            profile_path.mkdir(parents=True, exist_ok=True)
            default_settings = {
                "display_name": display_name,
                "whisper_model": DEFAULT_WHISPER_MODEL, "language": DEFAULT_LANGUAGE,
                "output_to_internal_editor": INTERNAL_EDITOR_ENABLED_DEFAULT,
                "enable_audio_debug_recording": False
            }
            success = True
            success &= self._save_profile_file(profile_path, PROFILE_SETTINGS_FILENAME, default_settings)
            success &= self._save_profile_file(profile_path, MACROS_FILENAME, {})
            success &= self._save_profile_file(profile_path, VOCABULARY_FILENAME, [])
            success &= self._save_profile_file(profile_path, PRONUNCIATION_RULES_FILENAME, {})
            if not success: raise OSError("Fallimento salvataggio uno o più file del profilo.")
            app_logger.info(f"Profilo '{display_name}' (cartella: {safe_folder_name}) creato."); return True, None
        except Exception as e:
            error_msg = f"Errore creazione profilo '{display_name}': {e}"
            app_logger.error(error_msg, exc_info=True)
            if profile_path.exists():
                try: shutil.rmtree(profile_path); app_logger.info(f"Pulita cartella profilo '{profile_path}'.")
                except Exception as e_del: app_logger.error(f"Errore pulizia cartella '{profile_path}': {e_del}", exc_info=True)
            return False, error_msg

    def load_profile(self, display_name: str) -> bool:
        display_name = display_name.strip()
        if not display_name: app_logger.warning("Tentativo caricamento profilo con nome vuoto."); return False

        actual_profile_path_to_load = None
        actual_safe_name_to_load = None
        
        # CORRETTO: Usa _get_available_profiles_internal
        available_profiles_map = self._get_available_profiles_internal()
        for s_name, d_name_from_file in available_profiles_map.items():
            if d_name_from_file.lower() == display_name.lower():
                actual_profile_path_to_load = self._get_profile_path_from_safe_name(s_name)
                actual_safe_name_to_load = s_name
                break
        
        if not (actual_profile_path_to_load and actual_profile_path_to_load.exists() and actual_profile_path_to_load.is_dir()):
            app_logger.error(f"Profilo con nome visualizzato '{display_name}' non trovato o cartella non valida.")
            return False
        
        try:
            settings = self._load_profile_file(actual_profile_path_to_load, PROFILE_SETTINGS_FILENAME, {})
            settings.setdefault("display_name", display_name)
            settings.setdefault("whisper_model", DEFAULT_WHISPER_MODEL)
            settings.setdefault("language", DEFAULT_LANGUAGE)
            settings.setdefault("output_to_internal_editor", INTERNAL_EDITOR_ENABLED_DEFAULT)
            settings.setdefault("enable_audio_debug_recording", False)

            self.current_profile_data = {
                "settings": settings,
                "macros": self._load_profile_file(actual_profile_path_to_load, MACROS_FILENAME, {}),
                "vocabulary": self._load_profile_file(actual_profile_path_to_load, VOCABULARY_FILENAME, []),
                "pronunciation_rules": self._load_profile_file(actual_profile_path_to_load, PRONUNCIATION_RULES_FILENAME, {})
            }
            self.current_profile_safe_name = actual_safe_name_to_load
            app_logger.info(f"Profilo '{settings['display_name']}' (cartella: {self.current_profile_safe_name}) caricato.")
            self.save_global_preference("last_used_profile_safe_name", self.current_profile_safe_name)
            return True
        except Exception as e:
            app_logger.error(f"Errore caricamento dati profilo '{display_name}': {e}", exc_info=True)
            self.current_profile_safe_name = None; self.current_profile_data = {}
            return False

    def get_current_profile_display_name(self) -> Optional[str]:
        if self.current_profile_data and "settings" in self.current_profile_data:
            return self.current_profile_data["settings"].get("display_name")
        return None

    def delete_profile(self, display_name_to_delete: str) -> Tuple[bool, Optional[str]]:
        display_name_to_delete = display_name_to_delete.strip()
        if not display_name_to_delete:
            msg = "Nome profilo da eliminare non può essere vuoto."; app_logger.warning(msg); return False, msg

        safe_name_to_delete = None
        # CORRETTO: Usa _get_available_profiles_internal
        profiles_map = self._get_available_profiles_internal()
        for s_name, d_name in profiles_map.items():
            if d_name.lower() == display_name_to_delete.lower():
                safe_name_to_delete = s_name; break
        
        if not safe_name_to_delete:
            msg = f"Profilo '{display_name_to_delete}' non trovato per eliminazione."; app_logger.warning(msg); return False, msg
            
        profile_path_to_delete = self._get_profile_path_from_safe_name(safe_name_to_delete)
        try:
            if profile_path_to_delete.exists():
                shutil.rmtree(profile_path_to_delete)
                app_logger.info(f"Profilo '{display_name_to_delete}' (cartella: {safe_name_to_delete}) eliminato.")
                if self.current_profile_safe_name == safe_name_to_delete:
                    self.current_profile_safe_name = None; self.current_profile_data = {}
                    self.save_global_preference("last_used_profile_safe_name", None)
                return True, None
            else:
                msg = f"Cartella profilo '{profile_path_to_delete}' non trovata."; app_logger.error(msg); return False, msg
        except Exception as e:
            error_msg = f"Errore eliminazione profilo '{display_name_to_delete}': {e}"; app_logger.error(error_msg, exc_info=True); return False, error_msg

    def save_current_profile_data(self) -> bool:
        if not self.current_profile_safe_name or not self.current_profile_data:
            app_logger.warning("Nessun profilo corrente caricato per salvare."); return False
        
        profile_path = self._get_profile_path_from_safe_name(self.current_profile_safe_name)
        display_name = self.get_current_profile_display_name() or self.current_profile_safe_name.replace("_"," ")
            
        try:
            if "settings" not in self.current_profile_data: self.current_profile_data["settings"] = {}
            self.current_profile_data["settings"]["display_name"] = display_name
            success = True
            success &= self._save_profile_file(profile_path, PROFILE_SETTINGS_FILENAME, self.current_profile_data.get("settings", {}))
            success &= self._save_profile_file(profile_path, MACROS_FILENAME, self.get_macros())
            success &= self._save_profile_file(profile_path, VOCABULARY_FILENAME, self.get_vocabulary())
            success &= self._save_profile_file(profile_path, PRONUNCIATION_RULES_FILENAME, self.get_pronunciation_rules())
            if success: app_logger.info(f"Dati profilo '{display_name}' salvati."); return True
            else: app_logger.error(f"Fallimento salvataggio uno o più file per profilo '{display_name}'."); return False
        except Exception as e:
            app_logger.error(f"Errore salvataggio dati profilo '{display_name}': {e}", exc_info=True); return False

    def get_profile_setting(self, key: str, default: Any = None) -> Any:
        if not self.current_profile_data: return default
        return self.current_profile_data.get("settings", {}).get(key, default)

    def set_profile_setting(self, key: str, value: Any):
        if not self.current_profile_data: app_logger.warning("Set setting: nessun profilo caricato."); return
        if "settings" not in self.current_profile_data: self.current_profile_data["settings"] = {}
        self.current_profile_data["settings"][key] = value

    def get_macros(self) -> Dict[str, str]:
        if not self.current_profile_data: return {}
        return self.current_profile_data.get("macros", {})

    def update_macros(self, new_macros: Dict[str, str]):
        if not self.current_profile_data: app_logger.warning("Update macros: nessun profilo caricato."); return
        self.current_profile_data["macros"] = {k.strip().lower(): v for k, v in new_macros.items() if k.strip()}

    def get_vocabulary(self) -> List[str]:
        if not self.current_profile_data: return []
        return self.current_profile_data.get("vocabulary", [])

    def update_vocabulary(self, new_vocab_list: List[str]):
        if not self.current_profile_data: app_logger.warning("Update vocabulary: nessun profilo caricato."); return
        self.current_profile_data["vocabulary"] = sorted(list(set(word.strip() for word in new_vocab_list if word.strip())))

    def get_pronunciation_rules(self) -> Dict[str, str]:
        if not self.current_profile_data: return {}
        return self.current_profile_data.get("pronunciation_rules", {})

    def update_pronunciation_rules(self, new_rules: Dict[str, str]):
        if not self.current_profile_data: app_logger.warning("Update pron. rules: nessun profilo caricato."); return
        self.current_profile_data["pronunciation_rules"] = {k.strip().lower(): v for k, v in new_rules.items() if k.strip()}

    def add_macro(self, trigger: str, expansion: str):
        trigger = trigger.strip().lower();
        if not trigger: return
        if "macros" not in self.current_profile_data: self.current_profile_data["macros"] = {}
        self.current_profile_data["macros"][trigger] = expansion
            
    def remove_macro(self, trigger: str):
        trigger = trigger.strip().lower()
        if "macros" in self.current_profile_data and trigger in self.current_profile_data["macros"]:
            del self.current_profile_data["macros"][trigger]

    def add_pronunciation_rule(self, spoken: str, written: str):
        spoken = spoken.strip().lower()
        if not spoken: return
        if "pronunciation_rules" not in self.current_profile_data: self.current_profile_data["pronunciation_rules"] = {}
        self.current_profile_data["pronunciation_rules"][spoken] = written

    def remove_pronunciation_rule(self, spoken: str):
        spoken = spoken.strip().lower()
        if "pronunciation_rules" in self.current_profile_data and spoken in self.current_profile_data["pronunciation_rules"]:
            del self.current_profile_data["pronunciation_rules"][spoken]


if __name__ == '__main__':
    app_logger.info("Avvio test dettagliato ProfileManager (versione riscritta)...")
    
    test_base_path = Path.cwd() / "test_app_data_pm_v2" # Nuova cartella per questo test
    test_profiles_dir = test_base_path / PROFILES_DIR_NAME
    test_app_prefs_file = test_base_path / APP_PREFERENCES_FILENAME

    if test_base_path.exists(): shutil.rmtree(test_base_path)
    test_base_path.mkdir(parents=True)
    
    original_profiles_dir, PROFILES_DIR = PROFILES_DIR, test_profiles_dir
    original_app_prefs_file, APP_PREFERENCES_FILE = APP_PREFERENCES_FILE, test_app_prefs_file
    
    pm = ProfileManager()
    
    print(f"\n--- Test ProfileManager con path: {test_profiles_dir} ---")
    print(f"Prefs: {pm.global_app_preferences}, Curr Prof: {pm.get_current_profile_display_name()}, Avail: {pm.get_available_profiles()}")

    p1_name = "Profilo Test 1"
    s_p1, m_p1 = pm.create_profile(p1_name)
    print(f"Crea '{p1_name}': {s_p1}, {m_p1}. Profili: {pm.get_available_profiles()}")

    if s_p1:
        if pm.load_profile(p1_name):
            print(f"OK: Caricato '{p1_name}'. Modello: {pm.get_profile_setting('whisper_model')}")
            pm.set_profile_setting("whisper_model", "medium")
            pm.update_macros({"testmacro": "espansione test"})
            if pm.save_current_profile_data():
                print("OK: Dati profilo salvati.")
                if pm.load_profile(p1_name): # Ricarica
                    print(f"OK: Ricaricato '{p1_name}'. Modello: {pm.get_profile_setting('whisper_model')}, Macros: {pm.get_macros()}")
        else: print(f"FALLIMENTO caricamento '{p1_name}'")
    
    s_del, m_del = pm.delete_profile(p1_name)
    print(f"Elimina '{p1_name}': {s_del}, {m_del}. Profili: {pm.get_available_profiles()}")
    print(f"Curr Prof dopo delete: {pm.get_current_profile_display_name()}")
    print(f"Last used in prefs: {pm.get_global_preference('last_used_profile_safe_name')}")

    PROFILES_DIR, APP_PREFERENCES_FILE = original_profiles_dir, original_app_prefs_file
    print(f"\n--- Test ProfileManager completati. Cartella test: {test_base_path} ---")