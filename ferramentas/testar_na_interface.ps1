# Abre um 3MF no Anycubic Slicer Next, lê os textos das janelas e diálogos e fecha o programa.
# Uso: powershell -File testar_na_interface.ps1 -Arquivo "C:\caminho\projeto.3mf" [-Segundos 45]
param(
    [Parameter(Mandatory = $true)][string]$Arquivo,
    [int]$Segundos = 45,
    [string]$Slicer = "",
    [string]$Captura = ""
)
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes, System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class Janela {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
}
"@

if (-not $Slicer) {
    # acha o slicer pelo registro de programas instalados
    $Slicer = Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*,
        HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*,
        HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* -ErrorAction SilentlyContinue |
        Where-Object { $_.DisplayName -match 'AnycubicSlicerNext|Anycubic Slicer Next' } |
        ForEach-Object { $_.DisplayIcon.Trim('"').Split(',')[0] } | Select-Object -First 1
    if (-not $Slicer) { Write-Output "ERRO: não achei o Anycubic Slicer Next; use -Slicer"; exit 2 }
}
if (Get-Process -Name AnycubicSlicerNext -ErrorAction SilentlyContinue) {
    Write-Output "ERRO: o Anycubic Slicer Next já está aberto; feche-o antes do teste."
    exit 2
}

$proc = Start-Process -FilePath $Slicer -ArgumentList "`"$Arquivo`"" -PassThru
$raiz = [System.Windows.Automation.AutomationElement]::RootElement
$condicao = New-Object System.Windows.Automation.PropertyCondition(
    [System.Windows.Automation.AutomationElement]::ProcessIdProperty, $proc.Id)
$vistos = @{}
$fim = (Get-Date).AddSeconds($Segundos)
while ((Get-Date) -lt $fim) {
    Start-Sleep -Milliseconds 1500
    $janelas = $raiz.FindAll([System.Windows.Automation.TreeScope]::Children, $condicao)
    foreach ($janela in $janelas) {
        $titulo = $janela.Current.Name
        $textos = $janela.FindAll([System.Windows.Automation.TreeScope]::Descendants,
            [System.Windows.Automation.Condition]::TrueCondition) |
            Where-Object { $_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Text -and $_.Current.Name } |
            ForEach-Object { $_.Current.Name }
        $chave = "$titulo | $($textos -join ' / ')"
        if (-not $vistos.ContainsKey($chave)) {
            $vistos[$chave] = $true
            Write-Output ("[{0:N0}s] JANELA: {1}" -f ($Segundos - ($fim - (Get-Date)).TotalSeconds), $titulo)
            foreach ($t in ($textos | Select-Object -Unique -First 25)) { Write-Output "    texto: $t" }
        }
    }
}

if ($Captura) {
    $proc.Refresh()
    [Janela]::ShowWindow($proc.MainWindowHandle, 3) | Out-Null  # maximiza
    [Janela]::SetForegroundWindow($proc.MainWindowHandle) | Out-Null
    Start-Sleep -Seconds 2
    $principal = [System.Windows.Automation.AutomationElement]::FromHandle($proc.MainWindowHandle)
    $r = $principal.Current.BoundingRectangle
    $bmp = New-Object System.Drawing.Bitmap([int]$r.Width, [int]$r.Height)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen([int]$r.X, [int]$r.Y, 0, 0, $bmp.Size)
    $bmp.Save($Captura, [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose(); $bmp.Dispose()
    Write-Output "CAPTURA: $Captura"
}

# fecha sem salvar
$proc.CloseMainWindow() | Out-Null
Start-Sleep -Seconds 3
$janelas = $raiz.FindAll([System.Windows.Automation.TreeScope]::Children, $condicao)
foreach ($janela in $janelas) {
    $botoes = $janela.FindAll([System.Windows.Automation.TreeScope]::Descendants,
        (New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
            [System.Windows.Automation.ControlType]::Button)))
    foreach ($b in $botoes) {
        if ($b.Current.Name -match "Don't save|Não salvar|Nao salvar|Discard|Descartar") {
            $b.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
        }
    }
}
Start-Sleep -Seconds 3
if (-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force }
Write-Output "FECHADO"
