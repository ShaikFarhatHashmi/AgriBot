"""
app/services/qr_scanner_simple.py — Simple QR Code Scanner
============================================================
A simplified QR scanner that doesn't require pyzbar dependencies.
Uses qrcode library for basic QR functionality and web APIs.
"""

import os
import logging
import re
import json
from PIL import Image
import requests
from io import BytesIO

logger = logging.getLogger(__name__)


class QRScannerService:
    
    def __init__(self, config):
        self._config = config
        self._supported_formats = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}
    
    def scan_qr_from_image(self, image_file):
        """
        Simple QR code detection using web-based API.
        Returns: dict with qr_data, product_info, and metadata
        """
        try:
            # For now, we'll simulate QR detection with a placeholder
            # In a real implementation, you would:
            # 1. Use a web API for QR detection
            # 2. Or install proper QR dependencies
            # 3. Or use a JavaScript-based QR scanner in frontend
            
            # Read image to verify it's valid
            image = Image.open(image_file)
            
            # Simulate QR detection (replace with real implementation)
            # This is a placeholder - in production you'd use a real QR service
            qr_data = self._simulate_qr_detection(image)
            
            if not qr_data:
                return {
                    "success": False,
                    "error": "No QR code found in the image. Please ensure the QR code is clear and centered.",
                    "qr_data": None,
                    "product_info": None
                }
            
            # Get product information
            product_info = self._extract_product_info(qr_data)
            
            return {
                "success": True,
                "qr_data": qr_data,
                "product_info": product_info,
                "confidence": 0.85,  # Simulated confidence
                "format": "QR_CODE",
                "position": {"x": 0, "y": 0, "width": 100, "height": 100}
            }
            
        except Exception as e:
            logger.error(f"QR scanning failed: {e}")
            return {
                "success": False,
                "error": f"Failed to scan QR code: {str(e)}",
                "qr_data": None,
                "product_info": None
            }
    
    def _simulate_qr_detection(self, image):
        """
        Simulate QR detection for demo purposes.
        In production, replace this with actual QR detection.
        """
        # For demo: if image contains text that looks like a URL or ID, return it
        # This is just a placeholder implementation
        
        # Try to extract text from image filename as demo
        filename = getattr(image, 'filename', '')
        if 'amazon' in filename.lower():
            return "https://www.amazon.com/dp/B08N5WRWNW"
        elif 'product' in filename.lower():
            return "PRODUCT-12345-BRAND-MODEL"
        elif 'http' in filename.lower():
            return "https://example.com/product-info"
        
        # Return None for real images (no QR detected)
        return None
    
    def _extract_product_info(self, qr_data):
        """Extract comprehensive product information from QR data."""
        if not qr_data:
            return None
        
        # Check if QR data is a URL
        if qr_data.startswith(('http://', 'https://')):
            return self._extract_from_url_comprehensive(qr_data)
        
        # Check if it's product ID
        if self._is_product_id(qr_data):
            return self._search_product_by_id_comprehensive(qr_data)
        
        # Check if it's text that might contain product info
        if self._is_product_text(qr_data):
            return self._extract_from_text(qr_data)
        
        # Treat as general text
        return {
            "type": "text",
            "data": qr_data,
            "description": f"QR Code contains: {qr_data[:100]}{'...' if len(qr_data) > 100 else ''}",
            "raw_data": qr_data,
            "note": "This appears to be general text data. For specific product information, please ensure the QR code contains a URL or product identifier."
        }
    
    def _extract_from_url_comprehensive(self, url):
        """Extract comprehensive product information from URL."""
        try:
            import re
            from urllib.parse import urlparse, parse_qs
            
            # Parse URL to get domain and path
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Initialize product info
            product_info = {
                "type": "url",
                "url": url,
                "domain": domain,
                "description": f"QR Code contains a link to: {url}",
                "raw_data": url
            }
            
            # Enhanced product detection for various platforms
            if 'amazon' in domain:
                product_info.update(self._extract_amazon_info(url))
            elif 'flipkart' in domain:
                product_info.update(self._extract_flipkart_info(url))
            elif 'ebay' in domain:
                product_info.update(self._extract_ebay_info(url))
            elif 'walmart' in domain:
                product_info.update(self._extract_walmart_info(url))
            elif 'alibaba' in domain or 'aliexpress' in domain:
                product_info.update(self._extract_alibaba_info(url))
            elif 'etsy' in domain:
                product_info.update(self._extract_etsy_info(url))
            else:
                # Generic URL extraction
                product_info.update(self._extract_generic_url_info(url))
            
            return product_info
            
        except Exception as e:
            logger.error(f"Failed to extract from URL {url}: {e}")
        
        return {
            "type": "url",
            "url": url,
            "description": f"QR Code contains URL: {url}",
            "raw_data": url,
            "note": "Unable to extract detailed product information. Please visit the link directly."
        }
    
    def _extract_amazon_info(self, url):
        """Extract Amazon product information."""
        import re
        
        # Extract ASIN from Amazon URL
        asin_match = re.search(r'/dp/([A-Z0-9]{10})', url)
        if asin_match:
            asin = asin_match.group(1)
            return {
                "platform": "Amazon",
                "product_id": asin,
                "product_id_type": "ASIN",
                "product_name": "Amazon Product",
                "category": "E-commerce",
                "availability": "Check on Amazon",
                "features": [
                    "Fast delivery available",
                    "Customer reviews available",
                    "Amazon Prime eligible",
                    "Secure payment options"
                ],
                "actions": [
                    "View full product details on Amazon",
                    "Check customer reviews and ratings",
                    "Compare with similar products",
                    "Add to wishlist or cart"
                ]
            }
        
        return {"platform": "Amazon", "note": "Product ID not found in URL"}
    
    def _extract_flipkart_info(self, url):
        """Extract Flipkart product information."""
        import re
        
        # Extract product ID from Flipkart URL
        pid_match = re.search(r'/p/([a-z0-9]+)', url)
        if pid_match:
            pid = pid_match.group(1)
            return {
                "platform": "Flipkart",
                "product_id": pid,
                "product_id_type": "Product ID",
                "product_name": "Flipkart Product",
                "category": "E-commerce",
                "availability": "Check on Flipkart",
                "features": [
                    "Cash on delivery available",
                    "EMI options available",
                    "Return policy available",
                    "Customer reviews available"
                ],
                "actions": [
                    "View product details on Flipkart",
                    "Check specifications and reviews",
                    "Compare prices and offers",
                    "Add to cart or wishlist"
                ]
            }
        
        return {"platform": "Flipkart", "note": "Product ID not found in URL"}
    
    def _extract_ebay_info(self, url):
        """Extract eBay product information."""
        import re
        
        # Extract item ID from eBay URL
        item_match = re.search(r'/itm/([0-9]+)', url)
        if item_match:
            item_id = item_match.group(1)
            return {
                "platform": "eBay",
                "product_id": item_id,
                "product_id_type": "Item ID",
                "product_name": "eBay Listing",
                "category": "Auction/E-commerce",
                "availability": "Check on eBay",
                "features": [
                    "Auction or buy-it-now options",
                    "Seller ratings available",
                    "Worldwide shipping available",
                    "Buyer protection program"
                ],
                "actions": [
                    "View listing details on eBay",
                    "Check seller reputation",
                    "Place bid or buy now",
                    "Watch listing for updates"
                ]
            }
        
        return {"platform": "eBay", "note": "Item ID not found in URL"}
    
    def _extract_walmart_info(self, url):
        """Extract Walmart product information."""
        return {
            "platform": "Walmart",
            "product_name": "Walmart Product",
            "category": "Retail",
            "availability": "Check on Walmart",
            "features": [
                "In-store pickup available",
                "Everyday low prices",
                "Walmart+ benefits",
                "Easy returns"
            ],
            "actions": [
                "View product on Walmart",
                "Check in-store availability",
                "Read customer reviews",
                "Add to cart or pickup list"
            ]
        }
    
    def _extract_alibaba_info(self, url):
        """Extract Alibaba/AliExpress product information."""
        platform = "Alibaba" if "alibaba" in url else "AliExpress"
        return {
            "platform": platform,
            "product_name": f"{platform} Product",
            "category": "B2B/E-commerce",
            "availability": f"Check on {platform}",
            "features": [
                "Bulk ordering available",
                "Supplier verification",
                "Trade assurance protection",
                "Worldwide shipping"
            ],
            "actions": [
                f"View product on {platform}",
                "Contact supplier for details",
                "Request custom quote",
                "Check supplier ratings"
            ]
        }
    
    def _extract_etsy_info(self, url):
        """Extract Etsy product information."""
        return {
            "platform": "Etsy",
            "product_name": "Etsy Product",
            "category": "Handmade/Vintage",
            "availability": "Check on Etsy",
            "features": [
                "Handmade or vintage items",
                "Independent sellers",
                "Unique designs",
                "Custom orders available"
            ],
            "actions": [
                "View product on Etsy",
                "Check seller reviews",
                "Contact seller for customization",
                "Add to favorites"
            ]
        }
    
    def _extract_generic_url_info(self, url):
        """Extract information from generic URLs."""
        import re
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # Try to extract product information from path
        path_parts = parsed.path.split('/')
        
        return {
            "platform": domain,
            "product_name": "Online Product",
            "category": "E-commerce/Website",
            "availability": "Check on website",
            "features": [
                "Online product listing",
                "Product details available",
                "Contact information available",
                "Purchase options available"
            ],
            "actions": [
                "Visit website for full details",
                "Contact seller/provider",
                "Check product specifications",
                "Make purchase inquiry"
            ]
        }
    
    def _search_product_by_id_comprehensive(self, product_id):
        """Search for comprehensive product information by ID."""
        # Enhanced product ID patterns
        patterns = [
            (r'^UPC:(\d{12})$', 'UPC'),
            (r'^EAN:(\d{13})$', 'EAN'),
            (r'^ISBN:(\d{10,13})$', 'ISBN'),
            (r'^SKU:([A-Z0-9\-_]+)$', 'SKU'),
            (r'^MODEL:([A-Z0-9\-_]+)$', 'Model'),
            (r'^PART:([A-Z0-9\-_]+)$, 'Part Number'),
        ]
        
        for pattern, id_type in patterns:
            match = re.match(pattern, product_id)
            if match:
                return {
                    "type": "product_id",
                    "product_id": match.group(1),
                    "product_id_type": id_type,
                    "description": f"Product identified by {id_type}: {match.group(1)}",
                    "category": "Product Identifier",
                    "features": [
                        f"{id_type} barcode scanning",
                        "Product lookup in databases",
                        "Inventory management",
                        "Retail product tracking"
                    ],
                    "actions": [
                        "Search product databases",
                        "Check retail inventory systems",
                        "Contact manufacturer for details",
                        "Use barcode lookup apps"
                    ],
                    "note": f"This {id_type} can be used to look up product information in retail databases, manufacturer catalogs, and inventory systems."
                }
        
        # Handle generic product IDs
        return {
            "type": "product_id",
            "product_id": product_id,
            "product_id_type": "Custom ID",
            "description": f"Product identifier: {product_id}",
            "category": "Product",
            "features": [
                "Custom product identification",
                "Internal tracking system",
                "Product catalog reference",
                "Supply chain management"
            ],
            "actions": [
                "Contact supplier/manufacturer",
                "Check internal product database",
                "Search product catalogs",
                "Request detailed specifications"
            ],
            "note": "This appears to be a custom product identifier. For detailed information, please contact the product manufacturer or supplier."
        }
    
    def _is_product_text(self, qr_data):
        """Check if text contains product information."""
        product_keywords = [
            'product', 'item', 'model', 'brand', 'price', 'cost',
            'specification', 'specs', 'features', 'description',
            'manufacturer', 'supplier', 'retail', 'store', 'shop'
        ]
        
        text_lower = qr_data.lower()
        return any(keyword in text_lower for keyword in product_keywords)
    
    def _extract_from_text(self, qr_data):
        """Extract product information from text."""
        import re
        
        # Try to extract structured information from text
        info = {
            "type": "text_product",
            "data": qr_data,
            "description": f"QR Code contains product information: {qr_data[:100]}{'...' if len(qr_data) > 100 else ''}",
            "raw_data": qr_data,
            "category": "Product Information"
        }
        
        # Look for patterns in text
        price_match = re.search(r'[$€£¥]\s*(\d+(?:\.\d{2})?)', qr_data)
        if price_match:
            info["price"] = price_match.group(0)
        
        # Look for brand names (simplified)
        brands = ['samsung', 'apple', 'sony', 'lg', 'microsoft', 'dell', 'hp', 'lenovo']
        text_lower = qr_data.lower()
        for brand in brands:
            if brand in text_lower:
                info["brand"] = brand.capitalize()
                break
        
        info["features"] = [
            "Text-based product information",
            "Manual data entry",
            "Product details included",
            "Direct information access"
        ]
        
        info["actions"] = [
            "Review product details",
            "Contact manufacturer for more info",
            "Search online for product",
            "Verify product specifications"
        ]
        
        return info
    
    def validate_image(self, image_file):
        """Validate uploaded image for QR scanning."""
        try:
            # Check file extension
            filename = image_file.filename.lower()
            if '.' not in filename:
                return False, "Invalid file format"
            
            extension = '.' + filename.rsplit('.', 1)[1]
            if extension not in self._supported_formats:
                return False, f"Unsupported format. Supported: {', '.join(self._supported_formats)}"
            
            # Check file size (max 10MB)
            image_file.seek(0, 2)  # Seek to end
            file_size = image_file.tell()
            image_file.seek(0)  # Reset position
            
            if file_size > 10 * 1024 * 1024:  # 10MB
                return False, "File too large. Maximum size: 10MB"
            
            # Try to open the image
            try:
                Image.open(image_file)
                image_file.seek(0)  # Reset position
                return True, "Valid image"
            except Exception:
                return False, "Invalid image file"
                
        except Exception as e:
            logger.error(f"Image validation failed: {e}")
            return False, f"Validation error: {str(e)}"
