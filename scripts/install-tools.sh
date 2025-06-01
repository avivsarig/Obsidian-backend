#!/bin/bash
set -euo pipefail

echo "Installing development tools..."

# Install Python tools
pip install -r requirements-dev.txt

# Install tflint
if ! command -v tflint &> /dev/null; then
    echo "Installing tflint..."
    case "$(uname -s)" in
        Linux)
            curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash
            ;;
        Darwin)
            if command -v brew &> /dev/null; then
                brew install tflint
            else
                curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash
            fi
            ;;
        *)
            echo "Unsupported OS for tflint: $(uname -s)"
            exit 1
            ;;
    esac
else
    echo "tflint already installed"
fi

# Verify installations
echo ""
echo "Verifying installations..."
tflint --version

echo ""
echo "Tools installed successfully!"
