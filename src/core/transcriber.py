# src/core/transcriber.py
import whisper
import sounddevice as sd
import numpy as np
import time
import queue
from threading import Thread, Lock
import wave 
from datetime import datetime

from src.config import (
    DEFAULT_WHISPER_MODEL, DEFAULT_LANGUAGE, AVAILABLE_WHISPER_MODELS, LOGS_DIR,
    DEFAULT_WHISPER_TEMPERATURE,
    AUDIO_SAMPLE_RATE, AUDIO_CHANNELS, AUDIO_BLOCK_DURATION_S,
    AUDIO_SILENCE_THRESHOLD_S, AUDIO_MAX_BUFFER_S_INTERIM,
    AUDIO_MIN_SPEECH_FOR_SILENCE_S, AUDIO_MIN_CHUNK_FOR_FINAL_S
)
from src.utils.logger import app_logger
from src.core.profile_manager import ProfileManager
from typing import Optional, Callable, Any, List


class Transcriber:
    def __init__(self, profile_manager: ProfileManager,
                 on_transcription_callback: Optional[Callable[[str], None]] = None,
                 on_status_update_callback: Optional[Callable[[str], None]] = None):
        self.profile_manager = profile_manager
        self.on_transcription_callback = on_transcription_callback
        self.on_status_update_callback = on_status_update_callback

        self.is_listening = False
        self.audio_queue: queue.Queue[np.ndarray] = queue.Queue()
        self.model: Optional[whisper.Whisper] = None
        self.stream: Optional[sd.InputStream] = None
        self.model_lock = Lock()
        self.processing_thread: Optional[Thread] = None
        self.current_model_name: Optional[str] = None
        self.current_language: Optional[str] = None
        self.selected_audio_device_id: Optional[int] = None

        self.enable_audio_debug_recording = False
        self.debug_audio_writer: Optional[wave.Wave_write] = None

        self._load_global_audio_device_preference()
        self.reload_model_and_settings() 

    def _load_global_audio_device_preference(self):
        device_id = self.profile_manager.get_global_preference("selected_audio_device_id")
        if device_id is not None:
            try:
                self.selected_audio_device_id = int(device_id)
                app_logger.info(f"Dispositivo audio preferito caricato: ID {self.selected_audio_device_id}")
            except ValueError:
                app_logger.warning(f"ID dispositivo audio '{device_id}' non valido. Uso default.")
                self.selected_audio_device_id = None
        else:
            app_logger.info("Nessun dispositivo audio preferito. Uso default di sistema.")
            self.selected_audio_device_id = None

    def _update_status(self, message: str):
        if self.on_status_update_callback:
            self.on_status_update_callback(message)
        app_logger.info(f"[Transcriber Status] {message}")

    def reload_model_and_settings(self):
        with self.model_lock:
            new_model_name = self.profile_manager.get_profile_setting("whisper_model", DEFAULT_WHISPER_MODEL)
            new_language = self.profile_manager.get_profile_setting("language", DEFAULT_LANGUAGE)
            self.enable_audio_debug_recording = self.profile_manager.get_profile_setting("enable_audio_debug_recording", False)
            
            app_logger.info(f"Transcriber: Ricarica impostazioni: Modello='{new_model_name}', Lingua='{new_language}', DebugAudio={self.enable_audio_debug_recording}")

            if new_model_name not in AVAILABLE_WHISPER_MODELS:
                app_logger.warning(f"Modello Whisper '{new_model_name}' non valido. Uso default '{DEFAULT_WHISPER_MODEL}'.")
                new_model_name = DEFAULT_WHISPER_MODEL

            if self.model is None or self.current_model_name != new_model_name or self.current_language != new_language:
                self._update_status(f"Caricamento modello Whisper '{new_model_name}' (lingua: {new_language})...")
                app_logger.info(f"Transcriber: Inizio caricamento effettivo del modello '{new_model_name}' (da cache o download).") # <--- LOG AGGIUNTO QUI
                try:
                    self.model = whisper.load_model(new_model_name)
                    self.current_model_name = new_model_name
                    self.current_language = new_language
                    app_logger.info(f"Transcriber: Modello '{self.current_model_name}' (lingua: {self.current_language}) caricato.")
                    self._update_status(f"Modello '{self.current_model_name}' pronto.")
                except Exception as e:
                    app_logger.error(f"Transcriber: Fallimento caricamento modello '{new_model_name}': {e}", exc_info=True)
                    self._update_status(f"Errore caricamento modello: {str(e)[:100]}...")
                    self.model = None
                    self.current_model_name = None
                    self.current_language = None
            else:
                app_logger.info(f"Transcriber: Modello '{self.current_model_name}' (lingua: {self.current_language}) è già configurato.")
                self._update_status(f"Modello '{self.current_model_name}' pronto.")
    
    # ... (TUTTO IL RESTO DEL CODICE DI TRANSCRIBER.PY RIMANE IDENTICO ALLA VERSIONE CHE TI HO FORNITO PRIMA - File 13 / ID 9r6vwm8k4cm93)
    # _start_debug_recording, _stop_debug_recording, _audio_callback, _process_audio_queue, start_listening, stop_listening, if __name__ == '__main__'

    def _start_debug_recording(self):
        if self.enable_audio_debug_recording and not self.debug_audio_writer:
            try:
                debug_audio_dir = LOGS_DIR / "audio_debugs"
                debug_audio_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filename = debug_audio_dir / f"debug_audio_{timestamp}.wav"
                self.debug_audio_writer = wave.open(str(filename), 'wb')
                self.debug_audio_writer.setnchannels(AUDIO_CHANNELS)
                self.debug_audio_writer.setsampwidth(2)
                self.debug_audio_writer.setframerate(AUDIO_SAMPLE_RATE)
                app_logger.info(f"Avviata registrazione audio di debug su: {filename}")
            except Exception as e:
                app_logger.error(f"Impossibile avviare registrazione audio di debug: {e}", exc_info=True)
                self.debug_audio_writer = None

    def _stop_debug_recording(self):
        if self.debug_audio_writer:
            writer_to_close = self.debug_audio_writer
            self.debug_audio_writer = None
            try:
                writer_to_close.close()
                app_logger.info("Registrazione audio di debug fermata e file salvato.")
            except Exception as e:
                app_logger.error(f"Errore chiusura file WAV di debug: {e}", exc_info=True)

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info: Any, status: sd.CallbackFlags):
        if status: app_logger.warning(f"Stato stream audio (callback): {status}")
        if self.is_listening:
            self.audio_queue.put(indata.copy())
            if self.enable_audio_debug_recording and self.debug_audio_writer:
                try:
                    audio_int16 = (indata.flatten() * 32767).astype(np.int16)
                    self.debug_audio_writer.writeframes(audio_int16.tobytes())
                except Exception as e:
                    app_logger.error(f"Errore scrittura WAV di debug: {e}")

    def _process_audio_queue(self):
        recorded_audio_chunks: List[np.ndarray] = []
        last_speech_time = time.monotonic()
        currently_processing_transcription = False
        accumulated_audio_duration_for_interim = 0.0
        app_logger.info("Thread di processamento audio avviato.")
        while self.is_listening or not self.audio_queue.empty():
            process_now = False; is_final_chunk_due_to_stop = False
            try:
                audio_chunk = self.audio_queue.get(block=True, timeout=0.05)
                recorded_audio_chunks.append(audio_chunk)
                current_chunk_duration = len(audio_chunk) / AUDIO_SAMPLE_RATE
                accumulated_audio_duration_for_interim += current_chunk_duration
                last_speech_time = time.monotonic()
                self.audio_queue.task_done()
            except queue.Empty:
                if not self.is_listening and not recorded_audio_chunks: break
                current_time = time.monotonic(); time_since_last_speech = current_time - last_speech_time
                if self.is_listening and recorded_audio_chunks and not currently_processing_transcription:
                    total_buffered_s = sum(len(chk) for chk in recorded_audio_chunks) / AUDIO_SAMPLE_RATE
                    if time_since_last_speech > AUDIO_SILENCE_THRESHOLD_S and total_buffered_s >= AUDIO_MIN_SPEECH_FOR_SILENCE_S:
                        process_now = True; app_logger.debug(f"Processo SILENZIO ({time_since_last_speech:.2f}s). Buffer: {total_buffered_s:.2f}s")
                    elif accumulated_audio_duration_for_interim >= AUDIO_MAX_BUFFER_S_INTERIM:
                        process_now = True; app_logger.debug(f"Processo BUFFER INTERMEDIO ({accumulated_audio_duration_for_interim:.2f}s).")
                elif not self.is_listening and recorded_audio_chunks and not currently_processing_transcription:
                    total_buffered_s = sum(len(chk) for chk in recorded_audio_chunks) / AUDIO_SAMPLE_RATE
                    if total_buffered_s >= AUDIO_MIN_CHUNK_FOR_FINAL_S:
                        process_now = True; is_final_chunk_due_to_stop = True; app_logger.debug(f"Processo STOP (residuo: {total_buffered_s:.2f}s).")
                    else:
                        recorded_audio_chunks = []; accumulated_audio_duration_for_interim = 0.0
            if process_now:
                currently_processing_transcription = True
                audio_np = np.concatenate(recorded_audio_chunks).astype(np.float32).flatten()
                recorded_audio_chunks = []; accumulated_audio_duration_for_interim = 0.0
                app_logger.info(f"Invio a Whisper: {len(audio_np)/AUDIO_SAMPLE_RATE:.2f}s di audio.")
                initial_prompt_str = None
                transcribe_options = {"language": self.current_language, "fp16": False, "temperature": DEFAULT_WHISPER_TEMPERATURE}
                if initial_prompt_str: transcribe_options["initial_prompt"] = initial_prompt_str
                try:
                    with self.model_lock:
                        if not self.model:
                            app_logger.error("Modello Whisper non disponibile in _process_audio_queue."); self._update_status("Errore: Modello non pronto."); currently_processing_transcription = False; continue
                        result = self.model.transcribe(audio_np, **transcribe_options)
                    transcribed_text = result["text"].strip()
                    app_logger.info(f"Whisper ha trascritto: {repr(transcribed_text)}")
                    if transcribed_text and self.on_transcription_callback: self.on_transcription_callback(transcribed_text)
                except Exception as e: app_logger.error(f"Errore trascrizione Whisper: {e}", exc_info=True); self._update_status(f"Errore trascrizione: {str(e)[:70]}...")
                finally: currently_processing_transcription = False
            if is_final_chunk_due_to_stop and not recorded_audio_chunks: break
            if not self.is_listening and self.audio_queue.empty() and not recorded_audio_chunks: break
        app_logger.info("Thread di processamento audio (_process_audio_queue) terminato.")

    def start_listening(self) -> bool:
        if self.is_listening: app_logger.warning("Ascolto già attivo."); return True
        self.reload_model_and_settings()
        if not self.model: self._update_status("Errore Critico: Modello non caricabile."); return False
        self._load_global_audio_device_preference()
        self.is_listening = True
        self._update_status("Avvio stream audio...")
        if self.enable_audio_debug_recording: self._start_debug_recording()
        try:
            while not self.audio_queue.empty():
                try: self.audio_queue.get_nowait()
                except queue.Empty: break
                self.audio_queue.task_done()
            app_logger.info(f"Avvio stream audio su dispositivo ID: {self.selected_audio_device_id if self.selected_audio_device_id is not None else 'Default'}")
            self.stream = sd.InputStream(device=self.selected_audio_device_id, samplerate=AUDIO_SAMPLE_RATE, channels=AUDIO_CHANNELS, dtype='float32', blocksize=int(AUDIO_SAMPLE_RATE * AUDIO_BLOCK_DURATION_S), callback=self._audio_callback)
            self.stream.start()
            app_logger.info(f"Stream avviato su: {self.stream.device_name if hasattr(self.stream, 'device_name') else self.stream.device}")
            if not self.processing_thread or not self.processing_thread.is_alive():
                app_logger.info("Avvio nuovo thread processamento audio.")
                self.processing_thread = Thread(target=self._process_audio_queue, name="AudioProcessingThread", daemon=True)
                self.processing_thread.start()
            else: app_logger.info("Thread processamento audio già attivo.")
            self._update_status("Ascolto...")
            return True
        except Exception as e:
            self.is_listening = False; error_detail = str(e)
            app_logger.error(f"Errore avvio stream audio: {error_detail}", exc_info=True); self._update_status(f"Errore avvio audio: {error_detail[:70]}...")
            if self.stream:
                try:
                    if self.stream.active: self.stream.stop()
                    self.stream.close()
                except Exception as e_close: app_logger.error(f"Errore chiusura stream fallito: {e_close}")
                self.stream = None
            self._stop_debug_recording(); return False

    def stop_listening(self):
        if not self.is_listening and not (hasattr(self, 'stream') and self.stream and self.stream.active):
            app_logger.info("Trascrittore non in ascolto o stream già fermo.")
            if self.enable_audio_debug_recording: self._stop_debug_recording()
            if self.is_listening: self.is_listening = False
            return
        app_logger.info("Richiesta stop ascolto per Transcriber.")
        self._update_status("Arresto in corso...")
        self.is_listening = False
        if self.enable_audio_debug_recording: self._stop_debug_recording()
        if hasattr(self, 'stream') and self.stream:
            stream_to_close = self.stream; self.stream = None
            try:
                if stream_to_close.active: stream_to_close.stop(); app_logger.debug("Stream audio (sounddevice) stoppato.")
                stream_to_close.close(); app_logger.info("Stream audio (sounddevice) chiuso.")
            except Exception as e: app_logger.error(f"Errore stop/chiusura stream: {e}", exc_info=True)
        if hasattr(self, 'processing_thread') and self.processing_thread and self.processing_thread.is_alive():
            app_logger.info("Attesa terminazione thread processamento audio...")
            timeout_join = AUDIO_MAX_BUFFER_S_INTERIM + AUDIO_SILENCE_THRESHOLD_S + 2.0
            self.processing_thread.join(timeout=timeout_join)
            if self.processing_thread.is_alive(): app_logger.warning(f"Thread processamento audio non terminato (timeout {timeout_join}s).")
            else: app_logger.info("Thread processamento audio terminato.")
            self.processing_thread = None
        self._update_status("Trascrizione Stoppata.")
        app_logger.info("Processo di stop_listening completato.")

