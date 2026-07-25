# Run all test suites. Use -Fast to skip integration tests (no network needed).
param([switch]$Fast)

$marker = if ($Fast) { '-m', 'not integration' } else { @() }

Write-Host "`n=== ragcore tests ===" -ForegroundColor Cyan
pytest .\ragcore @marker
$ragcore = $LASTEXITCODE

Write-Host "`n=== backend tests ===" -ForegroundColor Cyan
pytest .\backend @marker
$backend = $LASTEXITCODE

if ($ragcore -ne 0 -or $backend -ne 0) {
    Write-Host "`nFAILURES" -ForegroundColor Red
    exit 1
}
Write-Host "`nALL PASSED" -ForegroundColor Green