; installers/setup_fixed.iss
; Исправленная версия с правильными путями

[Setup]
AppId={{8E5D6F2A-1B3C-4D5E-6F7A-8B9C0D1E2F3A}}
AppName=Voice Synthesizer
AppVersion=1.0.0
AppPublisher=Voice Synthesizer Team
DefaultDirName={autopf}\VoiceSynthesizer
DefaultGroupName=Voice Synthesizer
AllowNoIcons=yes
OutputDir=D:\speech_synthesizer\installers
OutputBaseFilename=VoiceSynthesizer_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={app}\VoiceSynthesizer.exe

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать значок на рабочем столе"; GroupDescription: "Дополнительные значки:"

[Files]
; Основной исполняемый файл
Source: "D:\speech_synthesizer\dist\VoiceSynthesizer.exe"; DestDir: "{app}"; Flags: ignoreversion

; Папка с данными
Source: "D:\speech_synthesizer\data\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Voice Synthesizer"; Filename: "{app}\VoiceSynthesizer.exe"
Name: "{group}\{cm:UninstallProgram,Voice Synthesizer}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\Voice Synthesizer"; Filename: "{app}\VoiceSynthesizer.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\VoiceSynthesizer.exe"; Description: "Запустить Voice Synthesizer"; Flags: postinstall nowait skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\VoiceSynthesizer"