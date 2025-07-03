import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Target website
base_url = "https://templates.g5plus.net/glowing-bootstrap-5/home-03.html"

# Set to store all image URLs
image_urls = set()

# Helper: Save image to local disk
def download_image(img_url):
    parsed = urlparse(img_url)
    path = parsed.path.lstrip('/')
    folder = os.path.dirname(path)
    os.makedirs(folder, exist_ok=True)
    try:
        img_data = requests.get(img_url, timeout=10).content
        with open(path, 'wb') as f:
            f.write(img_data)
        print(f"✅ Downloaded: {path}")
    except Exception as e:
        print(f"❌ Failed: {img_url} -> {e}")

# Step 1: Load HTML content
print(f"🔍 Fetching HTML from: {base_url}")
try:
    resp = requests.get(base_url)
    soup = BeautifulSoup(resp.text, "html.parser")
except Exception as e:
    print(f"❌ Failed to fetch main page: {e}")
    exit()

# Step 2: Extract <img> tags and lazy-loaded images
for img in soup.find_all("img"):
    attributes = ['src', 'data-src', 'data-original', 'data-lazy', 'data-srcset']
    for attr in attributes:
        value = img.get(attr)
        if value:
            full_url = urljoin(base_url, value)
            image_urls.add(full_url)

# Step 3: Extract <source srcset=""> from <picture> or <video>
for source in soup.find_all("source"):
    srcset = source.get("srcset")
    if srcset:
        for item in srcset.split(','):
            url = item.strip().split(' ')[0]
            full_url = urljoin(base_url, url)
            image_urls.add(full_url)

# Step 4: Extract inline style="background-image: url(...)"
for tag in soup.find_all(style=True):
    styles = tag["style"]
    matches = re.findall(r'url\([\'"]?(.*?)[\'"]?\)', styles)
    for match in matches:
        full_url = urljoin(base_url, match)
        image_urls.add(full_url)

# Step 5: Extract CSS files and look for background images
css_links = [
    urljoin(base_url, link.get("href"))
    for link in soup.find_all("link", rel="stylesheet")
    if link.get("href")
]

for css_url in css_links:
    try:
        css_resp = requests.get(css_url)
        # Match URLs with images (jpg, png, webp, svg, gif)
        css_image_paths = re.findall(r'url\([\'"]?(.*?\.(?:png|jpe?g|webp|svg|gif))(?:\?.*?)?[\'"]?\)', css_resp.text)
        for img_path in css_image_paths:
            full_url = urljoin(css_url, img_path)
            image_urls.add(full_url)
    except Exception as e:
        print(f"❌ Failed to fetch CSS: {css_url} -> {e}")

# Step 6: Download all collected images
print(f"\n📸 Found {len(image_urls)} images. Starting download...\n")
for img_url in image_urls:
    download_image(img_url)
