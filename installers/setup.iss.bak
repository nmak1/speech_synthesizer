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
AppPublisherURL=https://github.com/yourusername/FreeTalk
AppSupportURL=https://github.com/yourusername/FreeTalk
AppUpdatesURL=https://github.com/yourusername/FreeTalk
DefaultDirName={autopf}\FreeTalk
DefaultGroupName=FreeTalk
AllowNoIcons=yes
LicenseFile=..\LICENSE.txt

; Требования к системе
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Выходные файлы
OutputDir=.
OutputBaseFilename=FreeTalk_Setup_v1.2.0
SetupIconFile=logo.ico

; Настройки сжатия
Compression=lzma2/ultra64
SolidCompression=yes
InternalCompressLevel=ultra

; Внешний вид
WizardStyle=modern
WizardSizePercent=100,100
WizardResizable=no

; Настройки установки
UsePreviousAppDir=yes
DisableProgramGroupPage=no
DisableReadyPage=no
DisableWelcomePage=no
AllowRootDirectory=yes
DirExistsWarning=no
ChangesAssociations=no

; Настройки иконок
UninstallDisplayIcon={app}\FreeTalk.exe
UninstallDisplayName=FreeTalk 1.2.0

; Версия
VersionInfoVersion=1.2.0.0
VersionInfoCompany=FreeTalk
VersionInfoDescription=Голосовой синтезатор FreeTalk
VersionInfoCopyright=FreeTalk
VersionInfoProductName=FreeTalk
VersionInfoProductVersion=1.2.0.0

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать значок на рабочем столе"; GroupDescription: "Дополнительные значки:"; Flags: unchecked
Name: "quicklaunchicon"; Description: "Создать значок на панели быстрого запуска"; GroupDescription: "Дополнительные значки:"; Flags: unchecked

[Files]
; Основной исполняемый файл
Source: "FreeTalk.exe"; DestDir: "{app}"; Flags: ignoreversion

; Иконки (должны быть скопированы для отображения в программе)
Source: "logo.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "logo.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "logo_big.png"; DestDir: "{app}"; Flags: ignoreversion

; Файлы программы (только необходимые)
Source: "..\main.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion

; Модули Python
Source: "..\src\*"; DestDir: "{app}\src"; Flags: ignoreversion recursesubdirs createallsubdirs

; Данные
Source: "..\data\dictionaries\*"; DestDir: "{app}\data\dictionaries"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\data\models\v3_1_ru.pt"; DestDir: "{app}\data\models"; Flags: ignoreversion

; Изображения
Source: "..\imeg\*"; DestDir: "{app}\imeg"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Главный ярлык в меню Пуск
Name: "{group}\FreeTalk"; Filename: "{app}\FreeTalk.exe"; IconFilename: "{app}\logo.ico"; WorkingDir: "{app}"

; Ярлык для документации
Name: "{group}\README"; Filename: "{app}\README.md"; IconFilename: "{sys}\notepad.exe"; IconIndex: 0

; Ярлык для лицензии
Name: "{group}\Лицензия"; Filename: "{app}\LICENSE.txt"; IconFilename: "{sys}\notepad.exe"; IconIndex: 0

; Ярлык на рабочем столе
Name: "{userdesktop}\FreeTalk"; Filename: "{app}\FreeTalk.exe"; IconFilename: "{app}\logo.ico"; WorkingDir: "{app}"; Tasks: desktopicon

; Ярлык в панели быстрого запуска
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\FreeTalk"; Filename: "{app}\FreeTalk.exe"; IconFilename: "{app}\logo.ico"; WorkingDir: "{app}"; Tasks: quicklaunchicon

[Run]
; Запуск программы после установки
Filename: "{app}\FreeTalk.exe"; Description: "Запустить FreeTalk"; Flags: postinstall nowait skipifsilent unchecked

[UninstallDelete]
; Удаление файлов настроек при деинсталляции
Type: files; Name: "{userappdata}\FreeTalk\*"
Type: dirifempty; Name: "{userappdata}\FreeTalk"

[Registry]
; Регистрация в системе
Root: HKCU; Subkey: "Software\FreeTalk"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\FreeTalk"; ValueType: string; ValueName: "Version"; ValueData: "1.2.0"; Flags: uninsdeletekey

[Code]
// Проверка системных требований
function InitializeSetup(): Boolean;
var
  Version: TWindowsVersion;
begin
  Result := True;

  // Проверка версии Windows (требуется Windows 10 или выше для лучшей работы)
  GetWindowsVersionEx(Version);
  if (Version.Major < 10) then
  begin
    if MsgBox('FreeTalk лучше работает на Windows 10/11. Продолжить установку?', mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False;
      Exit;
    end;
  end;
end;

// Создание резервной копии настроек при обновлении
procedure CurStepChanged(CurStep: TSetupStep);
var
  OldConfig, NewConfig: String;
begin
  if CurStep = ssInstall then
  begin
    if DirExists(ExpandConstant('{userappdata}\FreeTalk')) then
    begin
      OldConfig := ExpandConstant('{userappdata}\FreeTalk');
      NewConfig := ExpandConstant('{app}\data\user_data\backup');
      if not DirExists(NewConfig) then
        CreateDir(NewConfig);
    end;
  end;
end;