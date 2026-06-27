[Setup]
AppName=IntegratedDataTool
AppVersion=1.1.1
DefaultDirName={localappdata}\IntegratedDataTool
DefaultGroupName=IntegratedDataTool
UninstallDisplayIcon={app}\IntegratedDataTool.exe
OutputDir=dist
OutputBaseFilename=IntegratedDataTool_Setup_v1.1.1
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
CloseApplications=yes
CloseApplicationsFilter=IntegratedDataTool.exe

[Files]
Source: "dist\IntegratedDataTool.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\IntegratedDataTool"; Filename: "{app}\IntegratedDataTool.exe"
Name: "{userdesktop}\IntegratedDataTool"; Filename: "{app}\IntegratedDataTool.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Run]
Filename: "{app}\IntegratedDataTool.exe"; Description: "{cm:LaunchProgram,IntegratedDataTool}"; Flags: nowait postinstall skipifsilent
