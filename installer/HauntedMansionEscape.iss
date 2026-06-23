#ifndef MyAppVersion
#define MyAppVersion "1.0.0"
#endif

#ifndef MyExeName
#define MyExeName "HauntedMansionEscape.exe"
#endif

[Setup]
AppId={{CF65E6B4-89B8-4A1A-8A58-9E8F2E5E2A2E}
AppName=Haunted Mansion Escape
AppVersion={#MyAppVersion}
AppPublisher=CS-499 Capstone
DefaultDirName={autopf}\Haunted Mansion Escape
DefaultGroupName=Haunted Mansion Escape
DisableProgramGroupPage=yes
LicenseFile=
OutputDir=dist
OutputBaseFilename=HauntedMansionEscape-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "..\dist\{#MyExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "Launch-Game.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "Start-Save-DB.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "Stop-Save-DB.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "README-offline.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Haunted Mansion Escape\Play Haunted Mansion Escape"; Filename: "{app}\HauntedMansionEscape.exe"
Name: "{autoprograms}\Haunted Mansion Escape\Start Save Database (Docker)"; Filename: "{app}\Start-Save-DB.bat"
Name: "{autoprograms}\Haunted Mansion Escape\Stop Save Database (Docker)"; Filename: "{app}\Stop-Save-DB.bat"
Name: "{autoprograms}\Haunted Mansion Escape\Offline README"; Filename: "{app}\README-offline.txt"
Name: "{autodesktop}\Haunted Mansion Escape"; Filename: "{app}\HauntedMansionEscape.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\HauntedMansionEscape.exe"; Description: "Launch Haunted Mansion Escape"; Flags: nowait postinstall skipifsilent
