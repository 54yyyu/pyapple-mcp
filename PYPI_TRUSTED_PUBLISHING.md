# PyPI Trusted Publishing Setup

This document explains how to set up PyPI Trusted Publishing for automated releases via GitHub Actions.

## What is Trusted Publishing?

Trusted Publishing allows you to publish to PyPI from GitHub Actions without needing to store API tokens as secrets. It uses OpenID Connect (OIDC) to verify that the publishing request comes from your GitHub repository.

## Setup Steps

### 1. Configure PyPI Trusted Publishing

1. **Go to PyPI**: Visit https://pypi.org/manage/account/publishing/
2. **Add a new pending publisher** with these details:
   - **PyPI Project Name**: `pyapple-mcp`
   - **Owner**: `54yyyu` (your GitHub username)
   - **Repository name**: `pyapple-mcp`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi`

3. **Optional: Set up TestPyPI** at https://test.pypi.org/manage/account/publishing/:
   - Same details but with environment name: `testpypi`

### 2. Create GitHub Environments

1. **Go to your GitHub repository**: https://github.com/54yyyu/pyapple-mcp
2. **Navigate to Settings > Environments**
3. **Create two environments**:
   - `pypi` - for production PyPI releases
   - `testpypi` - for testing releases

4. **Optional: Add protection rules**:
   - Require reviewers for production releases
   - Restrict to specific branches (e.g., `main`)

### 3. Create a Release

To trigger the automated publishing:

1. **Create and push a git tag**:
   ```bash
   git tag v1.0.1
   git push origin v1.0.1
   ```

2. **Create a GitHub Release**:
   - Go to https://github.com/54yyyu/pyapple-mcp/releases
   - Click "Create a new release"
   - Choose the tag `v1.0.1`
   - Add release notes
   - Click "Publish release"

3. **Monitor the workflow**:
   - The workflow will automatically build and publish to both TestPyPI and PyPI
   - Check the Actions tab for progress

## Workflow Overview

The GitHub Actions workflow (`publish.yml`) will:

1. **Build**: Create source and wheel distributions
2. **Test Publish**: Upload to TestPyPI (for all releases)
3. **Publish**: Upload to PyPI (only for tagged releases)

## Manual Publishing (Alternative)

If you prefer manual publishing, you can still use:

```bash
# Build the package
python -m build

# Upload to PyPI (requires API token)
python -m twine upload dist/*
```

## Troubleshooting

### Common Issues

1. **"Publisher not configured"**: Make sure you've set up the trusted publisher on PyPI with exact matching details

2. **"Environment protection rules"**: If you set up environment protection, you may need to approve the deployment

3. **"Permission denied"**: Ensure the workflow has `id-token: write` permissions

4. **"Package already exists"**: You need to increment the version number in `pyproject.toml` and `pyapple_mcp/__init__.py`

### Checking Status

- **PyPI Project**: https://pypi.org/project/pyapple-mcp/
- **GitHub Actions**: https://github.com/54yyyu/pyapple-mcp/actions
- **Workflow Runs**: Check the "Publish to PyPI" workflow runs

## Version Management

To release a new version:

1. **Update version numbers**:
   - `pyproject.toml`: Update `version = "1.0.2"`
   - `pyapple_mcp/__init__.py`: Update `__version__ = "1.0.2"`

2. **Commit and tag**:
   ```bash
   git add .
   git commit -m "Bump version to 1.0.2"
   git tag v1.0.2
   git push origin main --tags
   ```

3. **Create GitHub Release**: This triggers the automated publishing

## Security Benefits

- ✅ No API tokens stored in GitHub secrets
- ✅ Automatic token rotation
- ✅ Scoped to specific repository and workflow
- ✅ Audit trail of all publishing activities