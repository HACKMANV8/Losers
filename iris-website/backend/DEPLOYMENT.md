# IRis Backend Deployment Guide

Quick start guide for deploying the IRis Backend API.

## ✅ Pre-Deployment Checklist

### 1. System Dependencies
```bash
# Verify all required tools are installed
clang --version          # LLVM/Clang compiler
opt --version            # LLVM optimizer
llc --version            # LLVM static compiler
riscv64-linux-gnu-gcc --version  # RISC-V cross-compiler
qemu-riscv64 --version   # QEMU RISC-V emulator
```

### 2. Python Environment
```bash
python3 --version   # Should be 3.8+
pip3 --version
```

### 3. Model Files
Ensure these files exist:
- `../../passformer_binary_size.pth` or `../../passformer_runtime.pth`
- `../../models/combined_model.pkl` (optional, for XGBoost)

---

## 🚀 Quick Start

### Step 1: Install Dependencies
```bash
cd /home/yash/hackman/iris-website/backend
pip3 install -r requirements.txt
```

### Step 2: Create Log Directory
```bash
mkdir -p logs
```

### Step 3: Test Configuration
```bash
python3 -c "from config import APIConfig; print('✓ Config OK')"
```

### Step 4: Start Development Server
```bash
python3 app.py
```

The server will start on `http://localhost:5001`

---

## 🔧 Configuration

### Edit config.py to customize:

1. **Model Paths**
```python
ModelConfig.TRANSFORMER_RUNTIME_MODEL = Path("path/to/model.pth")
ModelConfig.XGBOOST_MODEL = Path("path/to/model.pkl")
```

2. **Target Architecture**
```python
CompilationConfig.DEFAULT_TARGET_ARCH = "riscv64"  # or "riscv32"
```

3. **Server Settings**
```python
APIConfig.HOST = "0.0.0.0"  # Listen on all interfaces
APIConfig.PORT = 5001
APIConfig.DEBUG = False     # Set to False for production
```

4. **CORS Origins** (for frontend integration)
```python
APIConfig.CORS_ORIGINS = [
    "http://localhost:3000",
    "https://your-frontend-domain.com"
]
```

---

## 🐳 Docker Deployment (Optional)

Create `Dockerfile`:
```dockerfile
FROM ubuntu:22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    clang llvm \
    gcc-riscv64-linux-gnu \
    qemu-user \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy backend files
COPY backend/ /app/
COPY passformer_binary_size.pth /app/../../
COPY tools/ /app/../../tools/

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Expose port
EXPOSE 5001

# Run application
CMD ["python3", "app.py"]
```

Build and run:
```bash
docker build -t iris-backend .
docker run -p 5001:5001 iris-backend
```

---

## 🔒 Production Deployment

### Using Gunicorn (Recommended)

1. **Install Gunicorn**
```bash
pip3 install gunicorn
```

2. **Create systemd service** (`/etc/systemd/system/iris-backend.service`):
```ini
[Unit]
Description=IRis Backend API
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/home/yash/hackman/iris-website/backend
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/local/bin/gunicorn -w 4 -b 0.0.0.0:5001 --timeout 120 "app:create_app()"
Restart=always

[Install]
WantedBy=multi-user.target
```

3. **Enable and start service**
```bash
sudo systemctl daemon-reload
sudo systemctl enable iris-backend
sudo systemctl start iris-backend
sudo systemctl status iris-backend
```

### Using Nginx as Reverse Proxy

**Nginx configuration** (`/etc/nginx/sites-available/iris-backend`):
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeouts for long-running compilations
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/iris-backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 📊 Monitoring & Logs

### View Logs
```bash
# Application logs
tail -f logs/iris_backend.log

# Systemd service logs (if using systemd)
sudo journalctl -u iris-backend -f
```

### Health Check
```bash
# Simple health check
curl http://localhost:5001/api/health

# Detailed status
curl http://localhost:5001/api/status
```

