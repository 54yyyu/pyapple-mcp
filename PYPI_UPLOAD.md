# PyPI Upload Instructions

This document contains instructions for uploading PyApple MCP to PyPI.

## Prerequisites

1. **Install build tools**:
   ```bash
   pip install build twine
   ```

2. **PyPI Account**: You need a PyPI account and API token
   - Create account at https://pypi.org/account/register/
   - Generate API token at https://pypi.org/manage/account/token/

## Building the Package

1. **Clean previous builds**:
   ```bash
   rm -rf dist/ build/ *.egg-info
   ```

2. **Build the package**:
   ```bash
   python -m build
   ```

   This creates:
   - `dist/pyapple_mcp-1.0.1.tar.gz` (source distribution)
   - `dist/pyapple_mcp-1.0.1-py3-none-any.whl` (wheel distribution)

3. **Verify package contents**:
   ```bash
   python -m twine check dist/*
   ```
   
   Note: You may see warnings about license metadata format. These are deprecation warnings and don't prevent upload.

## Testing Installation

Test the built package locally before uploading:

```bash
pip install dist/pyapple_mcp-1.0.1-py3-none-any.whl
pyapple-mcp --help  # Should start the server
```

## Uploading to PyPI

### Option 1: Using API Token (Recommended)

1. **Upload to TestPyPI first** (optional but recommended):
   ```bash
   python -m twine upload --repository testpypi dist/*
   ```

2. **Upload to PyPI**:
   ```bash
   python -m twine upload dist/*
   ```

   When prompted:
   - Username: `__token__`
   - Password: Your PyPI API token (including `pypi-` prefix)

### Option 2: Using Username/Password

```bash
python -m twine upload dist/*
```

Enter your PyPI username and password when prompted.

## Post-Upload Verification

1. **Check PyPI page**: Visit https://pypi.org/project/pyapple-mcp/
2. **Test installation**: 
   ```bash
   pip install pyapple-mcp
   pyapple-mcp-setup  # Test setup helper
   ```

## Version Updates

To release a new version:

1. **Update version** in `pyproject.toml` and `pyapple_mcp/__init__.py`
2. **Commit changes**:
   ```bash
   git add .
   git commit -m "Bump version to X.Y.Z"
   git tag vX.Y.Z
   git push origin main --tags
   ```
3. **Rebuild and upload** following the steps above

## Package Information

- **Package Name**: `pyapple-mcp`
- **Author**: Steven Yu
- **License**: MIT
- **Python Support**: 3.9+
- **Platform**: macOS only

## Troubleshooting

- **License warnings**: These are deprecation warnings about metadata format and don't prevent upload
- **Upload fails**: Check your API token and network connection
- **Import errors**: Ensure all dependencies are properly listed in `pyproject.toml`

## Files Included in Package

The package includes:
- `pyapple_mcp/` - Main Python package
- `README.md` - Package documentation  
- `LICENSE` - MIT license file
- `CLAUDE.md` - Development guide
- `pyproject.toml` - Package configuration