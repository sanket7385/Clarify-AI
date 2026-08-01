# 🚀 Deploy ScribeFlow AI on AWS EC2

Step-by-step guide to deploy this app on an EC2 instance using Docker.

---

## 1. Launch an EC2 Instance

### Recommended Instance Types

| Instance     | vCPU | RAM   | Cost (on-demand) | Best For                     |
| ------------ | ---- | ----- | ----------------- | ---------------------------- |
| `t3.large`   | 2    | 8 GB  | ~$0.083/hr        | Whisper `tiny` / `small`     |
| `t3.xlarge`  | 4    | 16 GB | ~$0.166/hr        | Whisper `small` / `medium`   |

### Launch Steps (AWS Console)

1. Go to **EC2 → Launch Instance**
2. **Name**: `scribeflow-ai`
3. **AMI**: Ubuntu Server 22.04 LTS (or Amazon Linux 2023)
4. **Instance type**: `t3.large` (minimum)
5. **Key pair**: Select or create one (you'll need the `.pem` file to SSH in)
6. **Storage**: Set root volume to **30 GB** (gp3) — the Docker image needs ~4 GB + room for data
7. **Security Group**: Create or select one with these rules:

| Type  | Port  | Source    | Purpose          |
| ----- | ----- | --------- | ---------------- |
| SSH   | 22    | Your IP   | SSH access       |
| Custom TCP | 8501 | 0.0.0.0/0 | Streamlit app |

8. Click **Launch Instance**

---

## 2. Connect to Your Instance

```bash
# Replace with your key file and EC2 public IP
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>
```

---

## 3. Install Docker & Docker Compose

### Ubuntu 22.04

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Allow running Docker without sudo
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker compose version
```

### Amazon Linux 2023

```bash
sudo yum update -y
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose plugin
sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
```

---

## 4. Deploy the Application

### Option A: Clone & Build on EC2 (Recommended)

```bash
# Clone the repository
git clone <YOUR_REPO_URL> scribeflow-ai
cd scribeflow-ai

# Create the .env file with your API keys
cat > .env << 'EOF'
MISTRAL_API_KEY=your_mistral_api_key_here
WHISPER_MODEL=tiny
EOF

# Build and start (first build takes 5-10 minutes)
docker compose up -d --build

# Watch the build progress
docker compose logs -f
```

### Option B: Pull Pre-built Image from Docker Hub

```bash
# If you've pushed your image to Docker Hub:
docker pull yourusername/scribeflow-ai:latest

# Create .env and docker-compose.yml, then:
docker compose up -d
```

---

## 5. Verify Deployment

```bash
# Check container is running
docker compose ps

# Check health status
docker inspect --format='{{.State.Health.Status}}' scribeflow-ai

# View application logs
docker compose logs -f

# Test from the server
curl http://localhost:8501/_stcore/health
```

Then open your browser and go to:
```
http://<EC2_PUBLIC_IP>:8501
```

---

## 6. Useful Commands

```bash
# Stop the app
docker compose down

# Restart the app
docker compose restart

# Rebuild after code changes
docker compose up -d --build

# View real-time logs
docker compose logs -f

# Check image size
docker images

# SSH into the running container
docker exec -it scribeflow-ai bash

# Clean up unused Docker resources
docker system prune -af
```

---

## 7. Troubleshooting

### Container keeps restarting
```bash
# Check logs for errors
docker compose logs --tail=50
```

### Out of memory
- Upgrade to `t3.xlarge` (16 GB RAM), or
- Set `WHISPER_MODEL=tiny` in `.env` (uses ~1 GB vs ~2 GB for `small`)

### Port 8501 not accessible
- Verify the **Security Group** has port 8501 open
- Check: `sudo ufw status` — if UFW is active, run `sudo ufw allow 8501`

### Build fails on EC2
- Ensure at least **30 GB** disk space: `df -h`
- Free up space: `docker system prune -af`

---

## 8. Security Best Practices

> ⚠️ **For production use**, consider these additional steps:

1. **Use HTTPS**: Set up an Nginx reverse proxy with Let's Encrypt SSL
2. **Restrict port 8501**: In your security group, limit source to your IP only
3. **Use AWS Secrets Manager** instead of `.env` files for API keys
4. **Enable CloudWatch** for monitoring and alerting
5. **Set up automated backups** for the chroma_db volume
