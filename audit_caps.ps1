# Busca problemas nos capitulos
$capDir = 'D:\DEV\BOOK\CAPITULOS'
$files = Get-ChildItem "$capDir\cap*.md" | Sort-Object Name

Write-Host "===== DOIS PONTOS EM TITULOS (## e ###) =====" -ForegroundColor Yellow
foreach ($file in $files) {
    $lines = Get-Content $file.FullName -Encoding UTF8
    $found = @()
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        if ($line -match '^#{2,3}\s.*:') {
            $found += "  L$($i+1): $($line.Trim())"
        }
    }
    if ($found.Count -gt 0) {
        Write-Host "--- $($file.Name) ---" -ForegroundColor Cyan
        $found | ForEach-Object { Write-Host $_ }
    }
}

Write-Host ""
Write-Host "===== ABAIXO / ACIMA =====" -ForegroundColor Yellow
foreach ($file in $files) {
    $lines = Get-Content $file.FullName -Encoding UTF8
    $found = @()
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        if ($line -match '\babaixo\b|\bacima\b') {
            $trunc = if ($line.Trim().Length -gt 120) { $line.Trim().Substring(0,120) + '...' } else { $line.Trim() }
            $found += "  L$($i+1): $trunc"
        }
    }
    if ($found.Count -gt 0) {
        Write-Host "--- $($file.Name) ---" -ForegroundColor Cyan
        $found | ForEach-Object { Write-Host $_ }
    }
}

Write-Host ""
Write-Host "===== BACKTICK EM TERMOS ESTRANGEIROS (fora de blocos de codigo) =====" -ForegroundColor Yellow
$foreignTerms = @('`embeddings`','`snapshot`','`cold storage`','`cold open`','`dashboard`','`pipeline`','`benchmark`','`timeout`','`deploy`','`buffer`','`cache`','`token`','`input`','`output`','`feedback`','`trigger`')
foreach ($file in $files) {
    $lines = Get-Content $file.FullName -Encoding UTF8
    $inCode = $false
    $found = @()
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        if ($line -match '^\s*```') { $inCode = -not $inCode }
        if (-not $inCode) {
            foreach ($term in $foreignTerms) {
                if ($line -match [regex]::Escape($term)) {
                    $trunc = if ($line.Trim().Length -gt 120) { $line.Trim().Substring(0,120) + '...' } else { $line.Trim() }
                    $found += "  L$($i+1) [$term]: $trunc"
                    break
                }
            }
        }
    }
    if ($found.Count -gt 0) {
        Write-Host "--- $($file.Name) ---" -ForegroundColor Cyan
        $found | ForEach-Object { Write-Host $_ }
    }
}

Write-Host ""
Write-Host "===== BLOCOS DE CODIGO LONGOS (mais de 20 linhas) =====" -ForegroundColor Yellow
foreach ($file in $files) {
    $lines = Get-Content $file.FullName -Encoding UTF8
    $inCode = $false
    $startLine = 0
    $count = 0
    $found = @()
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        if ($line -match '^\s*```') {
            if (-not $inCode) {
                $inCode = $true
                $startLine = $i + 1
                $count = 0
            } else {
                $inCode = $false
                if ($count -gt 20) {
                    $found += "  L$startLine-$($i+1): bloco com $count linhas"
                }
            }
        } elseif ($inCode) {
            $count++
        }
    }
    if ($found.Count -gt 0) {
        Write-Host "--- $($file.Name) ---" -ForegroundColor Cyan
        $found | ForEach-Object { Write-Host $_ }
    }
}
