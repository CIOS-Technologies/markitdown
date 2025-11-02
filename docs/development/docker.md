# Docker Deployment Guide

This guide covers building and running MarkItDown in Docker containers for production deployments, CI/CD pipelines, and isolated execution environments.

## Overview

The MarkItDown Docker image provides a containerized version of the application with all dependencies pre-installed, making it ideal for:
- **Production deployments** - Consistent runtime environment
- **CI/CD pipelines** - Automated document processing
- **Isolated execution** - Sandboxed document conversion
- **Cloud deployments** - Easy scaling and distribution

## Dockerfile Structure

The MarkItDown Dockerfile is optimized for production use:

```dockerfile
FROM python:3.13-slim-bullseye

# Runtime dependencies
- ffmpeg (for audio/video processing)
- exiftool (for metadata extraction)

# Optional dependencies
- git (install with build arg INSTALL_GIT=true)

# Packages installed
- markitdown[all]
- markitdown-sample-plugin
```

## Building the Docker Image

### Basic Build

Build the image from the repository root:

```bash
docker build -t markitdown:latest .
```

Or use the provided test script:

```bash
./test-docker.sh
```

### Build Options

**Include Git support** (required for some plugin installations):

```bash
docker build --build-arg INSTALL_GIT=true -t markitdown:latest .
```

**Specify custom user** (for security hardening):

```bash
docker build \
  --build-arg USERID=1000 \
  --build-arg GROUPID=1000 \
  -t markitdown:latest .
```

### Build Context Optimization

The `.dockerignore` file optimizes the build context by excluding unnecessary files:

```
*
!packages/
```

This ensures only the required package directories are included, reducing build time and image size.

## Running the Container

### Basic Usage

**Convert a file from stdin:**

```bash
docker run --rm -i markitdown:latest < input.pdf > output.md
```

**Convert a file from a mounted volume:**

```bash
docker run --rm \
  -v /path/to/files:/data \
  markitdown:latest /data/document.pdf > output.md
```

**Convert with output file:**

```bash
docker run --rm \
  -v /path/to/files:/data \
  -v $(pwd):/output \
  markitdown:latest /data/document.pdf -o /output/result.md
```

### Advanced Usage

**Enable plugins:**

```bash
docker run --rm \
  -v /path/to/files:/data \
  markitdown:latest --use-plugins /data/document.docx
```

**List available plugins:**

```bash
docker run --rm markitdown:latest --list-plugins
```

**Show help:**

```bash
docker run --rm markitdown:latest --help
```

**Use Azure Document Intelligence:**

```bash
docker run --rm \
  -e DOCINTEL_ENDPOINT="your-endpoint" \
  -v /path/to/files:/data \
  markitdown:latest -d -e "$DOCINTEL_ENDPOINT" /data/scan.pdf
```

## Container Configuration

### Environment Variables

The container supports the following environment variables:

- `EXIFTOOL_PATH` - Path to exiftool binary (default: `/usr/bin/exiftool`)
- `FFMPEG_PATH` - Path to ffmpeg binary (default: `/usr/bin/ffmpeg`)
- `DOCINTEL_ENDPOINT` - Azure Document Intelligence endpoint
- `OPENAI_API_KEY` - OpenAI API key for LLM integration
- `GEMINI_API_KEY` - Google Gemini API key for LLM integration

### Volume Mounts

**Input files:**
```bash
-v /host/path/to/files:/data
```

**Output directory:**
```bash
-v /host/output:/output
```

**Configuration files:**
```bash
-v /host/config:/app/config
```

### Network Configuration

For accessing external resources (YouTube, web content):

```bash
docker run --rm \
  --network host \
  markitdown:latest https://example.com/document.pdf
```

## Docker Deployment Scenarios

### Development

```bash
# Build for development
docker build -t markitdown:dev .

# Run with local code mounted
docker run --rm -it \
  -v $(pwd):/app \
  markitdown:dev --help
```

### Production

```bash
# Build optimized production image
docker build -t markitdown:prod .

# Run in production mode
docker run -d \
  --name markitdown \
  --restart unless-stopped \
  -v /data/inputs:/inputs \
  -v /data/outputs:/outputs \
  markitdown:prod
```

