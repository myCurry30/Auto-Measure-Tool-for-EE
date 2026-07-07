Unicode true
; ═══════════════════════════════════════════════════════════════════════════════
; NSIS Installer Script — EE Power On AutoTool V2.2
;
; Prerequisites:
;   - NSIS 3.x  (https://nsis.sourceforge.io/Download)
;   - PyInstaller output: dist\EE_Power_On_AutoTool_V2.2.0.exe
;
; Build:
;   makensis installer\setup.nsi
;
; Output:
;   installer\EE_Power_On_AutoTool_V2.2_Setup.exe
; ═══════════════════════════════════════════════════════════════════════════════

; ── Includes ─────────────────────────────────────────────────────────────────
!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"

; ── General ──────────────────────────────────────────────────────────────────
!define PRODUCT_NAME           "EE Power On AutoTool"
!define PRODUCT_VERSION        "2.2.0"
!define PRODUCT_PUBLISHER      "Nettrix"
!define PRODUCT_WEB_SITE       ""
!define PRODUCT_DIR_REGKEY     "Software\Microsoft\Windows\CurrentVersion\App Paths\${PRODUCT_NAME}.exe"
!define PRODUCT_UNINST_KEY     "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "EE_Power_On_AutoTool_V${PRODUCT_VERSION}_Setup.exe"
InstallDir "$PROGRAMFILES64\${PRODUCT_NAME}"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
RequestExecutionLevel admin    ; require admin for Program Files install
SetCompressor /SOLID lzma
ShowInstDetails show
ShowUnInstDetails show
BrandingText "${PRODUCT_PUBLISHER}"

; ── MUI Interface Settings ───────────────────────────────────────────────────
!define MUI_ABORTWARNING
!define MUI_ICON "..\resources\app_icon.ico"
!define MUI_UNICON "..\resources\app_icon.ico"

; Welcome page
!define MUI_WELCOMEPAGE_TITLE "Welcome to ${PRODUCT_NAME} Setup"
!define MUI_WELCOMEPAGE_TEXT "This wizard will install ${PRODUCT_NAME} V${PRODUCT_VERSION} on your computer.$\r$\n$\r$\nHardware Engineer Automated Testing Tool — oscilloscope automation for Sequence & Monotony tests.$\r$\n$\r$\nClick Next to continue."

; Finish page
!define MUI_FINISHPAGE_RUN "$INSTDIR\EE_Power_On_AutoTool_V2.2.0.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Launch ${PRODUCT_NAME}"
!define MUI_FINISHPAGE_SHOWREADME ""
!define MUI_FINISHPAGE_SHOWREADME_NOTCHECKED
!define MUI_FINISHPAGE_LINK "Nettrix Website"
!define MUI_FINISHPAGE_LINK_LOCATION ""

; ── MUI Pages ────────────────────────────────────────────────────────────────
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; ── MUI Language ─────────────────────────────────────────────────────────────
!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_LANGUAGE "English"

; ── Version Information ──────────────────────────────────────────────────────
VIProductVersion "${PRODUCT_VERSION}.0"
VIAddVersionKey "ProductName"     "${PRODUCT_NAME}"
VIAddVersionKey "CompanyName"     "${PRODUCT_PUBLISHER}"
VIAddVersionKey "FileDescription" "EE Power On AutoTool Installer"
VIAddVersionKey "FileVersion"     "${PRODUCT_VERSION}.0"
VIAddVersionKey "ProductVersion"  "${PRODUCT_VERSION}"
VIAddVersionKey "LegalCopyright"  "Nettrix  |  liujch2"

; ═══════════════════════════════════════════════════════════════════════════════
; Install Section
; ═══════════════════════════════════════════════════════════════════════════════
Section "MainSection" SEC01
    SetOutPath "$INSTDIR"

    ; ── Main executable ──────────────────────────────────────────────────
    File "..\dist\EE_Power_On_AutoTool_V2.2.0.exe"

    ; ── Config template (optional — shipped as default if present) ──
    File /nonfatal "..\config.json"

    ; ── Create runtime directories ────────────────────────────────────────
    CreateDirectory "$INSTDIR\outputs"
    CreateDirectory "$INSTDIR\logs"

    ; ── Write registry for Add/Remove Programs ────────────────────────────
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayName"          "${PRODUCT_NAME}"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayVersion"       "${PRODUCT_VERSION}"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "Publisher"            "${PRODUCT_PUBLISHER}"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayIcon"          "$INSTDIR\EE_Power_On_AutoTool_V2.2.0.exe"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "UninstallString"      "$INSTDIR\uninst.exe"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "QuietUninstallString" "$INSTDIR\uninst.exe /S"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "InstallLocation"      "$INSTDIR"
    WriteRegDWORD HKLM "${PRODUCT_UNINST_KEY}" "NoModify" 1
    WriteRegDWORD HKLM "${PRODUCT_UNINST_KEY}" "NoRepair" 1

    ; Estimate size
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKLM "${PRODUCT_UNINST_KEY}" "EstimatedSize" "$0"

    ; ── App Paths (optional: lets user type app name in Win+R) ───────────
    WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\EE_Power_On_AutoTool_V2.2.0.exe"
    WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "Path" "$INSTDIR"

    ; ── Create uninstaller ────────────────────────────────────────────────
    WriteUninstaller "$INSTDIR\uninst.exe"

    ; ── Start Menu shortcuts ──────────────────────────────────────────────
    SetShellVarContext all
    CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
    CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME} V${PRODUCT_VERSION}.lnk" \
        "$INSTDIR\EE_Power_On_AutoTool_V2.2.0.exe"
    CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall.lnk" \
        "$INSTDIR\uninst.exe"

    ; ── Desktop shortcut ──────────────────────────────────────────────────
    CreateShortCut "$DESKTOP\${PRODUCT_NAME} V${PRODUCT_VERSION}.lnk" \
        "$INSTDIR\EE_Power_On_AutoTool_V2.2.0.exe"
