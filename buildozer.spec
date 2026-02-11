[app]
# (str) Title of your application
title = Family Hub

# (str) Package name
package.name = familyhub

# (str) Package domain (needed for android packaging)
package.domain = org.family

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json,sqlite3,ttc

# (list) List of inclusions using pattern matching
#source.include_patterns = assets/*,images/*.png

# (list) Source files to exclude (let empty to include nothing)
#source.exclude_exts = spec

# (list) List of directory to exclude (let empty to include nothing)
#source.exclude_dirs = tests, bin, venv

# (list) List of exclusions using pattern matching
#source.exclude_patterns = license,images/*/*.jpg

# (str) Application versioning (method 1)
version = 0.1

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy==2.3.0,kivymd,plyer,pillow,google-generativeai,requests,certifi,urllib3,idna,charset-normalizer,matplotlib,python-dotenv,pg8000,scramp,openssl

# (str) Custom source folders for requirements
# packgage.source.kivymd = ../../kivymd

# (list) Garden requirements
#garden_requirements =

# (list) Presplash of the application
#presplash.filename = %(source.dir)s/assets/presplash.png

# (list) Icon of the application
#icon.filename = %(source.dir)s/assets/icon.png

# (str) Supported orientations (landscape, portrait or all)
orientation = portrait

# (list) List of architectures to build for (e.g. armeabi-v7a, arm64-v8a)
android.archs = arm64-v8a, armeabi-v7a

# (list) Android permissions
android.permissions = INTERNET, CAMERA, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, ACCESS_NETWORK_STATE

# (int) Target Android API, should be as high as possible (specific to each NDK)
android.api = 34

# (int) Minimum API your APK will support.
android.minapi = 24

# (bool) Automatic SDK license acceptance
android.accept_sdk_license = True

# (str) Android NDK version to use
#android.ndk = 25b

# (bool) skip setup py to compile (recommended)
#android.skip_setup_py = False

# (list) The Android archs to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
#android.archs = arm64-v8a

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = off, 1 = on)
warn_on_root = 1
