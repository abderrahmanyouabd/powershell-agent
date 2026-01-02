# Build and Installation Guide

## ✅ Fixed Entry Point Issue

The `powershell-agent` command now works correctly! I fixed the async entry point issue.

## 🔨 Build Commands

### 1. Build the Distribution Package

```powershell
poetry build
```

**Output files in `dist/` directory:**
- `powershell_agent-0.1.0-py3-none-any.whl` (wheel - recommended)
- `powershell_agent-0.1.0.tar.gz` (source distribution)

### 2. Verify Build

```powershell
Get-ChildItem dist
```

You should see both files listed.

## 📦 Installation Methods

### Method 1: Install from Wheel (Recommended)

```powershell
pip install dist/powershell_agent-0.1.0-py3-none-any.whl
```

### Method 2: Install from Source

```powershell
pip install dist/powershell_agent-0.1.0.tar.gz
```

### Method 3: Install in Editable Mode (Development)

```powershell
pip install -e .
```

This installs from the current directory and any changes you make are immediately reflected.

### Method 4: Install Using Poetry (Within Project)

```powershell
poetry install
```

Then run with:
```powershell
poetry run powershell-agent
```

## 🚀 Running After Installation

### If installed with pip:

```powershell
# Set your API key
$env:GROQ_API_KEY="your-groq-api-key"

# Run the installed command
powershell-agent

# Or with a prompt directly
powershell-agent "list all Python files"
```

### If using Poetry:

```powershell
# Set your API key
$env:GROQ_API_KEY="your-groq-api-key"

# Run with Poetry
poetry run powershell-agent

# Or with a prompt
poetry run powershell-agent "list all Python files"
```

## 🧹 Clean Build

If you need to rebuild from scratch:

```powershell
# Remove old build artifacts
Remove-Item -Recurse -Force dist, build, *.egg-info, __pycache__ -ErrorAction SilentlyContinue

# Build fresh
poetry build
```

## 📤 Distribution

To share your package:

### Upload to PyPI (optional)

```powershell
# Configure PyPI credentials first
poetry config pypi-token.pypi your-pypi-token

# Publish
poetry publish
```

### Share the Wheel File

Simply share the `.whl` file from `dist/` with others:

```powershell
# They can install it with:
pip install powershell_agent-0.1.0-py3-none-any.whl
```

## 🧪 Test Installation

After installing, verify it works:

```powershell
# Test 1: Check if command is available
Get-Command powershell-agent

# Test 2: Try running it
powershell-agent "Get-Date"
```

## 🔄 Upgrade/Reinstall

To upgrade after making changes:

```powershell
# Rebuild
poetry build

# Uninstall old version
pip uninstall powershell-agent

# Install new version
pip install dist/powershell_agent-0.1.0-py3-none-any.whl --force-reinstall
```

## 📋 Complete Workflow Example

```powershell
# 1. Navigate to project
cd c:\Users\youab\Downloads\gormiti

# 2. Clean old builds
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue

# 3. Build package
poetry build

# 4. Install
pip install dist/powershell_agent-0.1.0-py3-none-any.whl

# 5. Set API key
$env:GROQ_API_KEY="your-actual-api-key"

# 6. Run!
powershell-agent "search for TODO in all files"
```

## 🎯 What Changed

**Fixed:** The entry point now properly calls `cli()` which wraps `asyncio.run(main())` instead of trying to call the async function directly. This fixes the "coroutine was never awaited" error.

## 💡 Pro Tips

1. **Development Mode**: Use `pip install -e .` during development so you don't need to rebuild after every change

2. **Virtual Environment**: Consider creating a virtual environment first:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install dist/powershell_agent-0.1.0-py3-none-any.whl
   ```

3. **Global Installation**: Skip the venv if you want it available globally on your system

4. **Update Version**: When making changes, update the version in `pyproject.toml` and rebuild

## ✅ Success Indicators

After installation, you should be able to:
- ✅ Run `powershell-agent` from any directory
- ✅ Pass prompts as command-line arguments
- ✅ See the interactive prompt if no arguments provided
- ✅ Execute PowerShell commands through natural language

Enjoy your PowerShell agent! 🚀
