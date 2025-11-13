# Publishing Your Fork as a Pip Package

This guide explains how to build and publish your MarkItDown fork as a pip-installable package for use in cloud deployments and other projects.

## 📋 Overview

Publishing your fork as a pip package allows you to:
- **Install in cloud deployments** - Use `pip install your-package` in production
- **Share across projects** - Easily install in multiple projects
- **Version control** - Manage releases with semantic versioning
- **Dependency management** - Let other projects declare it as a dependency

## 🎯 Key Decisions to Make

### 1. Package Naming Strategy

**Critical Decision**: The name `markitdown` is already taken on PyPI by Microsoft's original package. You have several options:

#### Option A: Use a Different Name (Recommended for Public PyPI)
- **Name examples**: `cios-markitdown`, `markitdown-cios`, `markitdown-fork`, `cios-markdown-converter`
- **Pros**: Can publish to public PyPI, clear it's your fork
- **Cons**: Users need to know the different name
- **Installation**: `pip install cios-markitdown[all]`

#### Option B: GitHub Packages with Same Name
- **Name**: Keep `markitdown` but publish to GitHub Packages
- **Pros**: Keep familiar name, organized under your org
- **Cons**: Requires GitHub Packages authentication, slightly more complex install
- **Installation**: `pip install markitdown --extra-index-url https://pypi.github.com/simple/CIOS-Technologies`

#### Option C: Private PyPI/Registry
- **Name**: Any name you want on your private registry
- **Pros**: Complete control, can use same name
- **Cons**: Requires maintaining private registry, more setup

#### Option D: Git-Based Installation (No Registry)
- **Name**: N/A - install directly from Git
- **Pros**: Simple, no publishing needed
- **Cons**: Requires Git access, slower installs, less version control
- **Installation**: `pip install git+https://github.com/CIOS-Technologies/markitdown.git`

### 2. Version Strategy

Decide your versioning approach:
- **Start fresh**: Begin at `0.1.0` or `1.0.0` (recommended for fork)
- **Track upstream**: Keep version compatible with upstream (e.g., `0.1.3+cios.1`)
- **Semantic versioning**: Follow `MAJOR.MINOR.PATCH` (e.g., `1.0.0`)

## 🔧 What Needs to Change

### Required Changes

1. **Package Name** (if publishing to public PyPI)
   ```toml
   [project]
   name = "cios-markitdown"  # Or your chosen name
   ```

2. **Author Information**
   ```toml
   [project]
   authors = [
       { name = "CIOS Technologies", email = "your-email@example.com" },
   ]
   ```

3. **Project URLs**
   ```toml
   [project.urls]
   Documentation = "https://github.com/CIOS-Technologies/markitdown#readme"
   Issues = "https://github.com/CIOS-Technologies/markitdown/issues"
   Source = "https://github.com/CIOS-Technologies/markitdown"
   Homepage = "https://github.com/CIOS-Technologies/markitdown"
   ```

4. **Version** (update in `__about__.py`)
   ```python
   # packages/markitdown/src/markitdown/__about__.py
   __version__ = "1.0.0"  # Start fresh or continue versioning
   ```

5. **Description** (optional but recommended)
   ```toml
   [project]
   description = "MarkItDown fork by CIOS Technologies - Utility tool for converting various files to Markdown"
   ```

### Optional Changes

- **Keywords**: Add keywords to improve discoverability
- **License**: Verify you can maintain MIT license (you can as long as you include original attribution)
- **Classifiers**: Update to reflect your organization if needed

## 📦 Publishing Options Comparison

| Option | Pros | Cons | Best For |
|--------|------|------|----------|
| **Public PyPI (different name)** | Simple, standard, widely accessible | Need different name | Open source, public projects |
| **GitHub Packages** | Keep same name, organized | Auth required, extra config | GitHub-based orgs |
| **Private PyPI** | Complete control | Setup/maintenance overhead | Enterprise, private projects |
| **Git Install** | No publishing needed | Slower, less control | Development, testing |

## 🚀 Step-by-Step Publishing Process

### Option 1: Public PyPI (Recommended for Most Cases)

#### Step 1: Update Package Configuration

1. **Update `pyproject.toml`**:
   ```toml
   [project]
   name = "cios-markitdown"  # Choose your name
   description = "MarkItDown fork by CIOS Technologies"
   
   authors = [
       { name = "CIOS Technologies", email = "contact@ciostechnologies.com" },
   ]
   
   [project.urls]
   Documentation = "https://github.com/CIOS-Technologies/markitdown#readme"
   Issues = "https://github.com/CIOS-Technologies/markitdown/issues"
   Source = "https://github.com/CIOS-Technologies/markitdown"
   Homepage = "https://github.com/CIOS-Technologies/markitdown"
   ```

