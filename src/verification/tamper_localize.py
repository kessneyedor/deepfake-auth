import cv2
import numpy as np
import base64

# Perceptual frequency weight matrix for 8x8 DCT blocks.
# Low-frequency coefficients (top-left) carry the most image content,
# so deviations there matter more than high-frequency noise.
_FREQ_WEIGHTS = np.array(
    [[1.0 / (1 + i + j) for j in range(8)] for i in range(8)],
    dtype=np.float32
)

def _dct_block_score(block_a, block_b):
    """Weighted DCT coefficient difference between two 8x8 luminance blocks."""
    dct_a = cv2.dct(block_a)
    dct_b = cv2.dct(block_b)
    return float(np.mean(np.abs(dct_a - dct_b) * _FREQ_WEIGHTS))

def localize_tampering(original_path, suspect_path, block_size=8):
    original = cv2.imread(original_path)
    suspect  = cv2.imread(suspect_path)

    if original is None or suspect is None:
        return None

    if original.shape != suspect.shape:
        suspect = cv2.resize(suspect, (original.shape[1], original.shape[0]))

    # Work on the luminance (Y) channel — matches JPEG compression model
    # and human perceptual sensitivity to changes
    orig_y = cv2.cvtColor(original, cv2.COLOR_BGR2YCrCb)[:, :, 0].astype(np.float32)
    susp_y = cv2.cvtColor(suspect,  cv2.COLOR_BGR2YCrCb)[:, :, 0].astype(np.float32)

    h, w = orig_y.shape
    heatmap = np.zeros((h, w), dtype=np.float32)

    # Block-by-block DCT comparison — the core tamper localization loop
    for r in range(0, h - block_size + 1, block_size):
        for c in range(0, w - block_size + 1, block_size):
            ob = orig_y[r:r+block_size, c:c+block_size]
            sb = susp_y[r:r+block_size, c:c+block_size]
            if ob.shape == (block_size, block_size):
                heatmap[r:r+block_size, c:c+block_size] = _dct_block_score(ob, sb)

    # Adaptive threshold: mean + 2*std separates genuine tampering from
    # minor compression / re-encoding noise
    threshold = float(np.mean(heatmap) + 2.0 * np.std(heatmap))
    tamper_mask_full = (heatmap > threshold).astype(np.uint8)

    # Count tampered 8x8 blocks
    total_blocks    = int((h // block_size) * (w // block_size))
    tampered_blocks = int(np.sum(tamper_mask_full[::block_size, ::block_size]))
    tampered_ratio  = round(tampered_blocks / max(total_blocks, 1) * 100, 1)

    # INFERNO colormap: black -> deep red -> orange -> yellow -> white
    # Red/yellow = high deviation (tampered), black = clean
    heatmap_norm  = cv2.normalize(heatmap, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    heatmap_color = cv2.applyColorMap(heatmap_norm, cv2.COLORMAP_INFERNO)

    # Overlay: suspect image blended with the heatmap
    overlay = cv2.addWeighted(suspect, 0.55, heatmap_color, 0.45, 0)

    # Binary mask view: tampered blocks highlighted in red over darkened image
    mask_vis = np.zeros_like(suspect)
    mask_vis[:, :, 2] = (tamper_mask_full * 220).astype(np.uint8)
    mask_overlay = cv2.addWeighted(suspect, 0.35, mask_vis, 0.65, 0)

    def to_b64(img):
        _, buf = cv2.imencode('.png', img)
        return base64.b64encode(buf).decode('utf-8')

    return {
        'overlay_b64':     to_b64(overlay),
        'heatmap_b64':     to_b64(heatmap_color),
        'mask_b64':        to_b64(mask_overlay),
        'tampered_ratio':  tampered_ratio,
        'tampered_blocks': tampered_blocks,
        'total_blocks':    total_blocks,
        'max_deviation':   round(float(np.max(heatmap)), 2),
        'mean_deviation':  round(float(np.mean(heatmap)), 2),
        'threshold':       round(threshold, 2),
    }
