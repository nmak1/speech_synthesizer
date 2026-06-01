; installers/setup.iss
; Inno Setup Script для FreeTalk - Голосовой синтезатор
; Версия: 1.2.0

[Setup]
; Основная информация
AppId={{FreeTalk-Speech-Synthesizer}}
AppName=FreeTalk
AppVersion=1.2.0
AppVerName=FreeTalk 1.2.0
AppPublisher=FreeTalk
DefaultDirName={autopf}\FreeTalk
DefaultGroupName=FreeTalk
AllowNoIcons=yes
LicenseFile=..\LICENSE.txt

; Требования к системе
PrivilegesRequired=lowest

; Выходные файлы
OutputDir=.
OutputBaseFilename=FreeTalk_Setup_v1.2.0
SetupIconFile=logo.ico

; Настройки сжатия
Compression=lzma2/ultra64
SolidCompression=yes

; Внешний вид
WizardStyle=modern

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать значок на рабочем столе"; GroupDescription: "Дополнительные значки:"; Flags: unchecked

[Files]
; Основной исполняемый файл
Source: "FreeTalk.exe"; DestDir: "{app}"; Flags: ignoreversion

; Иконка
Source: "logo.ico"; DestDir: "{app}"; Flags: ignoreversion

; Модули Python
Source: "..\src\*"; DestDir: "{app}\src"; Flags: ignoreversion recursesubdirs createallsubdirs

; Данные
Source: "..\data\dictionaries\*"; DestDir: "{app}\data\dictionaries"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\data\models\v3_1_ru.pt"; DestDir: "{app}\data\models"; Flags: ignoreversion

; Изображения
Source: "..\imeg\*"; DestDir: "{app}\imeg"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Главный ярлык
Name: "{group}\FreeTalk"; Filename: "{app}\FreeTalk.exe"; IconFilename: "{app}\logo.ico"; WorkingDir: "{app}"
; Ярлык на рабочем столе
Name: "{userdesktop}\FreeTalk"; Filename: "{app}\FreeTalk.exe"; IconFilename: "{app}\logo.ico"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
; Запуск программы после установки
Filename: "{app}\FreeTalk.exe"; Description: "Запустить FreeTalk"; Flags: postinstall nowait skipifsilent unchecked

[UninstallDelete]
Type: files; Name: "{userappdata}\FreeTalk\*"
Type: dirifempty; Name: "{userappdata}\FreeTalk"

[Registry]
Root: HKCU; Subkey: "Software\FreeTalk"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
