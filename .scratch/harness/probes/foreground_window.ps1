# 진단 전용. 지금 앞에 있는 창(GetForegroundWindow)과 접근성 트리의 Claude 창 핸들을 찍는다. 아무것도 누르지 않는다.
# open_session.ps1 의 Send-AppKeys 가드가 Claude 창을 앞에 있는 창으로 보는지 가를 때 쓴다. -Focus 를 주면 Claude 창 안의
# 입력창 하나에 SetFocus 를 한 뒤 다시 찍는다(SetFocus 가 창을 앞으로 올리는지).
# 쓰는 법: pwsh -NoProfile -File .scratch/harness/probes/foreground_window.ps1 [-Focus]
param([switch] $Focus)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -TypeDefinition @'
using System; using System.Text; using System.Runtime.InteropServices;
public static class ForegroundProbe {
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
    [DllImport("user32.dll")] public static extern IntPtr GetAncestor(IntPtr h, uint flags);
    public static string Title(IntPtr h) { var s = new StringBuilder(256); GetWindowText(h, s, 256); return s.ToString(); }
}
'@
$Auto = [System.Windows.Automation.AutomationElement]
$Scope = [System.Windows.Automation.TreeScope]
$wins = @($Auto::RootElement.FindAll($Scope::Children, [System.Windows.Automation.Condition]::TrueCondition) | Where-Object { $_.Current.Name -eq 'Claude' })
"claude-windows=$($wins.Count)"
function Show {
    $fg = [ForegroundProbe]::GetForegroundWindow()
    $root = [ForegroundProbe]::GetAncestor($fg, 2)  # GA_ROOT
    "foreground=$([int64]$fg) root=$([int64]$root) title=[$([ForegroundProbe]::Title($fg))]"
    foreach ($w in $wins) { "claude-handle=$($w.Current.NativeWindowHandle) same=$([int64]$fg -eq [int64]$w.Current.NativeWindowHandle) same-root=$([int64]$root -eq [int64]$w.Current.NativeWindowHandle)" }
}
Show
if ($Focus -and $wins.Count -eq 1) {
    $editCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, [System.Windows.Automation.ControlType]::Edit)
    $edit = $wins[0].FindFirst($Scope::Descendants, $editCond)
    if ($edit) { try { $edit.SetFocus(); 'setfocus=ok' } catch { "setfocus=실패 $($_.Exception.Message)" }; Start-Sleep -Milliseconds 300; Show }
}
