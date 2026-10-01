# Script para separar cap06_07.md em dois arquivos
$inputFile = 'D:\DEV\BOOK\CAPITULOS\cap06_07.md'
$cap06File = 'D:\DEV\BOOK\CAPITULOS\cap06.md'
$cap07File = 'D:\DEV\BOOK\CAPITULOS\cap07.md'

# Ler o arquivo original
$content = [System.IO.File]::ReadAllText($inputFile, [System.Text.Encoding]::UTF8)

# Encontrar a posicao de inicio do Cap 7 (linha: ## Capitulo 7:)
$marker = "## Cap"
$allPositions = @()
$pos = 0
while ($true) {
    $found = $content.IndexOf($marker, $pos)
    if ($found -eq -1) { break }
    $allPositions += $found
    $pos = $found + 1
}

Write-Host "Encontradas $($allPositions.Count) ocorrencias de '$marker'"

# O Cap 7 comenca na segunda ocorrencia de "## Cap"
$cap7Start = $allPositions[1]

Write-Host "Cap 7 comeca na posicao: $cap7Start"
Write-Host "Trecho: $($content.Substring($cap7Start, 80))"

# Separar o conteudo
$cap6Content = $content.Substring(0, $cap7Start).TrimEnd()
$cap7Content = $content.Substring($cap7Start)

# Salvar os arquivos
[System.IO.File]::WriteAllText($cap06File, $cap6Content + "`r`n", [System.Text.Encoding]::UTF8)
[System.IO.File]::WriteAllText($cap07File, $cap7Content, [System.Text.Encoding]::UTF8)

Write-Host "Arquivos criados com sucesso!"
Write-Host "cap06.md: $((Get-Item $cap06File).Length) bytes"
Write-Host "cap07.md: $((Get-Item $cap07File).Length) bytes"