2. **Update version in `__about__.py`**:
   ```python
   __version__ = "1.0.0"
   ```

#### Step 2: Build the Package

```bash
cd packages/markitdown

# Install build tools
pip install build twine

# Build distribution
python -m build

# This creates:
# - dist/cios-markitdown-X.X.X.tar.gz (source distribution)
# - dist/cios_markitdown-X.X.X-py3-none-any.whl (wheel)
```

#### Step 3: Test Locally

```bash
# Install from local build
pip install dist/cios_markitdown-*.whl --force-reinstall

# Test it works
python -c "import markitdown; print(markitdown.__version__)"
markitdown --version
```

#### Step 4: Create PyPI Account

1. Go to https://pypi.org/account/register/
2. Create an account
3. Enable two-factor authentication (recommended)

#### Step 5: Get API Token

1. Go to https://pypi.org/manage/account/
2. Create an API token with "Upload projects" scope
3. Save the token (starts with `pypi-`)

#### Step 6: Upload to Test PyPI (Optional but Recommended)

```bash
# Upload to Test PyPI first
twine upload --repository testpypi dist/*

# Test installation from Test PyPI
pip install --index-url https://test.pypi.org/simple/ cios-markitdown
```

#### Step 7: Upload to Production PyPI

```bash
# Upload to production PyPI
twine upload dist/*

# Or use environment variables for security
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-YourTokenHere
twine upload dist/*
```

#### Step 8: Verify on PyPI

1. Check https://pypi.org/project/cios-markitdown/
2. Test installation:
   ```bash
   pip install cios-markitdown[all]
   ```

### Option 2: GitHub Packages

> **Note**: GitHub Packages requires authentication even for public packages when installing via pip. For public repositories, Option 3 (Git-based install) is simpler and doesn't require credentials.

#### Step 1: Create Personal Access Token

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Create token with `write:packages` and `read:packages` scope
3. Save the token

#### Step 2: Update Package Configuration

Add GitHub repository information to `pyproject.toml`:
```toml
[project]
name = "markitdown"

[project.urls]
Repository = "https://github.com/CIOS-Technologies/markitdown"
```

#### Step 3: Configure PyPI Credentials

Create `~/.pypirc`:
```ini
[distutils]
index-servers =
    pypi
    github

[github]
repository = https://pypi.python.org/simple
username = __token__
password = YOUR_GITHUB_TOKEN

[pypi]
username = __token__
password = YOUR_PYPI_TOKEN
```

#### Step 4: Build and Publish

```bash
cd packages/markitdown
python -m build
twine upload --repository github dist/*
```

#### Step 5: Install from GitHub Packages

**Note**: GitHub Packages requires authentication even for public packages. Users need to:
1. Create a GitHub Personal Access Token with `read:packages` scope
2. Configure authentication:
   ```bash
   pip install markitdown \
     --extra-index-url https://pypi.github.com/simple/CIOS-Technologies/ \
     --extra-index-url https://pypi.github.com/simple/ \
     --trusted-host pypi.github.com
   ```

Or use `.netrc` file:
```
machine pypi.github.com
login YOUR_GITHUB_USERNAME
password YOUR_GITHUB_TOKEN
```

### Option 3: Git-Based Installation (Simplest - Recommended for Public Repos)

**No credentials needed for public repositories!** Users install directly from Git without any authentication:

```bash
# Install from main branch (no credentials needed for public repo)
pip install git+https://github.com/CIOS-Technologies/markitdown.git#subdirectory=packages/markitdown

# Install specific version/tag
pip install git+https://github.com/CIOS-Technologies/markitdown.git@v1.0.0#subdirectory=packages/markitdown

# Install with extras
pip install "git+https://github.com/CIOS-Technologies/markitdown.git#subdirectory=packages/markitdown[all]"

# Install from specific branch
pip install git+https://github.com/CIOS-Technologies/markitdown.git@branch-name#subdirectory=packages/markitdown
```

**Benefits:**
- ✅ No authentication required for public repos
- ✅ Works immediately, no publishing step
- ✅ Easy version control via Git tags/branches
- ✅ No additional registries to manage

**In requirements.txt:**
```txt
# Option A: Direct Git URL
markitdown @ git+https://github.com/CIOS-Technologies/markitdown.git@main#subdirectory=packages/markitdown

# Option B: With extras
markitdown[all] @ git+https://github.com/CIOS-Technologies/markitdown.git@main#subdirectory=packages/markitdown

# Option C: Specific tag/commit
markitdown @ git+https://github.com/CIOS-Technologies/markitdown.git@v1.0.0#subdirectory=packages/markitdown
```

