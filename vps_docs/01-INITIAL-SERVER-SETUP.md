# Phase 1: Initial Server Setup & Hardening

## Overview
This document covers the initial setup and hardening of your Ubuntu 24.04 VPS. All commands are ready to copy and paste.

**Estimated Time**: 30-45 minutes  
**Prerequisites**: Fresh Ubuntu 24.04 installation with root access

---

## Step 1: Initial System Update

Connect to your VPS as root and update the system:

```bash
# Update package lists
apt update

# Upgrade all packages
apt upgrade -y

# Install essential tools
apt install -y curl wget git vim nano htop net-tools software-properties-common apt-transport-https ca-certificates gnupg lsb-release
```

**Security Note**: Always keep your system updated to patch security vulnerabilities.

---

## Step 2: Configure Timezone and Locale

Set your timezone to Asia/Makassar:

```bash
# Set timezone
timedatectl set-timezone Asia/Makassar

# Verify timezone
timedatectl

# Configure locale (optional)
locale-gen en_US.UTF-8
update-locale LANG=en_US.UTF-8
```

---

## Step 3: Create Deployment User

Create a non-root user for deployments and daily operations:

```bash
# Create user 'deploy' (change username if desired)
adduser deploy

# Follow prompts to set password and user information
# Use a strong password (at least 16 characters, mix of letters, numbers, symbols)
```

**Password Requirements**:
- Minimum 16 characters
- Mix of uppercase, lowercase, numbers, and symbols
- Example generator: `openssl rand -base64 24`

Add user to sudo group:

```bash
# Add deploy user to sudo group
usermod -aG sudo deploy

# Verify user groups
groups deploy
```

---

## Step 4: Configure SSH Key Authentication

### On Your Local Machine (Windows)

Generate SSH key pair if you don't have one:

```powershell
# Open PowerShell and run:
ssh-keygen -t ed25519 -C "your_email@example.com"

# Press Enter to accept default location (C:\Users\DEVA\.ssh\id_ed25519)
# Set a strong passphrase for the key
```

Display your public key:

```powershell
# Display public key
type C:\Users\DEVA\.ssh\id_ed25519.pub
```

### On Your VPS

Switch to deploy user and set up SSH directory:

```bash
# Switch to deploy user
su - deploy

# Create .ssh directory
mkdir -p ~/.ssh

# Set proper permissions
chmod 700 ~/.ssh

# Create authorized_keys file
nano ~/.ssh/authorized_keys
```

Paste your public key (from local machine) into the file, save and exit (Ctrl+X, Y, Enter).

Set proper permissions:

```bash
# Set file permissions
chmod 600 ~/.ssh/authorized_keys

# Exit back to root
exit
```

---

## Step 5: Configure SSH Security

Edit SSH configuration:

```bash
# Backup original SSH config
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

# Edit SSH config
nano /etc/ssh/sshd_config
```

Find and modify these settings (uncomment if needed):

```
# SSH Port (default 22, can change for additional security)
Port 22

# Disable root login (recommended after testing deploy user)
PermitRootLogin no

# Enable public key authentication
PubkeyAuthentication yes

# Keep password authentication enabled as backup
PasswordAuthentication yes

# Disable empty passwords
PermitEmptyPasswords no

# Disable X11 forwarding
X11Forwarding no

# Set login grace time
LoginGraceTime 60

# Maximum authentication attempts
MaxAuthTries 3

# Maximum sessions
MaxSessions 5

# Enable strict mode
StrictModes yes

# Disable host-based authentication
HostbasedAuthentication no

# Protocol version
Protocol 2
```

**Important**: Before disabling root login, test that you can SSH with the deploy user!

Test SSH configuration:

```bash
# Test SSH config for syntax errors
sshd -t

# If no errors, restart SSH service
systemctl restart sshd
```

---

## Step 6: Test SSH Access

**DO NOT CLOSE YOUR CURRENT ROOT SESSION YET!**

From your local machine, test SSH access:

```powershell
# Test SSH with deploy user
ssh deploy@YOUR_VPS_IP

# If successful, test sudo access
sudo whoami
# Should output: root
```

If successful, you can proceed. If not, troubleshoot before continuing.

---

## Step 7: Disable Root Login (Optional but Recommended)