SectionEnd

; ═══════════════════════════════════════════════════════════════════════════════
; Uninstall Section
; ═══════════════════════════════════════════════════════════════════════════════
Section "Uninstall"
    SetShellVarContext all

    ; ── Kill running instance ──────────────────────────────────────────────
    DetailPrint "Closing running instances..."
    nsExec::ExecToStack 'taskkill /f /im "EE_Power_On_AutoTool_V2.2.0.exe"'
    Pop $0
    Sleep 1000

    ; ── Remove shortcuts ──────────────────────────────────────────────────
    Delete "$DESKTOP\${PRODUCT_NAME} V${PRODUCT_VERSION}.lnk"
    Delete "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME} V${PRODUCT_VERSION}.lnk"
    Delete "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall.lnk"
    RMDir "$SMPROGRAMS\${PRODUCT_NAME}"

    ; ── Remove installed files ────────────────────────────────────────────
    Delete "$INSTDIR\EE_Power_On_AutoTool_V2.2.0.exe"
    Delete "$INSTDIR\config.json"
    Delete "$INSTDIR\uninst.exe"

    ; ── Ask whether to keep user data ─────────────────────────────────────
    ; outputs/ and logs/ may contain user-generated data — ask before deleting
    MessageBox MB_YESNO|MB_ICONQUESTION \
        "Do you want to remove user data (test outputs and logs) as well?$\r$\n$\r$\nThis will delete the 'outputs' and 'logs' folders in the install directory." \
        IDNO skip_userdata
    RMDir /r "$INSTDIR\outputs"
    RMDir /r "$INSTDIR\logs"
    Goto done_userdata
skip_userdata:
    DetailPrint "User data (outputs/, logs/) kept on disk."
done_userdata:

    ; ── Remove install directory (only if empty after cleanup) ────────────
    RMDir "$INSTDIR"

    ; ── Remove registry entries ────────────────────────────────────────────
    DeleteRegKey HKLM "${PRODUCT_UNINST_KEY}"
    DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"

    SetAutoClose true
SectionEnd

; ═══════════════════════════════════════════════════════════════════════════════
; Callbacks
; ═══════════════════════════════════════════════════════════════════════════════
Function .onInit
    ; Detect if already installed and offer upgrade path
    ReadRegStr $0 HKLM "${PRODUCT_UNINST_KEY}" "UninstallString"
    ${If} $0 != ""
        MessageBox MB_YESNO|MB_ICONQUESTION \
            "${PRODUCT_NAME} is already installed.$\r$\n$\r$\nDo you want to uninstall the existing version before continuing?$\r$\n(Your user data in outputs\ and logs\ will be preserved.)" \
            IDNO skip_uninstall
        ; Run uninstaller silently on the old version, then continue
        ClearErrors
        ExecWait '$0 /S _?=$INSTDIR'
        IfErrors 0 skip_uninstall
        MessageBox MB_OK|MB_ICONSTOP "Failed to uninstall existing version. Please remove it manually from Control Panel."
        Abort
skip_uninstall:
    ${EndIf}
FunctionEnd

Function .onInstSuccess
    ; Optional: launch app after silent install? No — Finish page handles this
FunctionEnd
