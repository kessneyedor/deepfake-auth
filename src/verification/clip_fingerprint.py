import torch
import clip
from PIL import Image
import numpy as np
import os

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

def extract_fingerprint(image_path):
    image = preprocess(Image.open(image_path)).unsqueeze(0).to(device)
    with torch.no_grad():
        features = model.encode_image(image)
        features = features / features.norm(dim=-1, keepdim=True)
    return features.cpu().numpy().flatten()

def compare_fingerprints(fp1, fp2):
    similarity = float(np.dot(fp1, fp2))
    return round(similarity, 4)
