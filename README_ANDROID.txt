RECEIPTS REPORT - ANDROID APK
=============================
Same logic as the Windows app (core.py is unchanged). The screen is rebuilt for phones with Kivy.

EASIEST: build the APK free in the cloud (no Linux / Android Studio needed)
  1. Create a free account on github.com, make a new repository (private is fine).
  2. Upload ALL files of this folder (main.py, core.py, buildozer.spec and the .github folder).
  3. Open the repo > Actions tab > "Build Android APK" > Run workflow.
  4. After ~20-30 minutes download the artifact "ReceiptsReport-apk" (zip) -> inside is the .apk.
  5. Copy the .apk to the phone, open it, allow "Install unknown apps" -> installed. Works fully offline.

OR build on your own Linux PC / WSL / Ubuntu:
  sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libffi-dev libssl-dev
  pip install buildozer cython
  buildozer android debug          -> apk appears in bin/

USE ON THE PHONE
  Import   -> pick CSV / Excel file(s) from phone storage, Drive, WhatsApp downloads...
  Filters  -> dates (type dd-mm-yyyy or tap Pick), Kendra, Type, Staff, Services (multi), fee range, search, query box
  Receipts -> cards with the ticked columns + total;  Summary tab -> Service Details table
  Export   -> creates the formatted .xlsx (A4 landscape print setup) in Documents and offers Share
  Print    -> Android has no print dialog for this app: Export, then open the xlsx in Excel/Sheets/WPS and print from there.
  Rules / Order / Columns buttons = same settings as Windows.
Note: old .xls files must first be saved as .xlsx or .csv.
