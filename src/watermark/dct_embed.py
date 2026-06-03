import cv2
import numpy as np
from skimage.metrics import peak_signal_noise_ratio as psnr
import os

def embed(image_path, payload_bits, alpha=100):
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f'Could not read image: {image_path}')
    watermarked = img.copy().astype(np.float32)
    h, w = img.shape[:2]
    bit_idx = 0
    for r in range(0, h - 8, 8):
        for c in range(0, w - 8, 8):
            if bit_idx >= len(payload_bits):
                break
            block = watermarked[r:r+8, c:c+8, 0]
            dct = cv2.dct(block)
            if payload_bits[bit_idx] == 1:
                dct[4, 4] = abs(dct[4, 4]) + alpha
            else:
                dct[4, 4] = -(abs(dct[4, 4]) + alpha)
            watermarked[r:r+8, c:c+8, 0] = cv2.idct(dct)
            bit_idx += 1
    return np.clip(watermarked, 0, 255).astype(np.uint8)

def compute_psnr(original_path, watermarked):
    original = cv2.imread(original_path)
    return psnr(original, watermarked)