### Performance Monitoring
Consider adding tools like:
- **Prometheus** for metrics collection
- **Grafana** for visualization
- **Sentry** for error tracking

---

## 🧪 Testing

### 1. Unit Tests (create test files in `tests/` directory)
```bash
pytest tests/
```

### 2. API Tests
```bash
# Health check
curl http://localhost:5001/api/health

# Model status
curl http://localhost:5001/api/analytics/models

# System status
curl http://localhost:5001/api/status
```

### 3. Integration Test
```bash
# Create a simple test program
echo '#include <stdio.h>
int main() { 
    printf("Hello RISC-V\n"); 
    return 0; 
}' > test.c

# Test optimization
curl -X POST http://localhost:5001/api/optimize \
  -F "source_file=@test.c" \
  -F "model_selection=transformer"
```

---

## 🔍 Troubleshooting

### Issue: Models not loading
**Solution:**
1. Check model file paths in `config.py`
2. Verify files exist: `ls -lh ../../*.pth`
3. Check logs: `tail -f logs/iris_backend.log`

### Issue: Compilation errors
**Solution:**
1. Verify RISC-V toolchain: `which riscv64-linux-gnu-gcc`
2. Test QEMU: `qemu-riscv64 --version`
3. Check LLVM tools: `which clang opt llc`

### Issue: CORS errors from frontend
**Solution:**
1. Add frontend URL to `APIConfig.CORS_ORIGINS` in `config.py`
2. Restart backend server

### Issue: Port already in use
**Solution:**
```bash
# Find process using port 5001
sudo lsof -i :5001

# Kill the process or change port in config.py
```

### Issue: Import errors
**Solution:**
```bash
# Ensure all dependencies are installed
pip3 install -r requirements.txt

# Check Python path
python3 -c "import sys; print('\n'.join(sys.path))"
```

---

## 🔄 Updates & Maintenance

### Updating the Backend
```bash
# Pull latest changes
git pull

# Update dependencies
pip3 install -r requirements.txt --upgrade

# Restart service
sudo systemctl restart iris-backend
```

### Database Migrations (if added later)
Currently the backend is stateless, but if you add a database:
```bash
# Run migrations
flask db upgrade
```

### Backup Important Files
```bash
# Backup models
tar -czf models_backup_$(date +%Y%m%d).tar.gz ../../*.pth ../../models/

# Backup logs
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/
```

---

## 📈 Scaling

### Horizontal Scaling
1. Deploy multiple backend instances
2. Use load balancer (e.g., Nginx, HAProxy)
3. Share model files via NFS or object storage

### Vertical Scaling
1. Increase Gunicorn workers: `-w 8`
2. Use more powerful CPU for compilations
3. Add GPU support for Transformer inference

### Caching
Consider adding Redis for:
- Feature extraction results
- Model predictions
- Compilation results

---

## 🛡️ Security Considerations

### Production Security Checklist
- [ ] Disable debug mode: `APIConfig.DEBUG = False`
- [ ] Set up HTTPS with SSL certificates
- [ ] Implement rate limiting
- [ ] Add authentication for sensitive endpoints
- [ ] Sanitize all user inputs (already done in validators)
- [ ] Set up firewall rules
- [ ] Regular security updates for dependencies
- [ ] Monitor for suspicious activity
- [ ] Implement request logging and audit trails

---

## 📞 Support

For issues or questions:
1. Check logs: `logs/iris_backend.log`
2. Review API documentation: `API_REFERENCE.md`
3. Check system status: `curl http://localhost:5001/api/status`
4. Refer to main project documentation

---

## ✨ Next Steps

After deployment:
1. ✅ Verify all endpoints are working
2. ✅ Test with real C programs
3. ✅ Monitor performance and logs
4. ✅ Set up automated backups
5. ✅ Configure monitoring and alerts
6. ✅ Document any custom configurations
7. ✅ Train team on API usage

---

**Backend Version:** 1.0.0  
**Last Updated:** 2025-11-01  
**Target Architecture:** RISC-V (riscv64)
