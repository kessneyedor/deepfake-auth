# 🔐 Proactive Deepfake Authentication System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-Web%20App-black?style=for-the-badge&logo=flask)
![OpenAI CLIP](https://img.shields.io/badge/CLIP-ViT--B%2F32-412991?style=for-the-badge&logo=openai)
![Blockchain](https://img.shields.io/badge/Blockchain-SHA256-orange?style=for-the-badge)
![Ed25519](https://img.shields.io/badge/Signing-Ed25519-green?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**A unified pipeline for watermarking, blockchain anchoring, key management, and CLIP-based semantic verification**

[🌐 Live Demo](https://kessney22-deepfake-auth.hf.space) • [📄 Paper](https://its2026tokyo.org) • [🎓 Kyungdong University](https://kduniv.ac.kr)

</div>

---

## 📌 Overview

This system provides **proactive media authentication** — certifying images at the point of creation and enabling downstream verification throughout the content lifecycle. Unlike reactive deepfake detectors that analyze statistical artifacts after the fact, this system embeds verifiable cryptographic signals into authentic media before distribution.

Presented at **ITS2026Tokyo** (25th Biennial Conference of the International Telecommunications Society, June 28–July 1, 2026) under the paper:

> *"Proactive Deepfake Authentication System: A Unified Pipeline for Watermarking, Blockchain Anchoring, Key Management, and CLIP-Based Semantic Verification"*
> — Akimana Kessney Edor, Department of Smart Computing, Kyungdong University, South Korea

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🖼️ **Invisible Watermarking** | DCT-domain 48-bit payload embedding — PSNR 56.3dB, completely imperceptible |
| 🔑 **Ed25519 Signing** | Post-quantum-ready cryptographic signing — 0.077ms latency, 3,896× faster than RSA |
| 🏛️ **3-Tier Key Management** | HKDF-based Root → Intermediate → Device hierarchy with rotation and revocation |
| 🧠 **CLIP Semantic Fingerprint** | OpenAI ViT-B/32 — 512-dim vector, similarity 1.0000 between original and watermarked |
| ⛓️ **Blockchain Registry** | SHA-256 content hash anchoring — 2.23ms registration latency |
| 🔍 **Tamper Localization** | DCT heatmap showing exactly WHERE an image was modified after certification |
| 🌐 **Web Interface** | Two-mode Flask app — Mode 1: Certify, Mode 2: Verify |

---

## 🏆 Novel Contributions

1. **First formally benchmarked end-to-end pipeline latency** — 183ms mean on CPU (n=50), closing the measurement gap left open by Yang & Kim (2026)
2. **First complete key lifecycle management** in this research domain — HKDF derivation, rotation scheduling, on-chain revocation
3. **First spatial tamper localization** — DCT heatmap identifies modified regions, capability absent from all prior systems

---

## 📊 Results

| Metric | Result | Target | Status |
|---|---|---|---|
| End-to-end latency | 183ms (n=50) | < 500ms | ✅ Pass |
| Watermark PSNR | 56.3 dB | > 40 dB | ✅ Pass |
| BER (clean images) | 0.000 | 0.000 | ✅ Pass |
| JPEG-90 detection | 90% | > 80% | ✅ Pass |
| Resize-75% detection | 100% | > 80% | ✅ Pass |
| Noise σ=10 detection | 100% | > 80% | ✅ Pass |
| CLIP similarity | 1.0000 | > 0.99 | ✅ Pass |
| Blockchain registration | 2.23ms | < 50ms | ✅ Pass |
| Verified authentic | 10/10 | 10/10 | ✅ Pass |
| JPEG-70 detection | 0% | > 80% | ⚠️ Limitation |

---

## 🗂️ Project Structure

```
deepfake_auth/
├── app.py                          # Flask web interface (Mode 1: Certify, Mode 2: Verify)
├── main.py                         # End-to-end pipeline runner
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker deployment (Hugging Face Spaces)
├── README.md
│
├── src/
│   ├── signing/
│   │   ├── ecc_sign.py             # Ed25519 signing — 0.077ms latency
│   │   └── key_manager.py          # 3-tier HKDF key hierarchy
│   ├── watermark/
│   │   ├── dct_embed.py            # DCT watermark embedding — PSNR 56.3dB
│   │   └── dct_decode.py           # DCT watermark decoding
│   ├── metadata/
│   │   └── extract.py              # EXIF provenance extraction → C2PA format
│   └── verification/
│       ├── verifier.py             # Cross-layer multi-signal verifier
│       ├── blockchain.py           # JSON blockchain content registry
│       ├── clip_fingerprint.py     # CLIP ViT-B/32 semantic fingerprinting
│       └── tamper_localize.py      # DCT heatmap spatial tamper detection
│
├── data/
│   ├── images/                     # Test images
│   └── results/
│       ├── signing_latency.csv     # Ed25519 benchmark results
│       ├── robustness_results.csv  # Attack robustness per attack type
│       ├── final_benchmark.csv     # 50-iteration pipeline benchmark
│       ├── blockchain_registry.json
│       └── key_events.json
│
└── paper/
    └── figures/
        ├── pipeline_architecture.png
        ├── pipeline_latency.png
        ├── robustness_results.png
        └── signing_latency.png
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- No GPU required — runs entirely on CPU

### Installation

```bash
# Clone the repository
git clone https://github.com/kessneyedor/deepfake-auth.git
cd deepfake-auth

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install flask numpy scipy matplotlib pillow opencv-python scikit-image cryptography pandas torch torchvision
pip install git+https://github.com/openai/CLIP.git
```

### Run the Web Interface

```bash
python app.py
```

Open your browser at `http://127.0.0.1:5000`

> **Note:** First run downloads the CLIP model (~350MB). Subsequent runs are instant.

---

## 🌐 Live Demo

The system is deployed on Hugging Face Spaces:

**[https://kessney22-deepfake-auth.hf.space](https://kessney22-deepfake-auth.hf.space)**

### Demo Scenarios

| Scenario | Steps | Expected Result |
|---|---|---|
| **Certify** | Upload any image in Mode 1 | Downloads `KDUniv_certified.png` with embedded watermark |
| **Verify Authentic** | Upload certified image in Mode 2 | ✅ AUTHENTIC — Confidence: 1.000 |
| **Verify Suspicious** | Upload any uncertified image | ❌ SUSPICIOUS — all signals fail |
| **Tamper Detection** | Modify certified image in Paint → upload | ❌ SUSPICIOUS + heatmap showing WHERE |

---

## 🔧 Pipeline Components

### 1. Metadata Extraction
Extracts EXIF device metadata and packages into a C2PA-compatible provenance record. Any modification invalidates the signature.

### 2. Ed25519 Digital Signing
Signs the provenance record using the institution's device key. Selected over RSA for:
- **0.077ms** signing latency vs ~300ms for RSA
- Post-quantum resistance (NIST roadmap)
- Smaller key and signature sizes

### 3. Three-Tier Key Management
```
ROOT KEY (never rotates)
    └── INTERMEDIATE KEY (HKDF, rotates 90 days)
            └── DEVICE KEY (HKDF, rotates 30 days) → signs media
```
First complete key lifecycle implementation in this research domain.

### 4. CLIP Semantic Fingerprinting
OpenAI CLIP ViT-B/32 encodes each image into a 512-dimensional normalized vector. Similarity below 0.95 indicates semantic manipulation.

### 5. DCT Watermark Embedding
Embeds 48-bit payload into mid-frequency DCT coefficients of 8×8 blocks:
- **Source institution ID** (8 bits)
- **Capture timestamp** (32 bits)
- **Frame sequence number** (8 bits)

### 6. Blockchain Content Registry
SHA-256 hash of watermarked image anchored in JSON-linked chain. Any pixel-level modification produces a different hash → NOT_FOUND.

### 7. Tamper Localization
DCT coefficient comparison block-by-block between certified and submitted image. JET colormap heatmap: **RED = modified | BLUE = unchanged**.

---

## 📖 Citation

If you use this work, please cite:

```bibtex
@inproceedings{edor2026proactive,
  title={Proactive Deepfake Authentication System: A Unified Pipeline for 
         Watermarking, Blockchain Anchoring, Key Management, and 
         CLIP-Based Semantic Verification},
  author={Edor, Akimana Kessney},
  booktitle={Proceedings of the 25th Biennial Conference of the 
             International Telecommunications Society (ITS2026Tokyo)},
  year={2026},
  address={Tokyo, Japan}
}
```

---

## 🔭 Future Work

- [ ] Expand evaluation to CelebA-HQ (200,000 images) and FaceForensics++
- [ ] Replace DCT embedding with lightweight learned watermarking for JPEG-70 robustness
- [ ] Deploy blockchain registry on Ethereum Sepolia testnet
- [ ] Offline-first certification with deferred blockchain synchronization
- [ ] Video authentication via frame-by-frame processing with temporal consistency
- [ ] Mobile verification app for citizen-level media checking

---

## ⚠️ Limitations

- **JPEG-70**: 0% detection — aggressive JPEG quantization overwrites mid-frequency DCT coefficients
- **Analog hole**: Re-photographing a screen with a camera destroys the digital watermark
- **Blockchain**: Local simulation — production deployment requires on-chain anchoring
- **Dataset**: 10-image proof-of-concept evaluation

---

## 📋 References

- Yang & Kim (2026). Broker-assisted blockchain trust chains for media provenance authentication.
- Das et al. (2026). SAiW: Source-attributable invisible watermarking. IEEE TIFS.
- Corcoran et al. (2021). Countermeasure against deepfake using steganography. IEEE ICCE.
- Lai et al. (2025). Enhancing deepfake detection: Proactive forensics via digital watermarking. ACM Computing Surveys.
- Radford et al. (2021). Learning transferable visual models from natural language supervision. ICML.

---

## 👨‍💻 Author

**Akimana Kessney Edor**
Department of Smart Computing, Kyungdong University, South Korea
📧 kessneyedor@v.kduniv.ac.kr
🌐 [GitHub](https://github.com/kessneyedor)

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">
Made with ❤️ at Kyungdong University, South Korea 🇰🇷
<br>
Presented at ITS2026Tokyo 🇯🇵
</div>
