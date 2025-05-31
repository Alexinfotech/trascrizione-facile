# TrascriviPro Avanzato.spec
# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

block_cipher = None

# --- DETERMINA PERCORSI IMPORTANTI ---
project_root = os.getcwd()
src_path = os.path.join(project_root, 'src')

print(f"INFO: Project root (from .spec CWD) determined as: {project_root}")
print(f"INFO: Src path determined as: {src_path}")

app_icon_name = 'app_icon.icns' # Assicurati che questo file sia nella root del progetto
app_icon_path_str = os.path.join(project_root, app_icon_name)

if not os.path.exists(app_icon_path_str):
    print(f"ATTENZIONE: File icona '{app_icon_path_str}' non trovato. L'app non avrà un'icona personalizzata.")
    app_icon_path_str = None
else:
    print(f"INFO: Icona trovata: {app_icon_path_str}")

# -------------------------------------------------------------

# Elenco degli hidden imports necessari
hidden_imports_list = [
    'sounddevice',
    '_sounddevice_cffi',
    'pyautogui',
    'pynput',
    'pynput.keyboard._mac',
    'pynput.mouse._mac',
    'PIL',
    'whisper',
    # 'whisper.assets', # Non più necessario qui se lo includiamo nei datas
    'torch',
    'torchaudio',
    'tiktoken',
    'tiktoken_ext.cl100k_base',
    'numba',
    'llvmlite',
    'tqdm',
    'regex',
    'requests',
    'charset_normalizer',
    'idna',
    'urllib3',
    'certifi',
    'filelock',
    'jinja2',
    'networkx',
    'sympy',
    'mpmath',
    'fsspec',
    'appdirs',
    'packaging',
    'cffi',
    'pycparser',
    'PyQt6.sip',
    'PyQt6.QtNetwork',
    'PyQt6.QtPrintSupport',
    'PyQt6.QtGui',
    'PyQt6.QtCore',
    'PyQt6.QtWidgets',
    'PyQt6.QtMultimedia',
    'sklearn',
    'sklearn.utils._typedefs',
    'sklearn.neighbors._ball_tree',
    'pandas'
]

# Dati da includere
datas_to_include = []
if app_icon_path_str:
    datas_to_include.append((app_icon_path_str, '.')) # Copia l'icona nella root del bundle (es. Contents/Resources)

# --- INCLUDI GLI ASSETS DI WHISPER ---
# Percorso identificato dall'utente per la directory 'assets' di whisper nel suo venv
whisper_assets_source_path = '/Users/alessandrotornabene/.pyenv/versions/3.9.20/lib/python3.9/site-packages/whisper/assets'
if os.path.exists(whisper_assets_source_path) and os.path.isdir(whisper_assets_source_path):
    datas_to_include.append((whisper_assets_source_path, 'whisper/assets'))
    print(f"INFO: Assets di Whisper da includere da: {whisper_assets_source_path} a 'whisper/assets'")
else:
    # Questo dovrebbe essere un errore fatale se il percorso non è valido
    raise FileNotFoundError(f"ERRORE CRITICO: La directory assets di Whisper '{whisper_assets_source_path}' non esiste o non è una directory. Impossibile costruire.")
# ------------------------------------

# --- INCLUDI FFMPEG (TENTATIVO) ---
# Trova ffmpeg nel PATH di sistema. Questo è un tentativo, potrebbe non essere robusto.
# Su macOS, ffmpeg installato con Homebrew è spesso in /opt/homebrew/bin/ffmpeg (per Apple Silicon)
# o /usr/local/bin/ffmpeg (per Intel).
# Dobbiamo trovare il binario e includerlo.
ffmpeg_path = None
possible_ffmpeg_paths = ['/opt/homebrew/bin/ffmpeg', '/usr/local/bin/ffmpeg']
import shutil
system_ffmpeg_path = shutil.which('ffmpeg') # Prova a trovarlo nel PATH dell'ambiente di build

if system_ffmpeg_path:
    ffmpeg_path = system_ffmpeg_path
    print(f"INFO: Trovato ffmpeg nel PATH di build: {ffmpeg_path}")
else:
    for p in possible_ffmpeg_paths:
        if os.path.exists(p):
            ffmpeg_path = p
            print(f"INFO: Trovato ffmpeg in percorso predefinito: {ffmpeg_path}")
            break

binaries_to_include = []
if ffmpeg_path:
    binaries_to_include.append((ffmpeg_path, '.')) # Copia ffmpeg nella root dell'eseguibile (es. Contents/MacOS)
    print(f"INFO: ffmpeg sarà incluso da: {ffmpeg_path}")
else:
    print("ATTENZIONE: ffmpeg non trovato automaticamente. Whisper potrebbe non funzionare se non è già nel PATH di sistema dell'utente finale o se il codice non lo trova.")
# ------------------------------------


a = Analysis(
    ['src/main.py'],
    pathex=[project_root, src_path],
    binaries=binaries_to_include, # Aggiunto ffmpeg qui
    datas=datas_to_include,
    hiddenimports=hidden_imports_list,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TrascriviPro Avanzato',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False, # Imposta a True per debug se l'app non si avvia per vedere output del bootloader
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=app_icon_path_str
)

app = BUNDLE(
    exe,
    name='TrascriviPro Avanzato.app',
    icon=app_icon_path_str,
    bundle_identifier='com.alessandrotornabene.trascrivipro', # RICORDA DI PERSONALIZZARLO
    info_plist={
        'CFBundleName': 'TrascriviPro',
        'CFBundleDisplayName': 'TrascriviPro Avanzato',
        'CFBundleGetInfoString': 'TrascriviPro Avanzato, versione 1.0.1',
        'CFBundleIdentifier': 'com.alessandrotornabene.trascrivipro', # DEVE CORRISPONDERE
        'CFBundleShortVersionString': '1.0.1',
        'CFBundleVersion': '1.0.1',
        'LSMinimumSystemVersion': '11.0',
        'NSHumanReadableCopyright': 'Copyright © 2024 Alessandro Tornabene. Tutti i diritti riservati.',
        'NSPrincipalClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
        'LSApplicationCategoryType': 'public.app-category.productivity',
        'NSMicrophoneUsageDescription': 'L\'accesso al microfono è richiesto per la trascrizione vocale.',
        'NSSpeechRecognitionUsageDescription': 'Il riconoscimento vocale è utilizzato per convertire il parlato in testo.',
        'NSAppleEventsUsageDescription': 'L\'app necessita del permesso per controllare altre applicazioni e inviare testo (per la funzione di scrittura esterna).',
        'CFBundleExecutable': 'TrascriviPro Avanzato',
    }
)