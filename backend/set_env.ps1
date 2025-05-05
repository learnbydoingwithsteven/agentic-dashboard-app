# This script is a template for setting environment variables
# DO NOT store actual API keys in this file - add them at runtime

# Set the GROQ_API_KEY environment variable (replace with your actual key when running)
# $env:GROQ_API_KEY = 'your_api_key_here'

# Set to use Ollama instead of Groq API (true/false)
$env:USE_OLLAMA = 'false'

# Enable debug logging (true/false)
# $env:DEBUG = 'false'

# Verify the environment variables
Write-Host "Environment variables:"
Write-Host "USE_OLLAMA set to: $env:USE_OLLAMA"
if ($env:GROQ_API_KEY) {
    Write-Host "GROQ_API_KEY is set"
} else {
    Write-Host "GROQ_API_KEY is not set"
}
