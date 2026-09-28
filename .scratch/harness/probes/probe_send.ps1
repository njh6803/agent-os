Add-Type -AssemblyName UIAutomationClient; Add-Type -AssemblyName UIAutomationTypes
$Auto = [System.Windows.Automation.AutomationElement]
$Scope = [System.Windows.Automation.TreeScope]
$root = $Auto::RootElement
$wins = @($root.FindAll($Scope::Children, [System.Windows.Automation.Condition]::TrueCondition) | Where-Object { $_.Current.Name -eq 'Claude' })
"windows=$($wins.Count)"
if ($wins.Count -ne 1) { exit 1 }
$win = $wins[0]
foreach ($name in @('보내기', 'Send')) {
    $cond = New-Object System.Windows.Automation.PropertyCondition($Auto::NameProperty, $name)
    $els = @($win.FindAll($Scope::Descendants, $cond))
    foreach ($el in $els) {
        $c = $el.Current
        $patterns = ($el.GetSupportedPatterns() | ForEach-Object { $_.ProgrammaticName }) -join ','
        "name=$name type=$($c.ControlType.ProgrammaticName) enabled=$($c.IsEnabled) offscreen=$($c.IsOffscreen) rect=$($c.BoundingRectangle) patterns=$patterns"
    }
}
$edits = @($win.FindAll($Scope::Descendants, (New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, [System.Windows.Automation.ControlType]::Edit))))
foreach ($e in $edits) {
    $v = ''
    try { $v = $e.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value } catch { $v = '<no value pattern>' }
    "edit name='$($e.Current.Name)' focused=$($e.Current.HasKeyboardFocus) len=$($v.Length) head='$($v.Substring(0, [Math]::Min(60, $v.Length)))'"
}
