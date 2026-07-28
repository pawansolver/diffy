# Run Dhee Evaluation against SkillsMCP.
$ErrorActionPreference = "Stop"
$evaluatorPath = Join-Path $PSScriptRoot "evaluator"

Push-Location $evaluatorPath
try {
    if (-Not (Test-Path "node_modules")) {
        Write-Host "Installing locked evaluator dependencies..."
        npm ci
    }

    Write-Host "Validating evaluator before execution..."
    npm run check

    if (-Not $env:OPENAI_API_KEY) {
        throw "OPENAI_API_KEY is required. Set it in the environment before running evaluation."
    }

    Write-Host "Running Skills MCP evaluation..."
    npm run eval -- --config skills_eval_config.json
    Write-Host "Evaluation completed."
}
finally {
    Pop-Location
}
