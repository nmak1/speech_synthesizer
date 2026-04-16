; installers/setup_fixed.iss
; Установщик для программы Free Talk - Голосовой синтезатор

[Setup]
; Основная информация
AppId={{8E5D6F2A-1B3C-4D5E-6F7A-8B9C0D1E2F3A}}
AppName=Free Talk
AppVersion=1.0.0
AppPublisher=Free Talk Team
AppPublisherURL=https://freetalk.com
AppSupportURL=https://freetalk.com/support
AppUpdatesURL=https://freetalk.com/updates
DefaultDirName={autopf}\FreeTalk
DefaultGroupName=Free Talk
SetupIconFile=..\logo.ico
AllowNoIcons=yes
OutputDir=.
OutputBaseFilename=FreeTalk_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
WizardImageFile=..\logo_medium.png
WizardSmallImageFile=..\logo_small.png
PrivilegesRequired=admin
UninstallDisplayIcon={app}\FreeTalk.exe
UninstallDisplayName=Free Talk - Голосовой синтезатор
LicenseFile=..\LICENSE.txt
InfoBeforeFile=..\README.md

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать значок на рабочем столе"; GroupDescription: "Дополнительные значки:"; Flags: checkedonce
Name: "quicklaunchicon"; Description: "Создать значок на панели быстрого запуска"; GroupDescription: "Дополнительные значки:"; Flags: checkedonce; OnlyBelowVersion: 6.1

[Files]
; Основной исполняемый файл
Source: "..\dist\FreeTalk.exe"; DestDir: "{app}"; Flags: ignoreversion

; Папка с данными (модель, словари, настройки)
Source: "..\data\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs

; Файлы логотипа
Source: "..\logo.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\logo.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\logo_small.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\logo_medium.png"; DestDir: "{app}"; Flags: ignoreversion

; Документация
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Free Talk"; Filename: "{app}\FreeTalk.exe"; IconFilename: "{app}\logo.ico"
Name: "{group}\{cm:UninstallProgram,Free Talk}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Free Talk"; Filename: "{app}\FreeTalk.exe"; IconFilename: "{app}\logo.ico"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\Free Talk"; Filename: "{app}\FreeTalk.exe"; IconFilename: "{app}\logo.ico"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\FreeTalk.exe"; Description: "Запустить Free Talk"; Flags: postinstall nowait skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\FreeTalk"
Type: filesandordirs; Name: "{app}\data"

[Code]
function InitializeSetup(): Boolean;
var
  ErrorCode: Integer;
  WindowsVersion: Integer;
begin
  Result := True;

  // Проверка версии Windows
  WindowsVersion := GetWindowsVersion();
  if WindowsVersion < $06010000 then
  begin
    MsgBox('Для работы программы требуется Windows 7 или выше.' + #13#10 +
           'Ваша версия Windows не поддерживается.', mbError, MB_OK);
    Result := False;
  end;

  // Проверка прав администратора
  if not IsAdminLoggedOn() then
  begin
    if MsgBox('Для установки программы требуются права администратора.' + #13#10 +
              'Продолжить установку?', mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Создаем необходимые папки
    CreateDir(ExpandConstant('{userappdata}\FreeTalk'));
    CreateDir(ExpandConstant('{userappdata}\FreeTalk\logs'));
    CreateDir(ExpandConstant('{userappdata}\FreeTalk\user_data'));

    // Создаем ссылку в меню Пуск
    CreateDir(ExpandConstant('{userappdata}\Microsoft\Windows\Start Menu\Programs\Free Talk'));
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Спрашиваем, удалять ли пользовательские данные
    if MsgBox('Удалить пользовательские настройки и данные?', mbConfirmation, MB_YESNO) = IDYES then
    begin
      DelTree(ExpandConstant('{userappdata}\FreeTalk'), True, True, True);
    end;
  end;
end;