if __name__ == '__main__':
    app_logger.info("Avvio test Transcriber standalone (versione riscritta)...")
    class MockProfileManager:
        def __init__(self):
            self.current_profile_data = {
                "settings": {"whisper_model": DEFAULT_WHISPER_MODEL, "language": DEFAULT_LANGUAGE, "display_name": "Profilo Test Standalone", "enable_audio_debug_recording": True, "output_to_internal_editor": True},
                "vocabulary": ["TrascriviPro", "PyQt6", "Supercalifragilistichespiralidoso"], "macros": {}, "pronunciation_rules": {}
            }
            self.global_app_preferences = {"selected_audio_device_id": None}
        def get_profile_setting(self, key, default): return self.current_profile_data["settings"].get(key, default)
        def get_vocabulary(self): return self.current_profile_data["vocabulary"]
        def get_current_profile_display_name(self): return self.current_profile_data["settings"].get("display_name")
        def get_global_preference(self, key, default=None): return self.global_app_preferences.get(key, default)
    mock_pm = MockProfileManager()
    all_transcriptions: List[str] = []
    def transcription_received_callback(text: str): print(f"\n>>> TRASCRIZIONE RICEVUTA (TEST): {repr(text)}\n"); all_transcriptions.append(text)
    def status_update_callback(status: str): print(f"--- STATO TRASCRITTORE (TEST): {status} ---")
    try:
        if not LOGS_DIR.exists(): LOGS_DIR.mkdir(parents=True, exist_ok=True)
        if not (LOGS_DIR / "audio_debugs").exists(): (LOGS_DIR / "audio_debugs").mkdir(parents=True, exist_ok=True)
        transcriber = Transcriber(profile_manager=mock_pm, on_transcription_callback=transcription_received_callback, on_status_update_callback=status_update_callback)
        if not transcriber.model: print("ERRORE TEST: Modello non caricato."); exit(1)
        print(f"\nINFO TEST: Soglie: SILENCE={AUDIO_SILENCE_THRESHOLD_S}s, BUFFER={AUDIO_MAX_BUFFER_S_INTERIM}s. DebugAudio: {transcriber.enable_audio_debug_recording}. Modello: {transcriber.current_model_name}\n")
        input("TEST: Premi Invio per avviare ascolto...")
        if transcriber.start_listening():
            print("TEST: Ascolto avviato..."); time_to_listen = 10;
            for i in range(time_to_listen): print(f"TEST: Parla... ({time_to_listen - i}s)", end='\r'); time.sleep(1)
            print("\nTEST: Fermo trascrizione..."); transcriber.stop_listening(); time.sleep(1)
            print("\n--- Test completato ---"); print("Trascrizioni:", all_transcriptions)
            if transcriber.enable_audio_debug_recording: print(f"\nControlla WAV in {LOGS_DIR / 'audio_debugs'}")
        else: print("ERRORE TEST: Avvio ascolto fallito.")
    except Exception as e_general: print(f"ERRORE IMPREVISTO TEST Transcriber: {e_general}", exc_info=True)