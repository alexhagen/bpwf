#!/bin/bash
# Script to run Cline CLI in YOLO mode to generate a Doric column visualization
# using the bpwf MCP server with local configuration

set -e  # Exit on error

echo "=========================================="
echo "Doric Column Generation with Cline CLI"
echo "=========================================="
echo ""

# Check if cline CLI is installed
if ! command -v cline &> /dev/null; then
    echo "Error: cline CLI not found. Please install it first:"
    echo "  npm install -g @cline/cli"
    echo ""
    echo "See: https://docs.cline.bot/cline-cli/getting-started"
    exit 1
fi

# Check if bpwf is installed
if ! python -c "import bpwf" 2>/dev/null; then
    echo "Error: bpwf package not found. Please install it first:"
    echo "  pip install bpwf"
    exit 1
fi

# Check if bpy is installed
if ! python -c "import bpy" 2>/dev/null; then
    echo "Warning: bpy not installed. The MCP server needs it."
    echo "Install with: pip install bpy"
    echo ""
fi

echo "✓ Prerequisites checked"
echo ""

# Load ANTHROPIC_API_KEY from environment or .env.secret
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "ANTHROPIC_API_KEY not found in environment, checking .env.secret..."
    PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
    ENV_FILE="$PROJECT_ROOT/.env.secret"
    
    if [ -f "$ENV_FILE" ]; then
        # Source the .env.secret file to load the API key
        export $(grep -v '^#' "$ENV_FILE" | grep ANTHROPIC_API_KEY | xargs)
        if [ -n "$ANTHROPIC_API_KEY" ]; then
            echo "✓ Loaded ANTHROPIC_API_KEY from .env.secret"
        else
            echo "Error: ANTHROPIC_API_KEY not found in .env.secret"
            exit 1
        fi
    else
        echo "Error: ANTHROPIC_API_KEY not in environment and .env.secret not found at $ENV_FILE"
        exit 1
    fi
else
    echo "✓ Using ANTHROPIC_API_KEY from environment"
fi
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROMPT_FILE="$SCRIPT_DIR/08_doric_column_prompt.md"
CONFIG_DIR="$SCRIPT_DIR/.cline-config"

# Check if prompt file exists
if [ ! -f "$PROMPT_FILE" ]; then
    echo "Error: Prompt file not found at $PROMPT_FILE"
    exit 1
fi

echo "Prompt file: $PROMPT_FILE"
echo ""

# Create local Cline configuration directory
echo "Setting up local Cline configuration..."
mkdir -p "$CONFIG_DIR"

# Create MCP configuration file
cat > "$CONFIG_DIR/mcp.json" << 'EOF'
{
  "mcpServers": {
    "bpwf": {
      "command": "bpwf-mcp",
      "args": [],
      "description": "Blender for Publication-Worthy Figures - 3D scene creation and rendering"
    }
  }
}
EOF

echo "✓ Created MCP configuration at: $CONFIG_DIR/mcp.json"
echo ""

# Authenticate Cline with the API key in the custom config directory
echo "Authenticating Cline with Anthropic API..."
cline auth -p anthropic -k "$ANTHROPIC_API_KEY" -m claude-sonnet-4-5-20250929 --config "$CONFIG_DIR"

if [ $? -eq 0 ]; then
    echo "✓ Cline authentication successful"
else
    echo "Error: Cline authentication failed"
    exit 1
fi
echo ""

echo "Starting Cline CLI in YOLO mode with local configuration..."
echo "This will autonomously generate the Doric column visualization."
echo ""

# Run cline in YOLO mode with the prompt and local config
# The --yolo flag enables autonomous execution without user confirmation
# The --config flag uses our local configuration directory
cline --yolo --config "$CONFIG_DIR" "$PROMPT_FILE"

echo ""
echo "=========================================="
echo "Generation complete!"
echo "Check the output in: assets/08_doric_column.png"
echo "=========================================="
