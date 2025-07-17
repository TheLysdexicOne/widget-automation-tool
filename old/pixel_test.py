import imagehash
from PIL import Image
from pathlib import Path

# Config
folder = Path("assets/backgrounds")
output_file = folder / "pixel_test.txt"
threshold = 8  # pHash Hamming distance threshold

# Step 1: Compute pHashes
results = []
for file in sorted(folder.glob("*.png")):
    img = Image.open(file).convert("RGB")
    ph = imagehash.phash(img)
    results.append((ph, file.name))

# Step 2: Write pHashes
with open(output_file, "w", encoding="utf-8") as f:
    for phash, name in results:
        f.write(f"{phash}: {name}\n")

# Step 3: Compare and find similar pairs
similar = []
for i, (hash1, name1) in enumerate(results):
    for j in range(i + 1, len(results)):
        hash2, name2 = results[j]
        dist = hash1 - hash2
        if dist <= threshold:
            similar.append((name1, name2, dist))

# Step 4: Append results
if similar:
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\nSimilar Screens (Hamming distance ≤ {}):\n".format(threshold))
        for n1, n2, d in similar:
            f.write(f"{n1} ≈ {n2} (distance {d})\n")
