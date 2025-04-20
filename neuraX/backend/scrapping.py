from bs4 import BeautifulSoup
import requests
import re
import random
from urllib.parse import urlparse
from IPython.display import display, Image, HTML
from fake_useragent import UserAgent

# Enhanced mock data
MOCK_PRODUCTS = {
    "women_saree": {
        "url": "https://www.amazon.in/dp/B0B5XYZ123",
        "image_url": "https://m.media-amazon.com/images/I/71vJ1a+UPOL._SL1500_.jpg",
        "gender": "Women",
        "sizes": ["S", "M", "L"]
    },
    "men_shirt": {
        "url": "https://www.amazon.in/dp/B0D7C58QLS",
        "image_url": "https://m.media-amazon.com/images/I/71vJ1a+UPOL._SL1500_.jpg",
        "gender": "Men",
        "sizes": ["M", "L", "XL"]
    }
}

def clean_amazon_url(url):
    """Extract clean product URL from any Amazon link"""
    try:
        parsed = urlparse(url)
        path_parts = parsed.path.split('/')
        if 'dp' in path_parts or 'dn' in path_parts:
            product_id = path_parts[path_parts.index('dp')+1] if 'dp' in path_parts else path_parts[path_parts.index('dn')+1]
            return f"https://www.amazon.in/dp/{product_id}"
        return url.split('?')[0]
    except:
        return url.split('?')[0]

def extract_image_url(soup):
    """Extract product image URL from BeautifulSoup object"""
    # Try multiple selectors for product image
    img_selectors = [
        '#landingImage',
        '#imgBlkFront',
        '.a-dynamic-image',
        '#main-image-container img',
        '#imageBlock img'
    ]
    
    for selector in img_selectors:
        img = soup.select_one(selector)
        if img:
            image_url = img.get('src') or img.get('data-old-hires') or img.get('data-a-dynamic-image')
            if image_url:
                if isinstance(image_url, dict):  # Handle data-a-dynamic-image case
                    image_url = next(iter(image_url.keys()))
                return image_url.split('?')[0]  # Remove any query parameters
    
    return None

def extract_sizes_advanced(soup):
    """Comprehensive size extraction with multiple fallbacks"""
    sizes = []

    # Method 1: Standard dropdown
    size_select = soup.find("select", id="native_dropdown_selected_size_name")
    if size_select:
        sizes = [opt.text.strip() for opt in size_select.find_all("option") if opt.get('value') != '-1'][1:]

    # Method 2: Button-style sizes
    if not sizes:
        size_buttons = soup.select('#variation_size_name li button, #variation_size_name li span')
        if size_buttons:
            sizes = [btn.text.strip() for btn in size_buttons]

    # Method 3: Size chart table
    if not sizes:
        size_table = soup.find("table", id="sizeChart")
        if size_table:
            for row in size_table.find_all("tr")[1:]:  # Skip header row
                cells = row.find_all("td")
                if cells and cells[0].text.strip():
                    size = cells[0].text.strip()
                    if "see all" not in size.lower():
                        sizes.append(size)

    # Method 4: Inline size mentions (e.g., "Size: XL")
    if not sizes:
        size_spans = soup.find_all(string=re.compile(r'Size[:]?', re.IGNORECASE))
        for span in size_spans:
            parent = span.parent
            for sibling in parent.next_siblings:
                if hasattr(sibling, 'text'):
                    text = sibling.text.strip()
                    if text and len(text) < 10:  # Simple size validation
                        sizes.append(text)

    # Method 5: JSON-LD data
    if not sizes:
        json_data = soup.find('script', type='application/ld+json')
        if json_data:
            try:
                product_info = json.loads(json_data.string)
                if isinstance(product_info, list):
                    product_info = product_info[0]
                if 'offers' in product_info:
                    offers = product_info['offers']
                    if isinstance(offers, list):
                        for offer in offers:
                            if 'name' in offer:
                                sizes.append(offer['name'])
            except:
                pass

    # Clean results
    sizes = [re.sub(r'[\n\t]', '', size) for size in sizes if size.strip()]
    sizes = [size for size in sizes if not any(x in size.lower() for x in ['see all', 'select', 'size'])]
    return list(set(sizes))  # Remove duplicates

def detect_gender(soup):
    """Detect product gender from page content"""
    gender = "Unisex"
    title = soup.find("span", id="productTitle")
    title_text = title.text.lower() if title else ""

    # Check category breadcrumbs
    breadcrumbs = soup.find("div", id="wayfinding-breadcrumbs_container")
    breadcrumb_text = breadcrumbs.text.lower() if breadcrumbs else ""

    # Combine text for gender detection
    full_text = f"{title_text} {breadcrumb_text}".lower()

    gender_keywords = {
        "Women": ["women", "woman", "ladies", "female", "girl", "saree", "lehenga"],
        "Men": ["men", "man", "gentleman", "male", "boy", "shirt"],
        "Kids": ["kids", "children", "child", "toddler"]
    }

    for gen, keywords in gender_keywords.items():
        if any(keyword in full_text for keyword in keywords):
            gender = gen
            break

    return gender

def get_product_data(url):
    try:
        # Generate random user agent
        ua = UserAgent()
        headers = {
            "User-Agent": ua.random,
            "Accept-Language": "en-US,en;q=0.9"
        }

        clean_url = clean_amazon_url(url)
        response = requests.get(clean_url, headers=headers, timeout=10)

        # Check if request was successful
        if response.status_code != 200:
            return {"success": False, "error": f"HTTP {response.status_code}"}

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract image URL separately
        image_url = extract_image_url(soup)
        
        # Gender detection
        gender = detect_gender(soup)

        # Size extraction
        sizes = extract_sizes_advanced(soup)

        return {
            "image_url": image_url,
            "gender": gender,
            "sizes": sizes,
            "product_url": clean_url,
            "success": True
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

def show_results(data, original_url):
    print("\n✅ Extracted Product Data")
    print("-----------------------------------")
    print(f"🔗 Clean Product URL: {data.get('product_url', original_url)}")
    print(f"👗 Detected Gender: {data['gender']}")
    print(f"📏 Available Sizes: {', '.join(data['sizes']) if data['sizes'] else 'Not found (try manual inspection)'}")
    
    # Display image separately with its URL
    if data.get("image_url"):
        print("\n🖼️ Product Image URL:")
        print(data["image_url"])
        print("\nImage Preview:")
        display(Image(url=data["image_url"], width=300))
    else:
        print("\n❌ No product image found")

    if not data.get("sizes"):
        print("\n💡 Debugging Tips:")
        print("- Check if sizes load with JavaScript (try opening in browser)")
        print("- Try a different product URL")
        print("- Some products may only have one size")

def amazon_extractor():
    print("🛍️ Amazon Virtual Try-On Data Extractor")
    print("-----------------------------------")
    url = input("Paste Amazon product URL: ").strip()

    print("\n⏳ Extracting product data...")
    data = get_product_data(url)

    if not data["success"]:
        print(f"⚠️ Error: {data.get('error', 'Unknown error')}")
        print("Using mock data instead...")
        data = random.choice(list(MOCK_PRODUCTS.values()))

    show_results(data, url)
    print("\n✨ Ready for virtual try-on processing!")

# Execute the function
amazon_extractor()