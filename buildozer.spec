[app]
title = Receipts Report
package.name = receiptsreport
package.domain = org.saanjh
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy==2.3.0,openpyxl,et_xmlfile,pyjnius,android,androidstorage4kivy
orientation = portrait
fullscreen = 0
android.api = 34
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.permissions = READ_EXTERNAL_STORAGE
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