Only do this after confirming deploy user SSH access works:

```bash
# Edit SSH config
nano /etc/ssh/sshd_config

# Change this line:
PermitRootLogin no

# Restart SSH
systemctl restart sshd
```

---

## Step 8: Configure Automatic Security Updates

Install unattended-upgrades:

```bash
# Install package
apt install -y unattended-upgrades

# Enable automatic updates
dpkg-reconfigure -plow unattended-upgrades
# Select "Yes" when prompted
```

Configure update settings:

```bash
# Edit configuration
nano /etc/apt/apt.conf.d/50unattended-upgrades
```

Ensure these lines are uncommented:

```
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}";
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESMApps:${distro_codename}-apps-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
};

Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
```

---

## Step 9: Install and Configure UFW Firewall

Install UFW:

```bash
# Install UFW
apt install -y ufw
```

Configure default policies:

```bash
# Default deny incoming
ufw default deny incoming

# Default allow outgoing
ufw default allow outgoing
```

Allow essential services:

```bash
# Allow SSH (IMPORTANT: Do this before enabling UFW!)
ufw allow 22/tcp comment 'SSH'

# Allow HTTP
ufw allow 80/tcp comment 'HTTP'

# Allow HTTPS
ufw allow 443/tcp comment 'HTTPS'
```

Enable UFW:

```bash
# Enable firewall
ufw enable

# Check status
ufw status verbose
```

**Expected Output**:
```
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), disabled (routed)

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW IN    Anywhere                   # SSH
80/tcp                     ALLOW IN    Anywhere                   # HTTP
443/tcp                    ALLOW IN    Anywhere                   # HTTPS
```

---

## Step 10: Install and Configure Fail2ban

Install Fail2ban:

```bash
# Install Fail2ban
apt install -y fail2ban
```

Create local configuration:

```bash
# Copy default config
cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local

# Edit local config
nano /etc/fail2ban/jail.local
```

Configure basic settings (find and modify these sections):

```ini
[DEFAULT]
# Ban time (1 hour)
bantime = 3600

# Find time window (10 minutes)
findtime = 600

# Max retry attempts
maxretry = 5

# Destination email for alerts (optional)
destemail = your_email@example.com

# Sender email
sender = fail2ban@yourvps.com

# Action (ban and send email)
action = %(action_mw)s

[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
```

Start and enable Fail2ban:

```bash
# Start Fail2ban
systemctl start fail2ban

# Enable on boot
systemctl enable fail2ban

# Check status
systemctl status fail2ban

# Check jail status
fail2ban-client status

# Check SSH jail specifically
fail2ban-client status sshd
```

---

## Step 11: Configure System Limits

Increase system limits for better performance:

```bash
# Edit limits configuration
nano /etc/security/limits.conf
```

Add these lines at the end:

```
* soft nofile 65536
* hard nofile 65536
* soft nproc 65536
* hard nproc 65536
```

Edit sysctl configuration:

```bash
# Edit sysctl config
nano /etc/sysctl.conf
```

Add these lines at the end:

```
# Increase system file descriptor limit
fs.file-max = 2097152

# Increase network buffer sizes
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728

# Increase TCP buffer sizes
net.ipv4.tcp_rmem = 4096 87380 67108864
net.ipv4.tcp_wmem = 4096 65536 67108864

# Enable TCP window scaling
net.ipv4.tcp_window_scaling = 1

# Increase max connections
net.core.somaxconn = 4096

# Protect against SYN flood attacks
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 8192

# Disable IP forwarding (unless needed)
net.ipv4.ip_forward = 0

# Enable IP spoofing protection
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Disable ICMP redirect acceptance
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0

# Enable bad error message protection
net.ipv4.icmp_ignore_bogus_error_responses = 1

# Log suspicious packets
net.ipv4.conf.all.log_martians = 1
```

Apply changes:

```bash
# Apply sysctl changes
sysctl -p

# Verify changes
sysctl fs.file-max
```

---

## Step 12: Set Up Swap Space (Recommended for 8GB RAM)

Create 4GB swap file:

```bash
# Create swap file
fallocate -l 4G /swapfile

# Set permissions
chmod 600 /swapfile

# Make swap
mkswap /swapfile

# Enable swap
swapon /swapfile

# Verify swap
swapon --show
free -h
```