### CI/CD Pipeline

```yaml
# Example GitHub Actions workflow
- name: Build Docker image
  run: docker build -t markitdown:${{ github.sha }} .

- name: Run tests
  run: docker run --rm markitdown:${{ github.sha }} --help

- name: Process documents
  run: |
    docker run --rm \
      -v ${{ github.workspace }}/docs:/data \
      markitdown:${{ github.sha }} /data/sample.pdf
```

## Troubleshooting

### Docker Daemon Not Running

**On Linux (systemd):**
```bash
sudo systemctl start docker
sudo systemctl enable docker  # Enable on boot
```

**On WSL2:**
If using Docker Desktop:
- Ensure Docker Desktop is installed and running
- Enable WSL2 integration in Docker Desktop settings

Alternatively, install Docker directly in WSL2:
```bash
sudo apt update
sudo apt install docker.io
sudo service docker start
```

**Verify Docker is running:**
```bash
docker info
```

### Permission Errors

Add your user to the docker group:

```bash
sudo usermod -aG docker $USER
newgrp docker  # Or log out and back in
```

### Container Can't Access Files

Ensure proper volume mounting:

```bash
# Use absolute paths
docker run --rm \
  -v /absolute/path/to/files:/data \
  markitdown:latest /data/file.pdf

# Check file permissions
ls -la /path/to/files
```

### Build Fails

**Check Dockerfile syntax:**
```bash
docker build --no-cache -t markitdown:test .
```

**Inspect build logs:**
```bash
docker build -t markitdown:test . 2>&1 | tee build.log
```

**Verify required packages exist:**
```bash
ls -la packages/markitdown packages/markitdown-sample-plugin
```

### Container Exit Issues

**Run interactively for debugging:**
```bash
docker run --rm -it markitdown:latest /bin/bash
```

**Check container logs:**
```bash
docker logs <container-id>
```

## Security Considerations

### Running as Non-Root User

The container runs as `nobody:nogroup` by default for security. To customize:

```bash
docker build \
  --build-arg USERID=1000 \
  --build-arg GROUPID=1000 \
  -t markitdown:secure .
```

### Resource Limits

Set resource constraints:

```bash
docker run --rm \
  --memory="512m" \
  --cpus="1.0" \
  markitdown:latest /data/file.pdf
```

### Network Isolation

For enhanced security, use custom networks:

```bash
docker network create markitdown-net
docker run --rm \
  --network markitdown-net \
  markitdown:latest
```

## Performance Optimization

### Image Size

The base image uses `python:3.13-slim-bullseye` for minimal size. Final image size is approximately 1.18GB.

### Build Cache

Docker automatically caches layers. To rebuild without cache:

```bash
docker build --no-cache -t markitdown:latest .
```

### Multi-Stage Builds

For production, consider multi-stage builds to reduce final image size:

```dockerfile
FROM python:3.13-slim-bullseye as builder
# Install build dependencies
WORKDIR /app
COPY packages/ ./packages/
RUN pip install /app/packages/markitdown[all]

FROM python:3.13-slim-bullseye
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
# ... rest of Dockerfile
```

## Integration Examples

### With Docker Compose

```yaml
version: '3.8'
services:
  markitdown:
    build: .
    volumes:
      - ./inputs:/inputs
      - ./outputs:/outputs
    environment:
      - DOCINTEL_ENDPOINT=${DOCINTEL_ENDPOINT}
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: markitdown
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: markitdown
        image: markitdown:latest
        volumeMounts:
        - name: inputs
          mountPath: /data
```

## Related Documentation

- [Installation Guide](installation.md) - Local installation and setup
- [Build System](build.md) - Hatch build system details
- [Development Setup](README.md) - Development environment configuration
- [Testing Guide](testing.md) - Running tests in containers

## Additional Resources

- [Docker Documentation](https://docs.docker.com/) - Official Docker docs
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/) - Container optimization
- [Docker Security](https://docs.docker.com/engine/security/) - Security guidelines

