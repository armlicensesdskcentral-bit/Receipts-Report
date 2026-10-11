[app]
title = Receipts Report
package.name = receiptsreport
package.domain = org.saanjh
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3==3.10.12,hostpython3==3.10.12,kivy==2.2.1,openpyxl,et_xmlfile,pyjnius,android,androidstorage4kivy
orientation = portrait
fullscreen = 0
android.api = 33
android.minapi = 24
android.archs = arm64-v8a
android.ndk = 25b
p4a.branch = v2024.01.21
android.accept_sdk_license = True
android.permissions = READ_EXTERNAL_STORAGE
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
