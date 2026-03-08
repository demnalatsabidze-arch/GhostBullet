<div align="center">

# 👌🏻 Ghost Bullet 👌🏻
<img width="1280" height="640" alt="Ghost Bullet Logo - Banner" src="https://github.com/user-attachments/assets/7c63dd75-4825-4630-8485-9af92fc7481d" />

**The Ultimate Tor Hidden Service Manager & Dark Net Intelligence Dashboard**

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Docker](https://img.shields.io/badge/Docker-Ready-cyan.svg)](https://www.docker.com/)
[![Tor](https://img.shields.io/badge/Tor-v3_Hidden_Services-indigo.svg)](https://www.torproject.org/)
[![Status](https://img.shields.io/badge/Status-Active-success.svg)]()
[![Developer](https://img.shields.io/badge/Developer-chadi0x-blue.svg)](https://github.com/chadi0x)

*Deploy entirely self-hosted, secure `.onion` sites in seconds with automated multi-threading, dynamic Nginx routing, and integrated Vanity URL generation.*

<img src="https://github.com/user-attachments/assets/b96c1be5-9837-4d9c-b25b-c3030297e8f2" alt="Ghost Bullet Dashboard Preview" onerror="this.style.display='none'">

</div>

---

## 🚀 Overview

**Ghost Bullet** takes the complex, error-prone process of manually configuring Tor hidden services and transforms it into a sleek, automated, cyberpunk-styled dashboard. Built with Docker, Flask, and Nginx, Ghost Bullet allows you to spin up multiple `.onion` websites instantly, either by uploading `.zip` archives directly to the built-in host, or by proxying traffic to your existing containers.

Stop wrestling with `torrc` configurations, `chown` permissions, and broken symlinks. Ghost Bullet handles the invisible network layer so you can focus on building.

## 🕹️ Features

- **Instant Deployment**: Go from a ZIP file to a live V3 `.onion` link in under 10 seconds.
- **Advanced Vanity URLs**: Integrated `mkp224o` worker cluster automatically brute-forces custom `.onion` prefixes in the background.
- **Dynamic Routing**: Built-in Nginx container seamlessly serves dozens of hidden services simultaneously with zero port conflicts.
- **Cyberpunk UI**: A gorgeous, dark-mode administrative dashboard for absolute control over your Tor nodes.
- **Live File Management**: View, edit, and delete hosted site files directly through the dashboard interface.
- **Container Proxying**: Easily bind new Tor links to any pre-existing Docker container on your server.

## 👑 Premium Edition

Enhance your Ghost Bullet installation with advanced offensive and defensive intelligence capabilities. Upgrade to Premium to unlock the top navigation modules:

*   **🛡️ Vulnerability Scanner For Tor**: Scan remote Onion addresses for exposed CVEs, misconfigurations, and standard web vulnerabilities aggressively.
*   **🗄️ Breach Data On Dark Net**: Search massive indexed archives of breached credentials, stolen data, and leaked databases natively from the dashboard.
*   **✅ Validate Sites**: Automatically ping and verify the uptime, signature, and health of thousands of external Onion URLs simultaneously.
*   **🐛 Last Exploits**: Real-time scraping engine monitoring underground forums for zero-days, new exploits, and active malware trends.

<div align="center">
  <a href="https://pay.oxapay.com/15690646">
    <img src="https://img.shields.io/badge/👑_GET_THE_PREMIUM_VERSION_NOW-8A2BE2?style=for-the-badge&logo=github&logoColor=white&labelColor=1a1a1a" alt="Get Premium Version" />
  </a>
</div>

---

## 🛠️ Installation & Setup

Ghost Bullet is entirely containerized. You only need Docker and Docker Compose installed on your host system.

### 1. Clone the Repository
```bash
git clone https://github.com/chadi0x/GhostBullet.git
cd GhostBullet
```

### 2. Configure Environment (Optional)
```bash
cp .env.example .env
# Edit .env if you wish to change default ports or database settings
```

### 3. Build & Launch
```bash
docker compose up -d --build
```
Ghost Bullet will compile the Vanity worker, initialize the database, configure Nginx, and establish a live connection to the Tor network.

### 4. Access the Dashboard
Open your local browser to:
**http://localhost:8008**

---

## ⚡ Usage

### Hosting a Built-in Site
1. Click **DEPLOY SITE** in the top navigation bar.
2. Select **Built-in (Nginx)**.
3. Once the Node is created, click the green **UPLOAD** button on the node card.
4. Select a `.zip` archive containing your `index.html` and assets. Ghost Bullet will instantly extract them and route the Tor traffic.

### File Management
Click the purple **MANAGE FILES** button on any active node to open the File Manager. From here, you can verify file extraction sizes and delete specific `.html` or image assets without wiping the entire node.

### Upgrades & Updates
Click the blue **REWRITE FILES** button to completely replace an existing node with a fresh `.zip` payload, while retaining the exact same `.onion` address.

---

## ⚠️ Disclaimer

Ghost Bullet is provided strictly for educational purposes, security research, and legitimate privacy preservation. **Tor is a privacy tool, not a criminal one.** 

The developer (**chadi0x**) is not responsible for any misuse, damage, or illegal activities conducted using this software. We do not endorse or support the use of Ghost Bullet to host illegal content or services. By using this software, you take full responsibility for your actions and how you choose to use it. Always ensure you have explicit permission before scanning or interacting with third-party hidden services.

---
<div align="center">
    <p>Developed with ❤️ by <a href="https://github.com/chadi0x">chadi0x</a></p>
</div>
