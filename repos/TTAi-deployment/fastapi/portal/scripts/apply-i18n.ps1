<#
.SYNOPSIS
  Apply i18n $t() replacements to all .vue files using EN locale keys.
  Replaces hardcoded text with {{ $t('Component.key') }} calls.
.DESCRIPTION
  Reads en.json locale file, finds matching text in .vue files,
  and replaces with i18n template expressions.
#>

param(
    [string]$PortalSrc = "C:\Users\vannt-pc\.openclaw\workspace\repos\TTAi-deployment\fastapi\portal\src",
    [string]$LocaleFile = "$PortalSrc\i18n\locales\en.json"
)

# Load locale
$enJson = Get-Content $LocaleFile -Raw | ConvertFrom-Json

$pagesDir = Join-Path $PortalSrc "pages"
$compDir  = Join-Path $PortalSrc "components"

$replaceCount = 0
$totalReplacements = 0

foreach ($comp in $enJson.PSObject.Properties) {
    $compName = $comp.Name
    $keys = $comp.Value

    # Locate the .vue file
    $file = Join-Path $pagesDir "$compName.vue"
    if (-not (Test-Path $file)) {
        $file = Join-Path $compDir "$compName.vue"
    }
    if (-not (Test-Path $file)) {
        Write-Host ("Skip {0}: no .vue file found" -f $compName)
        continue
    }

    $content = Get-Content $file -Raw
    $original = $content
    $thisReplacements = 0

    foreach ($keyEntry in $keys.PSObject.Properties) {
        $key = $keyEntry.Name
        $value = $keyEntry.Value

        # Escape regex special chars
        $escaped = [regex]::Escape($value)

        # Pattern 1: > value < (text nodes)
        $pattern = "(?<=>)$escaped(?=<)"
        $replacement = "{{ `$t('$compName.$key') }}"
        $newContent = $content -replace $pattern, $replacement
        if ($newContent -ne $content) {
            $thisReplacements++
            $content = $newContent
        }

        # Pattern 2: v-text="value"
        $pattern2 = "(v-text\s*=\s*\`")([^\`"]*?)($escaped)([^\`"]*?)(\`")"
        $replacement2 = "`$1`$2{{ `$t('$compName.$key') }}`$4`$5"
        $newContent2 = $content -replace $pattern2, $replacement2
        if ($newContent2 -ne $content) {
            $thisReplacements++
            $content = $newContent2
        }

        # Pattern 3: simple attr="value" (placeholder, title, etc)
        # Only if the value matches exactly
        $pattern3 = "(?<attr>(placeholder|title|alt|aria-label)\s*=\s*\`")$escaped(\`")"
        $replacement3 = "`${attr}{{ `$t('$compName.$key') }}`""
        $newContent3 = $content -replace $pattern3, $replacement3
        if ($newContent3 -ne $content) {
            $thisReplacements++
            $content = $newContent3
        }
    }

    if ($thisReplacements -gt 0) {
        # Write back (no trailing newline to match original)
        [System.IO.File]::WriteAllText($file, $content, [System.Text.Encoding]::UTF8)
        $replaceCount++
        $totalReplacements += $thisReplacements
        Write-Host ("[OK] {0}.vue: {1} replacements" -f $compName, $thisReplacements)
    } else {
        Write-Host ("[..] {0}.vue: no replacements (may need manual edit)" -f $compName)
    }
}

Write-Host "`n==== Summary ===="
Write-Host "Files updated: $replaceCount"
Write-Host "Total replacements: $totalReplacements"