Make swap permanent:

```bash
# Backup fstab
cp /etc/fstab /etc/fstab.backup

# Add swap to fstab
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

Configure swappiness:

```bash
# Edit sysctl config
nano /etc/sysctl.conf
```

Add these lines:

```
# Swappiness (lower = less swap usage)
vm.swappiness = 10

# Cache pressure
vm.vfs_cache_pressure = 50
```

Apply changes:

```bash
sysctl -p
```

---

## Step 13: Install Basic Monitoring Tools

Install monitoring utilities:

```bash
# Install monitoring tools
apt install -y htop iotop nethogs ncdu

# Install log monitoring
apt install -y logwatch

# Configure logwatch (optional)
cp /usr/share/logwatch/default.conf/logwatch.conf /etc/logwatch/conf/
```

---

## Step 14: Create Directory Structure

Create standard directory structure:

```bash
# Switch to deploy user
su - deploy

# Create application directories
mkdir -p ~/apps
mkdir -p ~/backups
mkdir -p ~/logs
mkdir -p ~/scripts

# Create docker directory
mkdir -p ~/docker

# Exit back to root
exit
```

---

## Step 15: Configure Hostname

Set a meaningful hostname:

```bash
# Set hostname (replace 'your-vps-name' with your choice)
hostnamectl set-hostname your-vps-name

# Edit hosts file
nano /etc/hosts
```

Add this line after localhost entries:

```
127.0.1.1    your-vps-name
```

Verify:

```bash
hostnamectl
```

---

## Step 16: Install Additional Security Tools

Install security scanning tools:

```bash
# Install rkhunter (rootkit hunter)
apt install -y rkhunter

# Update rkhunter database
rkhunter --update

# Run initial scan
rkhunter --propupd

# Install lynis (security auditing)
apt install -y lynis

# Run security audit (optional, for review)
lynis audit system
```

---

## Verification Checklist

Run these commands to verify your setup:

```bash
# Check system updates
apt update && apt list --upgradable

# Check SSH service
systemctl status sshd

# Check firewall status
ufw status verbose

# Check Fail2ban status
fail2ban-client status

# Check swap
free -h

# Check disk space
df -h

# Check system limits
ulimit -a

# Check listening ports
netstat -tulpn

# Check failed login attempts
lastb | head -20

# Check successful logins
last | head -20
```

---

## Security Checklist

- [x] System fully updated
- [x] Non-root user created with sudo access
- [x] SSH key authentication configured
- [x] SSH hardened (root login disabled, key auth enabled)
- [x] Firewall (UFW) enabled with minimal ports
- [x] Fail2ban installed and monitoring SSH
- [x] Automatic security updates enabled
- [x] System limits optimized
- [x] Swap space configured
- [x] Hostname set
- [x] Basic monitoring tools installed

---

## Important Notes

1. **Save Your SSH Key**: Keep your private key (`C:\Users\DEVA\.ssh\id_ed25519`) safe and backed up
2. **Document Passwords**: Store your deploy user password securely
3. **Test Before Proceeding**: Ensure you can SSH with deploy user before continuing
4. **Firewall Rules**: Only ports 22, 80, 443 are open - all other services will be proxied
5. **Regular Updates**: Run `apt update && apt upgrade` weekly

---

## Troubleshooting

### Cannot SSH with deploy user
```bash
# Check SSH service
systemctl status sshd

# Check SSH logs
tail -f /var/log/auth.log

# Verify authorized_keys permissions
ls -la /home/deploy/.ssh/
```

### Locked out after disabling root login
- Contact your VPS provider for console access
- Re-enable root login temporarily
- Fix deploy user SSH access

### Firewall blocking connections
```bash
# Disable UFW temporarily
ufw disable

# Re-add rules
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp

# Re-enable
ufw enable
```

---

## Next Steps

Proceed to [`02-SECURITY-HARDENING.md`](02-SECURITY-HARDENING.md) for additional security measures, or continue to [`03-DOCKER-INSTALLATION.md`](03-DOCKER-INSTALLATION.md) to install Docker.

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-07  
**Tested On**: Ubuntu 24.04 LTS