## ☁️ Using in Cloud Deployments

### Docker Deployment

**In Dockerfile:**
```dockerfile
# Option 1: From PyPI (if published)
RUN pip install cios-markitdown[all]

# Option 2: From GitHub Packages (requires credentials)
RUN pip install markitdown[all] \
    --extra-index-url https://pypi.github.com/simple/CIOS-Technologies/

# Option 3: From Git (no credentials needed for public repo) - RECOMMENDED
RUN pip install git+https://github.com/CIOS-Technologies/markitdown.git#subdirectory=packages/markitdown[all]

# Option 3b: Pin to specific version/tag for reproducible builds
RUN pip install git+https://github.com/CIOS-Technologies/markitdown.git@v1.0.0#subdirectory=packages/markitdown[all]
```

### Cloud Platform Examples

#### AWS Lambda / Google Cloud Functions

**requirements.txt:**
```txt
cios-markitdown[all]>=1.0.0
```

Or from Git:
```txt
markitdown[all] @ git+https://github.com/CIOS-Technologies/markitdown.git@main#subdirectory=packages/markitdown
```

#### Kubernetes / Helm

**values.yaml:**
```yaml
build:
  requirements:
    - "cios-markitdown[all]>=1.0.0"
```

#### GitHub Actions / CI/CD

```yaml
- name: Install dependencies
  run: |
    pip install cios-markitdown[all]
```

## 🔄 Versioning and Updates

### Semantic Versioning

Follow `MAJOR.MINOR.PATCH`:
- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes

### Releasing New Versions

1. Update version in `__about__.py`
2. Update CHANGELOG.md (if you maintain one)
3. Create Git tag:
   ```bash
   git tag v1.0.1
   git push origin v1.0.1
   ```
4. Build and publish:
   ```bash
   cd packages/markitdown
   python -m build
   twine upload dist/*
   ```

## 🔐 Security Best Practices

1. **API Tokens**: Never commit tokens to Git
   - Use environment variables
   - Use GitHub Secrets in CI/CD
   - Use `~/.pypirc` with proper permissions (600)

2. **Two-Factor Authentication**: Enable 2FA on PyPI/GitHub

3. **Token Scope**: Use minimal required scopes

4. **CI/CD Security**: Store tokens in secrets management

## 📝 Checklist Before Publishing

- [ ] Updated package name (if publishing to public PyPI)
- [ ] Updated author information
- [ ] Updated project URLs
- [ ] Updated version number
- [ ] Updated description
- [ ] Tested local build and installation
- [ ] Tested package works correctly
- [ ] Checked license compatibility
- [ ] Created PyPI/GitHub account
- [ ] Generated API tokens
- [ ] Tested on Test PyPI (if using PyPI)
- [ ] Updated documentation with new installation instructions

## 🆘 Troubleshooting

### Package Name Already Exists

**Problem**: Name conflict on PyPI  
**Solution**: Choose a different name or use GitHub Packages

### Authentication Errors

**Problem**: `403 Forbidden` or `401 Unauthorized`  
**Solution**: Check token is correct, has proper scopes, and not expired

### Build Errors

**Problem**: Build fails  
**Solution**: 
```bash
# Clean and rebuild
rm -rf dist/ build/ *.egg-info/
python -m build
```

### Installation Issues

**Problem**: Can't install published package  
**Solution**: 
- Wait a few minutes for PyPI to index
- Check package name spelling
- Verify index URL if using GitHub Packages

## 📚 Additional Resources

- [PyPI Publishing Guide](https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/)
- [GitHub Packages Documentation](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-python-package-registry)
- [Python Packaging User Guide](https://packaging.python.org/)
- [Semantic Versioning](https://semver.org/)

## 🎯 Recommended Approach

For your use case (public repository, cloud deployments):

1. **Best for Public Repos**: Git-based installation (Option 3) ✅
   - No credentials needed
   - No publishing step required
   - Works immediately
   - Perfect for public repositories
   - Easy versioning with Git tags

2. **Most Professional**: Publish to public PyPI (Option 1)
   - Faster installs (pre-built wheels)
   - Better for high-traffic/production
   - Standard pip install experience
   - Requires different package name

3. **Alternative**: GitHub Packages (Option 2)
   - Requires credentials even for public packages
   - More complex setup
   - Not recommended for public repos (use Option 3 instead)

**For a public repository, Option 3 (Git-based) is the simplest and most practical choice.** You get all the benefits without the overhead of publishing or authentication requirements.

