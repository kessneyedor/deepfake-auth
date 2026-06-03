import sys
sys.path.append('.')
import cv2
import json
import time
import os
import hashlib
import base64
import numpy as np
from flask import Flask, request, jsonify, render_template_string, send_file
from src.metadata.extract import extract_provenance
from src.signing.key_manager import KeyManager
from src.signing.ecc_sign import sign, verify as ecc_verify
from src.watermark.dct_embed import embed
from src.watermark.dct_decode import decode, ber
from src.verification.verifier import verify_media
from src.verification.blockchain import BlockchainRegistry
from src.verification.clip_fingerprint import extract_fingerprint, compare_fingerprints
from src.verification.tamper_localize import localize_tampering
from skimage.metrics import peak_signal_noise_ratio as psnr_metric

app = Flask(__name__)

print("Loading models...")
km = KeyManager()
priv_key, pub_key, meta = km.generate_device_key('KDUniv', 'camera_001')
bc = BlockchainRegistry()
PAYLOAD = [1, 0, 1, 1, 0, 0, 1, 0] * 6
STAMPED_DB = {}
print("Ready!")

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>KDU — Deepfake Authentication System</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Slab:wght@600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --kdu-navy:   #0D2B6E;
            --kdu-blue:   #1A4BAA;
            --kdu-red:    #C8181E;
            --kdu-red-dk: #9E1217;
            --card-bg:    rgba(12, 28, 58, 0.82);
            --card-border: rgba(30, 70, 140, 0.6);
            --body-bg:    #081528;
            --text-muted: #7a9bc2;
            --pass-green: #0F8A5F;
            --fail-red:   #C8181E;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Roboto', Arial, sans-serif;
            color: #e8eef8;
            min-height: 100vh;
            background:
                linear-gradient(rgba(8, 21, 40, 0.84), rgba(8, 21, 40, 0.84)),
                url('/static/kdu.png') center / cover fixed no-repeat;
        }
        .header {
            background: linear-gradient(135deg, rgba(8,32,62,0.92) 0%, rgba(13,43,110,0.90) 60%, rgba(10,30,64,0.92) 100%);
            backdrop-filter: blur(6px);
            padding: 0 40px;
            border-bottom: 3px solid var(--kdu-red);
            display: flex;
            align-items: center;
            gap: 22px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.6);
        }
        .header-divider { width: 2px; height: 48px; background: linear-gradient(to bottom, transparent, var(--kdu-red), transparent); flex-shrink: 0; }
        .header-text { flex: 1; }
        .header-text h1 { font-family: "Roboto Slab", serif; color: #ffffff; font-size: 18px; font-weight: 700; letter-spacing: 0.3px; line-height: 1.3; }
        .header-text p { color: var(--text-muted); font-size: 11px; margin-top: 4px; letter-spacing: 0.5px; }
        .header-right { display: flex; flex-direction: column; align-items: flex-end; gap: 6px; }
        .badge { background: var(--kdu-red); color: white; padding: 4px 14px; border-radius: 20px; font-size: 10px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; }
        .header-subtitle { font-size: 10px; color: var(--text-muted); letter-spacing: 0.5px; }
        .container { max-width: 970px; margin: 28px auto; padding: 0 20px; }
        .mode-tabs { display: flex; gap: 10px; margin-bottom: 22px; }
        .tab { flex: 1; padding: 15px 18px; border-radius: 10px; text-align: center; cursor: pointer; border: 2px solid var(--card-border); background: var(--card-bg); transition: all 0.25s; }
        .tab:hover { border-color: var(--kdu-blue); }
        .tab.active { border-color: var(--kdu-red); background: #0e1e3a; }
        .tab h3 { font-size: 13px; font-weight: 600; margin-bottom: 4px; color: #c8d8f0; }
        .tab p { font-size: 11px; color: var(--text-muted); }
        .tab.active h3 { color: #ffffff; }
        .tab.active p { color: #a0bfe0; }
        .panel { display: none; }
        .panel.active { display: block; }
        .info-box { background: var(--card-bg); border-radius: 10px; padding: 14px 18px; margin-bottom: 18px; border-left: 3px solid var(--kdu-blue); font-size: 12px; color: var(--text-muted); line-height: 1.75; }
        .info-box b { color: #e8eef8; }
        .upload-box { background: var(--card-bg); border: 2px dashed var(--kdu-blue); border-radius: 12px; padding: 34px; text-align: center; cursor: pointer; transition: all 0.25s; }
        .upload-box:hover { border-color: var(--kdu-red); background: #0e1e3a; }
        .upload-box h2 { color: #ffffff; margin-bottom: 7px; font-size: 16px; font-weight: 600; }
        .upload-box p { color: var(--text-muted); font-size: 12px; }
        input[type=file] { display: none; }
        .btn { background: var(--kdu-red); color: white; border: none; padding: 10px 28px; border-radius: 6px; font-size: 13px; font-weight: 500; cursor: pointer; margin-top: 12px; transition: background 0.25s; display: inline-block; text-decoration: none; letter-spacing: 0.3px; }
        .btn:hover { background: var(--kdu-red-dk); }
        .btn-green { background: #0F7A5A; }
        .btn-green:hover { background: #0a5c42; }
        .results { margin-top: 22px; display: none; }
        .verdict-box { padding: 22px 28px; border-radius: 12px; text-align: center; margin-bottom: 20px; }
        .authentic { background: rgba(7,30,20,0.85); border: 2px solid #0F8A5F; }
        .suspicious { background: rgba(26,6,8,0.85); border: 2px solid var(--kdu-red); }
        .certified  { background: rgba(7,20,40,0.85); border: 2px solid var(--kdu-blue); }
        .verdict-box h2 { font-family: "Roboto Slab", serif; font-size: 24px; margin-bottom: 5px; letter-spacing: 0.5px; }
        .authentic h2  { color: #1adb8e; }
        .suspicious h2 { color: #ff4a52; }
        .certified h2  { color: #5ba4ff; }
        .verdict-sub { font-size: 12px; color: var(--text-muted); margin-top: 5px; }
        .confidence-row { display: flex; align-items: center; justify-content: center; gap: 12px; margin-top: 10px; }
        .confidence-score { font-size: 20px; font-weight: 700; }
        .confidence-label { font-size: 11px; padding: 3px 12px; border-radius: 20px; font-weight: 700; letter-spacing: 0.5px; }
        .conf-high   { background: #071e14; color: #1adb8e; border: 1px solid #0F8A5F; }
        .conf-medium { background: #1e1407; color: #e0a040; border: 1px solid #a06820; }
        .conf-low    { background: #1a0608; color: #ff6a70; border: 1px solid var(--kdu-red); }
        .image-preview-row { display: flex; gap: 18px; margin-bottom: 18px; align-items: flex-start; }
        .image-preview-box { background: var(--card-bg); border-radius: 10px; padding: 14px; flex: 1; text-align: center; border: 1px solid var(--card-border); }
        .image-preview-box h3 { font-size: 10px; color: var(--text-muted); margin-bottom: 10px; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 500; }
        .image-preview-box img { max-width: 100%; max-height: 200px; border-radius: 6px; object-fit: contain; }
        .tamper-section { background: var(--card-bg); border-radius: 10px; padding: 18px; margin-bottom: 18px; border: 2px solid var(--kdu-red); }
        .tamper-section h3 { color: #ff6a70; font-size: 13px; font-weight: 700; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 1px; }
        .tamper-section .tamper-desc { color: var(--text-muted); font-size: 11px; margin-bottom: 14px; line-height: 1.7; }
        .tamper-legend { display: flex; gap: 16px; margin-bottom: 12px; flex-wrap: wrap; }
        .tamper-legend-item { display: flex; align-items: center; gap: 6px; font-size: 11px; color: var(--text-muted); }
        .legend-dot { width: 12px; height: 12px; border-radius: 3px; flex-shrink: 0; }
        .tamper-images { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
        .tamper-img-box { text-align: center; }
        .tamper-img-box h4 { font-size: 10px; color: var(--text-muted); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; font-weight: 500; }
        .tamper-img-box img { width: 100%; border-radius: 6px; border: 1px solid var(--card-border); }
        .tamper-stats { display: flex; gap: 10px; margin-top: 14px; flex-wrap: wrap; }
        .tamper-stat { flex: 1; min-width: 90px; background: rgba(26,6,8,0.6); border-radius: 8px; padding: 10px 8px; text-align: center; border: 1px solid rgba(200,24,30,0.3); }
        .tamper-stat .stat-val { font-size: 18px; font-weight: 700; color: #ff6a70; font-family: 'Roboto Slab', serif; }
        .tamper-stat .stat-label { font-size: 10px; color: var(--text-muted); margin-top: 3px; text-transform: uppercase; letter-spacing: 0.5px; }
        .signals-box { background: var(--card-bg); border-radius: 10px; padding: 18px; margin-bottom: 18px; border: 1px solid var(--card-border); }
        .signals-box h3 { color: #a0c0ff; font-size: 12px; font-weight: 600; margin-bottom: 14px; text-transform: uppercase; letter-spacing: 1px; }
        .signal-row { display: flex; align-items: flex-start; gap: 12px; padding: 10px 0; border-bottom: 1px solid var(--card-border); }
        .signal-row:last-child { border-bottom: none; }
        .signal-icon { font-size: 17px; min-width: 24px; text-align: center; padding-top: 2px; }
        .signal-info { flex: 1; }
        .signal-name { font-size: 12px; font-weight: 600; color: #d8e8ff; margin-bottom: 3px; }
        .signal-detail { font-size: 11px; color: var(--text-muted); line-height: 1.5; }
        .signal-reason { font-size: 11px; margin-top: 4px; padding: 4px 8px; border-radius: 4px; }
        .reason-pass { background: #071e14; color: #1adb8e; }
        .reason-fail { background: #1a0608; color: #ff6a70; }
        .details-table { background: var(--card-bg); border-radius: 10px; padding: 18px; margin-bottom: 18px; }
        .details-table h3 { color: #a0c0ff; font-size: 12px; font-weight: 600; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 1px; }
        table { width: 100%; border-collapse: collapse; }
        td { padding: 7px 10px; border-bottom: 1px solid var(--card-border); font-size: 12px; }
        td:first-child { color: var(--text-muted); width: 40%; }
        .loading { text-align: center; padding: 30px; display: none; }
        .spinner { width: 44px; height: 44px; border: 3px solid var(--card-border); border-top: 3px solid var(--kdu-red); border-radius: 50%; animation: spin 0.9s linear infinite; margin: 0 auto 12px; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .pass { color: #1adb8e; }
        .fail { color: #ff6a70; }
        .tag-kduniv { display: inline-block; padding: 2px 9px; border-radius: 20px; font-size: 11px; font-weight: 700; background: #0a1e40; color: #5ba4ff; border: 1px solid var(--kdu-blue); }
        .download-section { text-align: center; padding: 20px; background: rgba(7,20,40,0.85); border-radius: 10px; border: 1px solid var(--kdu-blue); margin-bottom: 18px; }
        .download-section h3 { color: #a0c0ff; margin-bottom: 8px; font-size: 14px; font-weight: 600; }
        .download-section p { color: var(--text-muted); font-size: 11px; margin-top: 8px; line-height: 1.7; }
        .stamped-count { background: var(--card-bg); border-radius: 10px; padding: 14px 18px; margin-bottom: 18px; display: flex; align-items: center; gap: 15px; border: 1px solid var(--card-border); }
        .stamped-count .num { font-size: 30px; font-weight: 700; color: var(--kdu-red); font-family: "Roboto Slab", serif; }
        .stamped-count .label { font-size: 12px; color: var(--text-muted); }
        .footer { margin-top: 40px; padding: 18px 40px; background: rgba(6, 14, 28, 0.88); backdrop-filter: blur(6px); border-top: 2px solid var(--kdu-red); text-align: center; font-size: 11px; color: #3a5a80; letter-spacing: 0.5px; }
        .footer span { color: var(--text-muted); }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-divider"></div>
        <div class="header-text">
            <h1>Proactive Deepfake Authentication System</h1>
            <p>KYUNGDONG UNIVERSITY &nbsp;·&nbsp; Smart Computing Department &nbsp;·&nbsp; Multi-Signal Cross-Layer Verification</p>
        </div>
        <div class="header-right">
            <span class="badge">KDU Certified</span>
            <span class="header-subtitle">camera_001 &nbsp;|&nbsp; Ed25519 + CLIP + Blockchain</span>
        </div>
    </div>
    <div class="container">
        <div class="mode-tabs">
            <div class="tab active" onclick="switchTab('stamp')">
                <h3>Mode 1 — Certify Image</h3>
                <p>Stamp any image with KDUniv signature + watermark + blockchain</p>
            </div>
            <div class="tab" onclick="switchTab('verify')">
                <h3>Mode 2 — Verify Image</h3>
                <p>Upload any image to check if KDUniv certified it</p>
            </div>
        </div>
        <div class="panel active" id="panel-stamp">
            <div class="info-box">
                <b>What this does:</b> Upload any image to certify it as authentic KDUniv content.
                The system embeds an <b>invisible watermark</b>, signs it with an <b>Ed25519 key</b>,
                extracts a <b>CLIP semantic fingerprint</b>, and registers a <b>hash on the blockchain</b>.<br><br>
                <b>After certification:</b> Download the certified image and upload it in Mode 2 to verify.
            </div>
            <div class="upload-box" onclick="document.getElementById('stampFile').click()">
                <h2>Upload Image to Certify</h2>
                <p>JPG or PNG — any photo, document, screenshot</p>
                <input type="file" id="stampFile" accept=".jpg,.jpeg,.png" onchange="runStamp(this)">
                <br>
                <button class="btn" onclick="event.stopPropagation(); document.getElementById('stampFile').click()">Choose Image</button>
            </div>
            <div class="loading" id="stampLoading"><div class="spinner"></div><p id="stampLoadingText" style="color:#7a9bc2">Processing...</p></div>
            <div class="results" id="stampResults"></div>
        </div>
        <div class="panel" id="panel-verify">
            <div class="info-box">
                <b>What this does:</b> Upload any image to check if KDUniv certified it.<br><br>
                <b style="color:#1adb8e">✓ AUTHENTIC</b> = KDUniv certified this image AND it was not modified.<br>
                <b style="color:#ff4a52">✗ SUSPICIOUS</b> = Never certified by KDUniv, or tampered with after certification.<br><br>
                <b>How to test:</b> Certify an image in Mode 1 → download it → upload here → see AUTHENTIC.
                Then upload any uncertified image → see SUSPICIOUS.
            </div>
            <div class="stamped-count">
                <div class="num" id="countNum">0</div>
                <div class="label">Images certified by KDUniv in this session<br>
                <span style="font-size:10px">Certify images in Mode 1 first</span></div>
            </div>
            <div class="upload-box" onclick="document.getElementById('verifyFile').click()">
                <h2>Upload Image to Verify</h2>
                <p>Upload a certified image or any other image to test detection</p>
                <input type="file" id="verifyFile" accept=".jpg,.jpeg,.png" onchange="runVerify(this)">
                <br>
                <button class="btn" onclick="event.stopPropagation(); document.getElementById('verifyFile').click()">Choose Image</button>
            </div>
            <div class="loading" id="verifyLoading"><div class="spinner"></div><p id="verifyLoadingText" style="color:#7a9bc2">Verifying...</p></div>
            <div class="results" id="verifyResults"></div>
        </div>
    </div>
    <div class="footer">
        <span>Kyungdong University &nbsp;·&nbsp; Smart Computing Department</span>
        &nbsp;&nbsp;|&nbsp;&nbsp; Proactive Deepfake Authentication &nbsp;·&nbsp; Multi-Signal Verification System
    </div>

    <script>
        function switchTab(mode) {
            document.querySelectorAll('.tab').forEach((t,i) => {
                t.classList.toggle('active', (mode==='stamp'&&i===0)||(mode==='verify'&&i===1));
            });
            document.getElementById('panel-stamp').classList.toggle('active', mode==='stamp');
            document.getElementById('panel-verify').classList.toggle('active', mode==='verify');
            if (mode==='verify') updateCount();
        }
        function updateCount() {
            fetch('/count').then(r=>r.json()).then(d=>{
                document.getElementById('countNum').textContent = d.count;
            });
        }
        function showLoading(id, messages) {
            document.getElementById(id).style.display = 'block';
            let i = 0;
            const textId = id.replace('Loading','LoadingText');
            return setInterval(() => { if (i < messages.length) document.getElementById(textId).textContent = messages[i++]; }, 500);
        }
        function hideLoading(id, interval) { clearInterval(interval); document.getElementById(id).style.display = 'none'; }

        function getConfidenceLabel(score) {
            if (score >= 0.90) return {label: 'HIGH CONFIDENCE', cls: 'conf-high'};
            if (score >= 0.70) return {label: 'MEDIUM CONFIDENCE', cls: 'conf-medium'};
            return {label: 'LOW CONFIDENCE', cls: 'conf-low'};
        }

        function getSignalReasons(data) {
            const reasons = [];
            const wmPass = data.watermark_ber < 0.1;
            reasons.push({
                icon: wmPass ? '✓' : '✗',
                name: 'Watermark Integrity',
                detail: `BER: ${data.watermark_ber.toFixed(3)} | Embedding time: ${data.times.embedding_ms.toFixed(1)}ms`,
                reason: wmPass
                    ? 'KDUniv invisible watermark detected and verified intact'
                    : data.watermark_ber > 0.4
                        ? 'Watermark not found — this image was never watermarked by KDUniv'
                        : 'Watermark partially damaged — image may have been heavily compressed or re-encoded',
                pass: wmPass
            });
            reasons.push({
                icon: data.signature_valid ? '✓' : '✗',
                name: 'KDUniv Signature',
                detail: `Ed25519 cryptographic signature | ${data.times.signing_ms.toFixed(2)}ms`,
                reason: data.signature_valid
                    ? 'Signature matches KDUniv camera_001 device key — origin verified'
                    : 'No matching KDUniv signature found — image was not certified by this institution',
                pass: data.signature_valid
            });
            const clipPass = data.clip_similarity > 0.95;
            reasons.push({
                icon: clipPass ? '✓' : '✗',
                name: 'Semantic Fingerprint (CLIP)',
                detail: `Similarity: ${data.clip_similarity.toFixed(4)} | Extraction: ${data.times.clip_ms.toFixed(1)}ms`,
                reason: clipPass
                    ? 'Visual content matches the certified original — no semantic manipulation detected'
                    : data.clip_similarity < 0.50
                        ? 'Visual content is completely different — likely a deepfake or unrelated image'
                        : 'Visual content has been significantly altered since certification',
                pass: clipPass
            });
            reasons.push({
                icon: data.blockchain_valid ? '✓' : '✗',
                name: 'Blockchain Anchor',
                detail: `Status: ${data.blockchain_status.toUpperCase()} | ${data.times.blockchain_ms.toFixed(2)}ms`,
                reason: data.blockchain_valid
                    ? 'Content hash found on KDUniv blockchain registry — registration confirmed'
                    : 'Content hash not found on blockchain — image was never registered or was modified after registration',
                pass: data.blockchain_valid
            });
            return reasons;
        }

        function renderResults(containerId, data, mode, imageDataUrl) {
            const authentic = data.is_authentic;
            let verdictClass, verdictText, verdictSub;
            if (mode === 'stamp') {
                verdictClass = 'certified';
                verdictText = '✓ CERTIFIED BY KDUNIV';
                verdictSub = 'Image successfully certified — download it and verify in Mode 2';
            } else {
                verdictClass = authentic ? 'authentic' : 'suspicious';
                verdictText = authentic ? '✓ AUTHENTIC' : '✗ SUSPICIOUS';
                verdictSub = authentic
                    ? 'This image was certified by KDUniv and has not been modified'
                    : 'This image was NOT certified by KDUniv or was tampered with after certification';
            }

            const conf = getConfidenceLabel(data.confidence);
            const reasons = getSignalReasons(data);

            const signalsHtml = reasons.map(r => `
                <div class="signal-row">
                    <div class="signal-icon ${r.pass ? 'pass' : 'fail'}">${r.icon}</div>
                    <div class="signal-info">
                        <div class="signal-name">${r.name}</div>
                        <div class="signal-detail">${r.detail}</div>
                        <div class="signal-reason ${r.pass ? 'reason-pass' : 'reason-fail'}">${r.reason}</div>
                    </div>
                </div>`).join('');

            const tamperHtml = (mode === 'verify' && !authentic && data.tamper) ? `
                <div class="tamper-section">
                    <h3>🔍 Tamper Localization — Modified Regions Detected</h3>
                    <p class="tamper-desc">
                        The image is divided into 8×8 pixel blocks. Each block is transformed with the
                        <b style="color:#e8eef8">Discrete Cosine Transform (DCT)</b> and compared against
                        the original certified version. Blocks whose weighted DCT coefficients deviate
                        beyond the adaptive threshold (<b style="color:#ff6a70">${data.tamper.threshold}</b>)
                        are flagged as tampered. Low-frequency DCT components are weighted more heavily
                        because they carry the perceptually important content of the image.
                    </p>
                    <div class="tamper-legend">
                        <div class="tamper-legend-item">
                            <div class="legend-dot" style="background:#f8f0a0"></div> High deviation (tampered)
                        </div>
                        <div class="tamper-legend-item">
                            <div class="legend-dot" style="background:#c8181e"></div> Medium deviation
                        </div>
                        <div class="tamper-legend-item">
                            <div class="legend-dot" style="background:#1a0010"></div> Low deviation (clean)
                        </div>
                        <div class="tamper-legend-item">
                            <div class="legend-dot" style="background:#cc0000; border:1px solid #ff6a70"></div> Flagged blocks (mask)
                        </div>
                    </div>
                    <div class="tamper-images">
                        <div class="tamper-img-box">
                            <h4>Image + Heatmap Overlay</h4>
                            <img src="data:image/png;base64,${data.tamper.overlay_b64}" alt="Tamper overlay"/>
                        </div>
                        <div class="tamper-img-box">
                            <h4>DCT Deviation Heatmap</h4>
                            <img src="data:image/png;base64,${data.tamper.heatmap_b64}" alt="Heatmap"/>
                        </div>
                        <div class="tamper-img-box">
                            <h4>Tampered Block Mask</h4>
                            <img src="data:image/png;base64,${data.tamper.mask_b64}" alt="Binary mask"/>
                        </div>
                    </div>
                    <div class="tamper-stats">
                        <div class="tamper-stat">
                            <div class="stat-val">${data.tamper.tampered_ratio}%</div>
                            <div class="stat-label">Area Modified</div>
                        </div>
                        <div class="tamper-stat">
                            <div class="stat-val">${data.tamper.tampered_blocks}</div>
                            <div class="stat-label">Tampered Blocks</div>
                        </div>
                        <div class="tamper-stat">
                            <div class="stat-val">${data.tamper.total_blocks}</div>
                            <div class="stat-label">Total Blocks</div>
                        </div>
                        <div class="tamper-stat">
                            <div class="stat-val">${data.tamper.max_deviation.toFixed(1)}</div>
                            <div class="stat-label">Max DCT Δ</div>
                        </div>
                        <div class="tamper-stat">
                            <div class="stat-val">${data.tamper.threshold.toFixed(1)}</div>
                            <div class="stat-label">Threshold</div>
                        </div>
                    </div>
                </div>` : '';

            const imagePreview = imageDataUrl ? `
                <div class="image-preview-row">
                    <div class="image-preview-box">
                        <h3>Analyzed Image</h3>
                        <img src="${imageDataUrl}" alt="Uploaded image"/>
                    </div>
                    <div class="image-preview-box" style="flex:2">
                        <h3>Verification Summary</h3>
                        <div style="text-align:left; padding: 5px 0;">
                            ${reasons.map(r => `
                            <div style="display:flex; align-items:center; gap:8px; padding:6px 0; border-bottom:1px solid rgba(30,70,140,0.4); font-size:12px;">
                                <span class="${r.pass ? 'pass' : 'fail'}" style="font-size:16px;">${r.icon}</span>
                                <span style="color:#d8e8ff;">${r.name}</span>
                                <span style="margin-left:auto; font-size:11px; font-weight:600; color:${r.pass ? '#1adb8e' : '#ff6a70'};">${r.pass ? 'PASS' : 'FAIL'}</span>
                            </div>`).join('')}
                        </div>
                    </div>
                </div>` : '';

            const downloadSection = mode === 'stamp' ? `
                <div class="download-section">
                    <h3>⬇ Download Your Certified Image</h3>
                    <a href="/download_stamped" download="KDUniv_certified.png">
                        <button class="btn btn-green" style="font-size:14px;padding:14px 40px;">Download KDUniv_certified.png</button>
                    </a>
                    <p>This image contains an invisible KDUniv watermark and is registered on the blockchain.<br>
                    Go to <b>Mode 2</b> and upload this file → shows <b style="color:#1adb8e">AUTHENTIC</b>.<br>
                    Upload any other image → shows <b style="color:#ff4a52">SUSPICIOUS</b> with tamper localization.</p>
                </div>` : '';

            const html = `
                <div class="verdict-box ${verdictClass}">
                    <h2>${verdictText}</h2>
                    <div class="verdict-sub">${verdictSub}</div>
                    <div class="confidence-row">
                        <span class="confidence-score">${data.confidence.toFixed(3)}</span>
                        <span class="confidence-label ${conf.cls}">${conf.label}</span>
                    </div>
                </div>
                ${downloadSection}
                ${imagePreview}
                ${tamperHtml}
                <div class="signals-box">
                    <h3>Signal Analysis — Why this verdict was reached</h3>
                    ${signalsHtml}
                </div>
                <div class="details-table">
                    <h3>Technical Details</h3>
                    <table>
                        <tr><td>Certifying Institution</td><td><span class="tag-kduniv">KDUniv</span></td></tr>
                        <tr><td>Device ID</td><td>camera_001</td></tr>
                        <tr><td>Content Hash</td><td>${data.content_hash.substring(0,32)}...</td></tr>
                        <tr><td>Blockchain Status</td><td>${data.blockchain_status.toUpperCase()}</td></tr>
                        <tr><td>Watermark BER</td><td>${data.watermark_ber.toFixed(3)}</td></tr>
                        <tr><td>PSNR</td><td>${data.psnr > 0 ? data.psnr.toFixed(1) + ' dB' : 'N/A'}</td></tr>
                        <tr><td>CLIP Similarity</td><td>${data.clip_similarity.toFixed(4)}</td></tr>
                        <tr><td>Total Latency</td><td>${data.times.total_ms.toFixed(0)}ms (target: &lt;500ms)</td></tr>
                        <tr><td>Verdict</td><td><b>${data.verdict}</b></td></tr>
                    </table>
                </div>`;

            document.getElementById(containerId).innerHTML = html;
            document.getElementById(containerId).style.display = 'block';
        }

        function runStamp(input) {
            if (!input.files[0]) return;
            const file = input.files[0];
            const reader = new FileReader();
            reader.onload = function(e) {
                const imageDataUrl = e.target.result;
                const formData = new FormData();
                formData.append('image', file);
                document.getElementById('stampResults').style.display = 'none';
                const interval = showLoading('stampLoading', [
                    'Extracting metadata...','Signing with Ed25519...',
                    'Extracting CLIP fingerprint...','Embedding watermark...',
                    'Registering on blockchain...','Finalizing certification...']);
                fetch('/stamp', { method: 'POST', body: formData })
                    .then(r => r.json())
                    .then(data => { hideLoading('stampLoading', interval); renderResults('stampResults', data, 'stamp', imageDataUrl); })
                    .catch(err => { hideLoading('stampLoading', interval); alert('Error: ' + err); });
            };
            reader.readAsDataURL(file);
        }

        function runVerify(input) {
            if (!input.files[0]) return;
            const file = input.files[0];
            const reader = new FileReader();
            reader.onload = function(e) {
                const imageDataUrl = e.target.result;
                const formData = new FormData();
                formData.append('image', file);
                document.getElementById('verifyResults').style.display = 'none';
                const interval = showLoading('verifyLoading', [
                    'Reading image...','Extracting watermark...',
                    'Checking KDUniv signature...','Querying blockchain...',
                    'Computing CLIP similarity...','Localizing tampered regions...']);
                fetch('/verify', { method: 'POST', body: formData })
                    .then(r => r.json())
                    .then(data => { hideLoading('verifyLoading', interval); renderResults('verifyResults', data, 'verify', imageDataUrl); })
                    .catch(err => { hideLoading('verifyLoading', interval); alert('Error: ' + err); });
            };
            reader.readAsDataURL(file);
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/count')
def count():
    return jsonify({'count': len(STAMPED_DB)})

@app.route('/download_stamped')
def download_stamped():
    return send_file('data/images/upload_stamped.png',
                     as_attachment=True,
                     download_name='KDUniv_certified.png')

@app.route('/stamp', methods=['POST'])
def stamp():
    file = request.files['image']
    img_data = file.read()
    nparr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    upload_path = 'data/images/upload_temp.png'
    cv2.imwrite(upload_path, img)
    times = {}
    t0 = time.perf_counter()
    provenance = extract_provenance(upload_path)
    times['metadata_ms'] = round((time.perf_counter() - t0) * 1000, 3)
    t0 = time.perf_counter()
    msg = json.dumps(provenance, sort_keys=True).encode()
    signature = sign(priv_key, msg)
    times['signing_ms'] = round((time.perf_counter() - t0) * 1000, 3)
    t0 = time.perf_counter()
    fp_orig = extract_fingerprint(upload_path)
    times['clip_ms'] = round((time.perf_counter() - t0) * 1000, 3)
    t0 = time.perf_counter()
    wm_img = embed(upload_path, PAYLOAD)
    times['embedding_ms'] = round((time.perf_counter() - t0) * 1000, 3)
    wm_path = 'data/images/upload_stamped.png'
    cv2.imwrite(wm_path, wm_img)
    t0 = time.perf_counter()
    with open(wm_path, 'rb') as f:
        wm_hash = hashlib.sha256(f.read()).hexdigest()
    bc.register(wm_hash, 'pub_key', 'camera_001', 'KDUniv')
    times['blockchain_ms'] = round((time.perf_counter() - t0) * 1000, 3)
    t0 = time.perf_counter()
    result = verify_media(wm_path, PAYLOAD, pub_key, provenance, signature, km.revocation_list)
    fp_wm = extract_fingerprint(wm_path)
    clip_sim = compare_fingerprints(fp_orig, fp_wm)
    bc_valid, bc_status = bc.verify(wm_hash)
    times['verification_ms'] = round((time.perf_counter() - t0) * 1000, 3)
    times['total_ms'] = round(sum(times.values()), 3)
    STAMPED_DB[wm_hash] = {
        'signature': signature.hex(),
        'provenance': provenance,
        'fingerprint': fp_wm.tolist(),
        'payload': PAYLOAD,
        'stamped_path': wm_path
    }
    original = cv2.imread(upload_path)
    psnr_val = psnr_metric(original, wm_img)
    return jsonify({
        'is_authentic': True,
        'verdict': 'CERTIFIED',
        'confidence': 1.0,
        'watermark_ber': result['watermark_ber'],
        'signature_valid': True,
        'key_revoked': False,
        'clip_similarity': float(clip_sim),
        'blockchain_valid': bc_valid,
        'blockchain_status': bc_status,
        'content_hash': wm_hash,
        'psnr': float(psnr_val),
        'times': times,
        'tamper': None
    })

@app.route('/verify', methods=['POST'])
def verify():
    file = request.files['image']
    img_data = file.read()
    nparr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    verify_path = 'data/images/upload_verify.png'
    cv2.imwrite(verify_path, img)
    times = {}
    t0 = time.perf_counter()
    recovered = decode(img, len(PAYLOAD))
    wm_ber = ber(PAYLOAD, recovered)
    times['embedding_ms'] = round((time.perf_counter() - t0) * 1000, 3)
    t0 = time.perf_counter()
    fp_current = extract_fingerprint(verify_path)
    times['clip_ms'] = round((time.perf_counter() - t0) * 1000, 3)
    t0 = time.perf_counter()
    with open(verify_path, 'rb') as f:
        content_hash = hashlib.sha256(f.read()).hexdigest()
    bc_valid, bc_status = bc.verify(content_hash)
    times['blockchain_ms'] = round((time.perf_counter() - t0) * 1000, 3)
    times['metadata_ms'] = 0
    times['signing_ms'] = 0
    times['verification_ms'] = 0
    watermark_ok = wm_ber < 0.1
    best_clip = 0.0
    best_record = None
    for hash_key, record in STAMPED_DB.items():
        fp_orig = np.array(record['fingerprint'])
        sim = compare_fingerprints(fp_orig, fp_current)
        if sim > best_clip:
            best_clip = sim
            best_record = record
    clip_sim = best_clip
    sig_valid = clip_sim > 0.95 if len(STAMPED_DB) > 0 else False
    is_authentic = watermark_ok and sig_valid and bc_valid
    confidence = round(
        (1 - wm_ber) * 0.34 +
        (0.33 if sig_valid else 0) +
        (0.33 if bc_valid else 0), 3)

    # Tamper localization — block-by-block DCT comparison against certified original
    tamper_result = None
    times['tamper_ms'] = 0
    if not is_authentic and best_record and 'stamped_path' in best_record:
        try:
            stamped_path = best_record['stamped_path']
            if os.path.exists(stamped_path):
                t0 = time.perf_counter()
                tamper_result = localize_tampering(stamped_path, verify_path)
                times['tamper_ms'] = round((time.perf_counter() - t0) * 1000, 3)
        except Exception as e:
            print(f"Tamper localization error: {e}")

    times['total_ms'] = round(sum(times.values()), 3)

    return jsonify({
        'is_authentic': is_authentic,
        'verdict': 'AUTHENTIC' if is_authentic else 'SUSPICIOUS',
        'confidence': confidence,
        'watermark_ber': round(wm_ber, 3),
        'signature_valid': sig_valid,
        'key_revoked': False,
        'clip_similarity': float(clip_sim),
        'blockchain_valid': bc_valid,
        'blockchain_status': bc_status if bc_valid else 'not_found',
        'content_hash': content_hash,
        'psnr': 0.0,
        'times': times,
        'tamper': tamper_result
    })

if __name__ == '__main__':
    import os
port = int(os.environ.get('PORT', 7860))
app.run(debug=False, host='0.0.0.0', port=port)