import cv2
import numpy as np

def decode(watermarked_img, n_bits):
    h, w = watermarked_img.shape[:2]
    recovered = []
    for r in range(0, h - 8, 8):
        for c in range(0, w - 8, 8):
            if len(recovered) >= n_bits:
                break
            block = watermarked_img[r:r+8, c:c+8, 0].astype(np.float32)
            dct = cv2.dct(block)
            recovered.append(1 if dct[4, 4] > 0 else 0)
    return recovered[:n_bits]

def ber(original, recovered):
    errors = sum(a != b for a, b in zip(original, recovered))
    return errors / len(original)
