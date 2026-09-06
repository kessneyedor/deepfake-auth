# 🔐 Proactive Deepfake Authentication System

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-Web%20App-black?style=for-the-badge&logo=flask)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

A unified pipeline for watermarking, blockchain anchoring, key management, and CLIP-based semantic verification.

🌐 **Live Demo:** https://kessney22-deepfake-auth.hf.space

---

## 📌 About

This system provides **proactive media authentication** — certifying images at the point of creation and enabling downstream verification. Presented at **ITS2026Tokyo** (June 28–July 1, 2026).

> Akimana Kessney Edor — Department of Smart Computing, Kyungdong University, South Korea

---

## ✨ Features

- 🖼️ **DCT Watermarking** — invisible 48-bit payload, PSNR 56.3dB
- 🔑 **Ed25519 Signing** — 0.077ms latency, 3,896× faster than RSA
- 🏛️ **3-Tier Key Management** — HKDF hierarchy with rotation and revocation
- 🧠 **CLIP Fingerprinting** — OpenAI ViT-B/32 semantic verification
- ⛓️ **Blockchain Registry** — SHA-256 content hash anchoring
- 🔍 **Tamper Localization** — DCT heatmap showing WHERE image was modified
- 🌐 **Web Interface** — Mode 1: Certify, Mode 2: Verify

---

## 📊 Key Results

| Metric | Result | Status |
|---|---|---|
| End-to-end latency | 183ms (n=50) | ✅ Pass |
| Watermark PSNR | 56.3 dB | ✅ Pass |
| BER clean images | 0.000 | ✅ Pass |
| JPEG-90 detection | 90% | ✅ Pass |
| CLIP similarity | 1.0000 | ✅ Pass |
| Verified authentic | 10/10 | ✅ Pass |
| JPEG-70 detection | 0% | ⚠️ Limitation |

---

## 🚀 Quick Start

```bash
git clone https://github.com/kessneyedor/deepfake-auth.git
cd deepfake-auth
python -m venv venv
venv\Scripts\activate
pip install flask numpy scipy matplotlib pillow opencv-python scikit-image cryptography pandas torch torchvision
pip install git+https://github.com/openai/CLIP.git
python app.py
```

Open browser at `http://127.0.0.1:5000`

---

## 🏆 Novel Contributions

1. First formally benchmarked end-to-end latency — 183ms on CPU
2. First complete key lifecycle management in this research domain
3. First spatial tamper localization using DCT heatmap

---

## ⚠️ Limitations

- JPEG-70: 0% detection
- Analog hole not mitigated
- Blockchain is local simulation
- 10-image proof-of-concept dataset

---

## 🔭 Future Work

- [ ] Expand to CelebA-HQ (200,000 images)
- [ ] Ethereum Sepolia testnet deployment
- [ ] Video authentication
- [ ] Mobile verification app

---

## 👨‍💻 Author

**Akimana Kessney Edor**
📧 kessneyedor@v.kduniv.ac.kr
🌐 github.com/kessneyedor

---

*Made with ❤️ at Kyungdong University 🇰🇷 | Presented at ITS2026Tokyo 🇯🇵*
