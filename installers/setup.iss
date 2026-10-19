; installers/setup.iss
; Inno Setup Script ? FreeTalk Speech Synthesizer
; ?????? ?? ??????: ?????????? ???????????? ????? /Dver=<??????> ?? src/version.py (??. release.py)

[Setup]
AppId={{FreeTalk-Speech-Synthesizer}}
AppName=FreeTalk
AppVersion={#ver}
AppVerName=FreeTalk {#ver}
AppPublisher=FreeTalk
AppPublisherURL=https://github.com/nmak1/speech_synthesizer
AppSupportURL=https://github.com/nmak1/speech_synthesizer
DefaultDirName={autopf}\FreeTalk
DefaultGroupName=FreeTalk
AllowNoIcons=yes
LicenseFile=..\LICENSE.txt

PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

OutputDir=.
OutputBaseFilename=FreeTalk_Setup_v{#ver}
SetupIconFile=logo.ico

Compression=lzma2/ultra64
SolidCompression=yes
InternalCompressLevel=ultra

WizardStyle=modern
WizardSizePercent=100,100
WizardResizable=no
DisableProgramGroupPage=no
DisableReadyPage=no
DisableWelcomePage=no
UsePreviousAppDir=yes

VersionInfoVersion={#ver}.0
VersionInfoCompany=FreeTalk
VersionInfoDescription=Synthesizer FreeTalk
VersionInfoCopyright=FreeTalk
VersionInfoProductName=FreeTalk
VersionInfoProductVersion={#ver}.0

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "??????? ????? ?? ??????? ?????"; GroupDescription: "?????????????? ??????:"; Flags: unchecked

[Files]
Source: "FreeTalk.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "logo.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\imeg\*"; DestDir: "{app}\imeg"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\FreeTalk"; Filename: "{app}\FreeTalk.exe"; IconFilename: "{app}\logo.ico"; WorkingDir: "{app}"
Name: "{userdesktop}\FreeTalk"; Filename: "{app}\FreeTalk.exe"; IconFilename: "{app}\logo.ico"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\FreeTalk.exe"; Description: "????????? FreeTalk"; Flags: postinstall nowait skipifsilent unchecked

[UninstallDelete]
Type: files; Name: "{userappdata}\FreeTalk\*"
Type: dirifempty; Name: "{userappdata}\FreeTalk"

[Registry]
Root: HKCU; Subkey: "Software\FreeTalk"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\FreeTalk"; ValueType: string; ValueName: "Version"; ValueData: "{#ver}"; Flags: uninsdeletekey