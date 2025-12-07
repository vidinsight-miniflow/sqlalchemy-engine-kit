# Publishing to PyPI

Guide for publishing sqlalchemy-engine-kit to PyPI.

## Prerequisites

1. **PyPI Account**: Create an account at https://pypi.org/account/register/
2. **API Token**: Generate an API token at https://pypi.org/manage/account/token/
3. **Build Tools**: Install build and twine:
   ```bash
   pip install build twine
   ```

## Setup

### 1. Configure PyPI Credentials

**Option A: Environment Variables (Recommended)**
```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-api-token-here
```

**Option B: .pypirc File**
```bash
# Copy template
cp .pypirc.template ~/.pypirc

# Edit and add your token
nano ~/.pypirc
```

### 2. Update Version

Before publishing, update version in:
- `src/sqlalchemy_engine_kit/__init__.py` → `__version__ = "0.1.0"`
- `pyproject.toml` → `version = "0.1.0"`
- `CHANGELOG.md` → Add new version entry

## Build and Publish

### Step 1: Clean Previous Builds
```bash
rm -rf dist/ build/ *.egg-info
```

### Step 2: Build Package
```bash
python -m build
```

This creates:
- `dist/sqlalchemy_engine_kit-0.1.0.tar.gz` (source distribution)
- `dist/sqlalchemy_engine_kit-0.1.0-py3-none-any.whl` (wheel)

### Step 3: Check Package
```bash
# Check package contents
twine check dist/*

# Test install locally
pip install dist/sqlalchemy_engine_kit-0.1.0-py3-none-any.whl
```

### Step 4: Test on TestPyPI (Optional but Recommended)
```bash
# Upload to TestPyPI first
twine upload --repository testpypi dist/*

# Test install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ sqlalchemy-engine-kit
```

### Step 5: Publish to PyPI
```bash
# Upload to production PyPI
twine upload dist/*
```

## Verification

After publishing, verify:
1. Package appears at: https://pypi.org/project/sqlalchemy-engine-kit/
2. Installation works:
   ```bash
   pip install sqlalchemy-engine-kit
   ```
3. Import works:
   ```python
   from sqlalchemy_engine_kit import DatabaseManager
   ```

## Updating Version

For new releases:

1. **Update version** in `__init__.py` and `pyproject.toml`
2. **Update CHANGELOG.md** with new version entry
3. **Commit and tag**:
   ```bash
   git add .
   git commit -m "Release v0.1.1"
   git tag v0.1.1
   git push origin main --tags
   ```
4. **Build and publish** (follow steps above)

## Troubleshooting

### Error: "File already exists"
- Version already published
- Increment version number

### Error: "Invalid credentials"
- Check API token is correct
- Ensure token has upload permissions

### Error: "Package name already taken"
- Choose different package name in `pyproject.toml`
- Or contact PyPI admins if it's your package

## Best Practices

1. **Always test on TestPyPI first**
2. **Use semantic versioning** (MAJOR.MINOR.PATCH)
3. **Update CHANGELOG.md** for each release
4. **Tag releases** in git
5. **Test installation** after publishing
6. **Monitor PyPI project page** for issues

## CI/CD Integration

For automated publishing, add to `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [created]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install build twine
      - run: python -m build
      - run: twine upload dist/*
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
```

---

**Note**: Keep your API token secure! Never commit `.pypirc` or tokens to git.

