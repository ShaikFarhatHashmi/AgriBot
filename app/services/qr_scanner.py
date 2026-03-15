"""
app/services/qr_scanner.py — QR Code Scanner Service
=========================================================
LAYER  : Service
PURPOSE: Handle QR code scanning and data extraction
"""

import logging
import base64
import io
import cv2
import numpy as np
from PIL import Image
from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, Optional, List, Tuple

try:
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    logging.warning("OpenCV not available, using fallback QR detection")

# Note: pyzbar requires ZBar library which is not available on Windows by default
# We'll use OpenCV for QR code detection which is more reliable for cross-platform support

logger = logging.getLogger(__name__)

class QRScannerService:
    """Service for scanning and processing QR codes"""
    
    def __init__(self, config=None):
        self._config = config
        self.supported_formats = [
            'url', 'text', 'email', 'phone', 'wifi', 'sms', 
            'vcard', 'location', 'product', 'certificate'
        ]
        
        # Agricultural product patterns
        self.product_patterns = {
            'fertilizer': r'(fertilizer|urea|dap|npk|compost|manure)',
            'pesticide': r'(pesticide|insecticide|herbicide|fungicide)',
            'seed': r'(seed|variety|hybrid|germination)',
            'equipment': r'(tractor|plow|harvester|irrigation|pump)',
            'crop': r'(wheat|rice|cotton|sugarcane|maize|pulses|vegetables)'
        }
        
        # Initialize web scraping session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scan_qr_from_image(self, image_file):
        """Scan QR code from uploaded image file - compatibility method"""
        try:
            # Convert image file to base64 for processing
            image_bytes = image_file.read()
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # Use the comprehensive scan method
            result = self.scan_qr_data(image_base64, is_image_data=True)
            
            if result['status'] == 'error':
                return {
                    "success": False,
                    "error": result['error'],
                    "qr_data": None,
                    "product_info": None
                }
            
            # Convert to expected format
            return {
                "success": True,
                "qr_data": result['raw_data'],
                "product_info": result['extracted_info'],
                "confidence": result['confidence'],
                "format": "QR_CODE",
                "universal_query": result.get('universal_query', ''),
                "agricultural_context": result.get('agricultural_context'),
                "is_agricultural": result.get('is_agricultural', False)
            }
            
        except Exception as e:
            logger.error(f"QR scan failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "qr_data": None,
                "product_info": None
            }
    
    def scan_qr_data(self, qr_data: str, is_image_data: bool = False) -> Dict:
        """Scan and process QR code data from text or image"""
        try:
            logger.info(f"📱 Scanning QR data: {qr_data[:50]}...")
            logger.info(f"📱 Is image data: {is_image_data}, Data length: {len(qr_data)}")
            
            # If it's image data, decode the QR code from image
            if is_image_data:
                logger.info("📱 Processing image data for QR detection...")
                qr_data = self._decode_qr_from_image(qr_data)
                if not qr_data:
                    logger.error("❌ No QR code found in image")
                    return {
                        'status': 'error',
                        'error': 'No QR code found in image',
                        'message': 'Could not detect a QR code in the uploaded image.'
                    }
                logger.info(f"✅ QR decoded from image: {qr_data[:100]}...")
            else:
                logger.info(f"📱 Processing text data: {qr_data[:100]}...")
            
            # Detect QR code type
            qr_type = self._detect_qr_type(qr_data)
            logger.info(f"📱 Detected QR type: {qr_type}")
            
            # Extract information based on type
            extracted_info = self._extract_qr_info(qr_data, qr_type)
            logger.info(f"📱 Extracted info: {extracted_info}")
            
            # If it's a URL, fetch content from the URL
            url_content = ""
            if qr_type == 'url' and extracted_info.get('url'):
                try:
                    logger.info(f"🌐 Fetching URL content for: {extracted_info['url']}")
                    url_content = self._fetch_url_content(extracted_info['url'])
                    logger.info(f"✅ Fetched URL content: {len(url_content)} chars")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to fetch URL content: {e}")
            
            # Add agricultural context if applicable
            try:
                agri_context = self._add_agricultural_context(extracted_info)
            except Exception as e:
                logger.warning(f"⚠️ Agricultural context detection failed: {e}")
                agri_context = None
            
            result = {
                'status': 'success',
                'type': qr_type,
                'raw_data': qr_data,
                'extracted_info': extracted_info,
                'url_content': url_content,
                'agricultural_context': agri_context,
                'is_agricultural': bool(agri_context),
                'confidence': self._calculate_confidence(qr_data, extracted_info),
                'scan_method': 'image_upload' if is_image_data else 'text_input'
            }
            
            # Generate universal query for AI processing
            try:
                logger.info(f"🌾 Starting universal query generation for type: {qr_type}")
                logger.info(f"🌾 URL content length: {len(url_content)}")
                logger.info(f"🌾 Agricultural context: {agri_context}")
                
                universal_query = self.generate_agricultural_query(result)
                result['universal_query'] = universal_query
                logger.info(f"🌾 Generated universal query: {universal_query[:100]}...")
            except Exception as e:
                logger.error(f"❌ Failed to generate universal query: {e}")
                import traceback
                logger.error(f"❌ Traceback: {traceback.format_exc()}")
                result['universal_query'] = f"Analyze this QR code content: {qr_data[:200]}"
            
            logger.info(f"✅ QR Scan successful: {qr_type} | Confidence: {result['confidence']:.1%} | Method: {result['scan_method']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ QR Scan failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'raw_data': qr_data
            }
    
    def _decode_qr_from_image(self, image_data: str) -> Optional[str]:
        """Decode QR code from image data using OpenCV with preprocessing"""
        try:
            logger.info("📱 Starting QR image decoding process...")
            
            # Decode base64 image data
            if image_data.startswith('data:image'):
                # Remove data URL prefix
                image_data = image_data.split(',')[1]
                logger.info("📱 Removed data URL prefix")
            
            image_bytes = base64.b64decode(image_data)
            logger.info(f"📱 Decoded base64 image: {len(image_bytes)} bytes")
            
            image = Image.open(io.BytesIO(image_bytes))
            logger.info(f"📱 Opened image: {image.size}, mode: {image.mode}")
            
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
                logger.info("📱 Converted to grayscale")
            
            # Convert PIL image to OpenCV format
            image_array = np.array(image)
            logger.info(f"📱 Converted to numpy array: {image_array.shape}")
            
            # Apply image preprocessing for better QR detection
            processed_image = self._preprocess_image(image_array)
            logger.info("📱 Applied image preprocessing")
            
            # Use OpenCV for QR code detection
            if OPENCV_AVAILABLE:
                logger.info("📱 Using OpenCV for QR detection...")
                try:
                    # Try multiple detection methods
                    detector = cv2.QRCodeDetector()
                    
                    # Method 1: Direct detection on processed image
                    try:
                        logger.info("📱 Method 1: Direct detection on processed image")
                        data, points, _ = detector.detectAndDecode(processed_image)
                        if data:
                            logger.info(f"✅ QR decoded with preprocessing: {data[:50]}...")
                            return data
                        else:
                            logger.info("📱 Method 1: No QR code found")
                    except Exception as e:
                        logger.warning(f"Method 1 failed: {e}")
                    
                    # Method 2: Try with adaptive threshold
                    try:
                        logger.info("📱 Method 2: Adaptive threshold")
                        adaptive_img = cv2.adaptiveThreshold(
                            processed_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                            cv2.THRESH_BINARY, 11, 2
                        )
                        data, points, _ = detector.detectAndDecode(adaptive_img)
                        if data:
                            logger.info(f"✅ QR decoded with adaptive threshold: {data[:50]}...")
                            return data
                        else:
                            logger.info("📱 Method 2: No QR code found")
                    except Exception as e:
                        logger.warning(f"Method 2 failed: {e}")
                    
                    # Method 3: Try with original image as fallback
                    try:
                        logger.info("📱 Method 3: Original image")
                        data, points, _ = detector.detectAndDecode(image_array)
                        if data:
                            logger.info(f"✅ QR decoded with original image: {data[:50]}...")
                            return data
                        else:
                            logger.info("📱 Method 3: No QR code found")
                    except Exception as e:
                        logger.warning(f"Method 3 failed: {e}")

                    # Method 4: Rescale to multiple sizes (handles curved/real-world QR codes)
                    try:
                        logger.info("📱 Method 4: Multi-scale detection")
                        for scale in [1.5, 2.0, 0.75, 0.5]:
                            h, w = image_array.shape[:2]
                            resized = cv2.resize(
                                image_array,
                                (int(w * scale), int(h * scale)),
                                interpolation=cv2.INTER_CUBIC if scale > 1 else cv2.INTER_AREA
                            )
                            data, points, _ = detector.detectAndDecode(resized)
                            if data:
                                logger.info(f"✅ QR decoded at scale {scale}: {data[:50]}...")
                                return data
                        logger.info("📱 Method 4: No QR code found at any scale")
                    except Exception as e:
                        logger.warning(f"Method 4 failed: {e}")

                    # Method 5: Warp correction for curved surfaces
                    try:
                        logger.info("📱 Method 5: Warp correction")
                        h, w = image_array.shape[:2]
                        # Sharpen strongly before attempting warp
                        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
                        sharpened = cv2.filter2D(image_array, -1, kernel)
                        # Try detect+decode with WECHAT detector (better for distorted QR)
                        try:
                            wechat = cv2.wechat_qrcode_WeChatQRCode()
                            texts, _ = wechat.detectAndDecode(sharpened)
                            if texts and texts[0]:
                                logger.info(f"✅ QR decoded with WeChatQRCode: {texts[0][:50]}...")
                                return texts[0]
                        except Exception:
                            pass
                        # Fallback: denoise then retry standard detector
                        denoised = cv2.fastNlMeansDenoising(sharpened, h=10)
                        data, points, _ = detector.detectAndDecode(denoised)
                        if data:
                            logger.info(f"✅ QR decoded after denoising: {data[:50]}...")
                            return data
                        logger.info("📱 Method 5: No QR code found")
                    except Exception as e:
                        logger.warning(f"Method 5 failed: {e}")
                        
                except Exception as e:
                    logger.warning(f"OpenCV QR decoding failed: {e}")
            else:
                logger.warning("OpenCV not available for QR detection")
            
            logger.error("❌ All QR detection methods failed")
            return None
            
        except Exception as e:
            logger.error(f"❌ Image decoding failed: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return None
    
    def _preprocess_image(self, image_array: np.ndarray) -> np.ndarray:
        """Apply preprocessing techniques to improve QR code detection"""
        try:
            # Convert to grayscale if not already
            if len(image_array.shape) == 3:
                gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = image_array
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # Apply histogram equalization to improve contrast
            equalized = cv2.equalizeHist(blurred)
            
            # Apply bilateral filter for edge preservation
            bilateral = cv2.bilateralFilter(equalized, 9, 75, 75)
            
            # Apply sharpening kernel
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(bilateral, -1, kernel/9.0)
            
            # Apply Otsu's thresholding for better binarization
            try:
                ret, thresholded = cv2.threshold(
                    sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
                )
            except Exception as e:
                logger.warning(f"Threshold processing failed: {e}")
                # Fallback to simple threshold
                _, thresholded = cv2.threshold(sharpened, 127, 255, cv2.THRESH_BINARY)
            
            # Apply morphological operations to clean up
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            cleaned = cv2.morphologyEx(thresholded, cv2.MORPH_CLOSE, kernel)
            
            # Resize to standard size for better detection
            height, width = cleaned.shape
            if max(height, width) > 2000:
                scale = 2000 / max(height, width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                cleaned = cv2.resize(cleaned, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            return cleaned
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}")
            return image_array
    
    def _detect_qr_type(self, qr_data: str) -> str:
        """Detect the type of QR code data"""
        qr_data = qr_data.strip().lower()
        
        # URL pattern
        if qr_data.startswith(('http://', 'https://', 'www.')):
            return 'url'
        
        # Email pattern
        if re.match(r'^mailto:', qr_data) or '@' in qr_data and '.' in qr_data:
            return 'email'
        
        # Phone pattern
        if re.match(r'^tel:|\+?\d{10,}', qr_data):
            return 'phone'
        
        # WiFi pattern
        if qr_data.startswith('wifi:') or 'ssid:' in qr_data:
            return 'wifi'
        
        # SMS pattern
        if qr_data.startswith('sms:'):
            return 'sms'
        
        # vCard pattern
        if qr_data.startswith('begin:vcard') or 'fn:' in qr_data:
            return 'vcard'
        
        # Location pattern
        if qr_data.startswith('geo:') or 'latitude:' in qr_data:
            return 'location'
        
        # JSON data
        if qr_data.startswith('{') and qr_data.endswith('}'):
            return 'json'
        
        # Product code pattern
        if re.match(r'^[A-Z0-9]{8,20}$', qr_data):
            return 'product_code'
        
        # Certificate pattern
        if 'certificate' in qr_data or 'cert' in qr_data:
            return 'certificate'
        
        return 'text'
    
    def _extract_qr_info(self, qr_data: str, qr_type: str) -> Dict:
        """Extract information based on QR code type"""
        if qr_type == 'url':
            return self._extract_url_info(qr_data)
        elif qr_type == 'email':
            return self._extract_email_info(qr_data)
        elif qr_type == 'phone':
            return self._extract_phone_info(qr_data)
        elif qr_type == 'wifi':
            return self._extract_wifi_info(qr_data)
        elif qr_type == 'sms':
            return self._extract_sms_info(qr_data)
        elif qr_type == 'vcard':
            return self._extract_vcard_info(qr_data)
        elif qr_type == 'location':
            return self._extract_location_info(qr_data)
        elif qr_type == 'json':
            return self._extract_json_info(qr_data)
        elif qr_type == 'product_code':
            return self._extract_product_code_info(qr_data)
        else:
            return {'text': qr_data, 'type': 'plain_text'}
    
    def _extract_url_info(self, url: str) -> Dict:
        """Extract information from URL"""
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            
            return {
                'url': url,
                'domain': parsed.netloc,
                'path': parsed.path,
                'parameters': params,
                'is_agricultural': self._is_agricultural_url(url)
            }
        except:
            return {'url': url, 'domain': 'unknown'}
    
    def _extract_email_info(self, email_data: str) -> Dict:
        """Extract email information"""
        email = email_data.replace('mailto:', '').strip()
        return {'email': email, 'type': 'contact'}
    
    def _extract_phone_info(self, phone_data: str) -> Dict:
        """Extract phone information"""
        phone = phone_data.replace('tel:', '').strip()
        return {'phone': phone, 'type': 'contact'}
    
    def _extract_wifi_info(self, wifi_data: str) -> Dict:
        """Extract WiFi information"""
        info = {'type': 'network'}
        parts = wifi_data.split(';')
        for part in parts:
            if ':' in part:
                key, value = part.split(':', 1)
                info[key.lower()] = value
        return info
    
    def _extract_sms_info(self, sms_data: str) -> Dict:
        """Extract SMS information"""
        sms_data = sms_data.replace('sms:', '').strip()
        if '?' in sms_data:
            phone, message = sms_data.split('?', 1)
            return {'phone': phone, 'message': message, 'type': 'message'}
        return {'phone': sms_data, 'type': 'contact'}
    
    def _extract_vcard_info(self, vcard_data: str) -> Dict:
        """Extract vCard information"""
        info = {'type': 'contact_card'}
        lines = vcard_data.split('\n')
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                if key.lower() in ['fn', 'n', 'tel', 'email', 'org']:
                    info[key.lower()] = value
        return info
    
    def _extract_location_info(self, location_data: str) -> Dict:
        """Extract location information"""
        if location_data.startswith('geo:'):
            coords = location_data.replace('geo:', '').split(',')
            if len(coords) >= 2:
                return {
                    'latitude': coords[0],
                    'longitude': coords[1],
                    'type': 'coordinates'
                }
        return {'location': location_data, 'type': 'location'}
    
    def _extract_json_info(self, json_data: str) -> Dict:
        """Extract JSON information"""
        try:
            import json
            data = json.loads(json_data)
            return {'data': data, 'type': 'structured_data'}
        except:
            return {'raw_json': json_data, 'type': 'invalid_json'}
    
    def _extract_product_code_info(self, code: str) -> Dict:
        """Extract product code information"""
        return {
            'product_code': code,
            'type': 'product_identifier',
            'format': 'alphanumeric'
        }
    
    def _is_agricultural_url(self, url: str) -> bool:
        """Check if URL is agricultural related"""
        agri_keywords = [
            'agriculture', 'farm', 'crop', 'seed', 'fertilizer', 
            'pesticide', 'irrigation', 'harvest', 'soil', 'weather'
        ]
        url_lower = url.lower()
        return any(keyword in url_lower for keyword in agri_keywords)
    
    def _add_agricultural_context(self, extracted_info: Dict) -> Optional[Dict]:
        """Add agricultural context to extracted information - Universal approach"""
        context = None
        
        try:
            # Check for agricultural keywords in text data
            text_data = str(extracted_info).lower()
            
            # Enhanced agricultural patterns
            agri_patterns = {
                'fertilizer': r'(fertilizer|urea|dap|npk|compost|manure|nutrient)',
                'pesticide': r'(pesticide|insecticide|herbicide|fungicide|chemical)',
                'seed': r'(seed|variety|hybrid|germination|sowing|planting)',
                'equipment': r'(tractor|plow|harvester|irrigation|pump|machine)',
                'crop': r'(wheat|rice|cotton|sugarcane|maize|pulses|vegetables)',
                'soil': r'(soil|earth|land|ground|clay|loam|sand)',
                'water': r'(water|irrigation|rainfall|drought|moisture)',
                'disease': r'(disease|pest|insect|fungus|virus|blight)',
                'harvest': r'(harvest|yield|production|crop|reaping)'
            }
            
            for category, pattern in agri_patterns.items():
                matches = re.findall(pattern, text_data)
                if matches:
                    if context is None:
                        context = {
                            'category': category,
                            'keywords': list(set(matches)),  # Remove duplicates
                            'confidence': len(matches) * 0.1
                        }
                    else:
                        # Multiple categories found
                        context['keywords'].extend(matches)
                        context['keywords'] = list(set(context['keywords']))  # Remove duplicates
                        context['confidence'] = min(context['confidence'] + 0.05, 0.5)
            
            return context
            
        except Exception as e:
            logger.warning(f"⚠️ Error adding agricultural context: {e}")
            return None
    
    def _calculate_confidence(self, qr_data: str, extracted_info: Dict) -> float:
        """Calculate confidence score for QR scan"""
        confidence = 0.4  # Base confidence
        
        # Data quality checks
        if len(qr_data.strip()) > 10:
            confidence += 0.1  # Reasonable length
        
        if len(qr_data.strip()) > 50:
            confidence += 0.1  # Substantial content
        
        # Boost for structured data types
        if extracted_info.get('type') in ['url', 'email', 'phone', 'json']:
            confidence += 0.2
        elif extracted_info.get('type') in ['wifi', 'sms', 'vcard']:
            confidence += 0.15
        elif extracted_info.get('type') == 'product_code':
            confidence += 0.25
        elif extracted_info.get('type') == 'certificate':
            confidence += 0.3
        
        # Boost for agricultural content
        try:
            agri_context = self._add_agricultural_context(extracted_info)
            if agri_context:
                confidence += 0.2
        except Exception as e:
            logger.warning(f"⚠️ Agricultural context in confidence calculation failed: {e}")
        
        # Quality indicators
        if extracted_info.get('type') == 'url' and '.' in extracted_info.get('url', ''):
            confidence += 0.1  # Valid URL format
        
        if extracted_info.get('type') == 'email' and '@' in extracted_info.get('email', ''):
            confidence += 0.1  # Valid email format
        
        if extracted_info.get('type') == 'phone' and extracted_info.get('phone', '').replace('-', '').replace(' ', '').isdigit():
            confidence += 0.1  # Valid phone format
        
        # Penalty for very short or empty data
        if len(qr_data.strip()) < 5:
            confidence -= 0.2
        
        # Penalty for suspicious patterns
        if 'test' in qr_data.lower() or 'example' in qr_data.lower():
            confidence -= 0.1
        
        return min(max(confidence, 0.1), 1.0)
    
    def generate_agricultural_query(self, scan_result: Dict) -> str:
        """Generate universal query based on QR scan result - handles both agricultural and non-agricultural content"""
        qr_type = scan_result.get('type', 'text')
        info = scan_result.get('extracted_info', {})
        raw_data = scan_result.get('raw_data', '')
        url_content = scan_result.get('url_content', '')
        agri_context = scan_result.get('agricultural_context', {})
        
        logger.info(f"🌾 Generating universal query for QR type: {qr_type}")
        
        # Priority 1: If we have agricultural context, create specific agricultural query
        if agri_context:
            return self._generate_agricultural_query(agri_context, info, language='en')
        
        # Priority 2: If it's a URL with content, analyze for relevance
        if url_content:
            return self._generate_url_query(url_content, info, raw_data)
        
        # Priority 3: For text QR codes, check for agricultural relevance
        if qr_type == 'text':
            return self._generate_text_query(raw_data, info)
        
        # Priority 4: For other QR types, provide appropriate analysis
        return self._generate_type_specific_query(qr_type, info, raw_data)
    
    def _generate_agricultural_query(self, agri_context: Dict, info: Dict, language: str) -> str:
        """Generate specific agricultural query"""
        category = agri_context.get('category', 'general')
        keywords = agri_context.get('keywords', [])
        
        if category == 'fertilizer':
            query = f"Provide detailed agricultural guidance about fertilizer products"
            if keywords:
                query += f" specifically: {', '.join(keywords[:3])}"
            query += ". Include application methods, dosage per acre, timing for different crops, safety precautions, and best practices for Indian farming conditions."
        
        elif category == 'pesticide':
            query = f"Provide comprehensive pest management guidance for pesticide products"
            if keywords:
                query += f" specifically: {', '.join(keywords[:3])}"
            query += ". Include target pests, application methods, safety precautions, waiting period before harvest, and integrated pest management practices."
        
        elif category == 'seed':
            query = f"Provide detailed cultivation guidance for seed products"
            if keywords:
                query += f" specifically: {', '.join(keywords[:3])}"
            query += ". Include sowing time, seed treatment, spacing, irrigation requirements, fertilizer schedule, and yield optimization tips for Indian conditions."
        
        elif category == 'equipment':
            query = f"Provide operational guidance for agricultural equipment"
            if keywords:
                query += f" specifically: {', '.join(keywords[:3])}"
            query += ". Include maintenance schedule, safety procedures, fuel efficiency tips, and best practices for Indian farming conditions."
        
        else:
            query = f"Provide comprehensive agricultural guidance"
            if keywords:
                query += f" about: {', '.join(keywords[:3])}"
            query += ". Explain its uses, benefits, application methods, and best practices for Indian farmers."
        
        return query
    
    def _generate_url_query(self, url_content: str, info: Dict, raw_data: str) -> str:
        """Generate query for URL content"""
        url = info.get('url', '')
        
        # Check if URL content contains agricultural information
        agri_keywords = ['farm', 'crop', 'seed', 'fertilizer', 'pesticide', 'agriculture', 'soil', 'water', 'harvest']
        if any(keyword in url_content.lower() for keyword in agri_keywords):
            query = f"Analyze this agricultural website content and provide comprehensive guidance: {url_content[:500]}"
            query += ". Explain key points, practical applications for Indian farming, and specific recommendations for farmers."
        else:
            query = f"Analyze this website content and provide relevant information: {url_content[:300]}"
            query += ". Explain what this website is about, its purpose, and how it might be useful. If not agricultural, explain its general purpose and potential applications."
        
        return query
    
    def _generate_text_query(self, raw_data: str, info: Dict) -> str:
        """Generate query for text QR codes"""
        # Check for agricultural keywords
        agri_keywords = ['fertilizer', 'pesticide', 'seed', 'crop', 'soil', 'water', 'farm', 'agriculture', 
                       'urea', 'dap', 'npk', 'wheat', 'rice', 'cotton', 'organic', 'compost', 'harvest', 'irrigation']
        
        if any(keyword in raw_data.lower() for keyword in agri_keywords):
            query = f"Provide detailed agricultural guidance about: {raw_data}"
            query += ". Explain its importance, usage, application methods, and best practices for Indian agriculture with specific crop recommendations."
        else:
            query = f"Analyze this information and provide comprehensive guidance: {raw_data}"
            query += ". Explain what this information is about, its purpose, and potential applications. If it's not agricultural, explain its general meaning and how it might be useful."
        
        return query
    
    def _generate_type_specific_query(self, qr_type: str, info: Dict, raw_data: str) -> str:
        """Generate query for specific QR types"""
        if qr_type == 'email':
            email = info.get('email', '')
            query = f"Analyze this email address: {email}"
            query += ". Explain what email QR codes are, their security aspects, and how they work. If this appears to be agricultural, explain potential farming applications."
        
        elif qr_type == 'phone':
            phone = info.get('phone', '')
            query = f"Analyze this phone number: {phone}"
            query += ". Explain what phone QR codes are, their uses, and security considerations. If this appears to be agricultural, explain potential farming helpline applications."
        
        elif qr_type == 'location':
            location = info.get('location', '')
            lat = info.get('latitude', '')
            lon = info.get('longitude', '')
            query = f"Analyze this location QR code"
            if lat and lon:
                query += f" with coordinates {lat}, {lon}"
            query += ". Explain location QR codes and their applications. If this is an agricultural area, explain farming potential for this region."
        
        elif qr_type == 'wifi':
            query = "Analyze this WiFi QR code. Explain WiFi QR codes, their security aspects, and how they work. Discuss potential applications in smart agriculture and IoT farming."
        
        elif qr_type == 'vcard':
            query = "Analyze this vCard/contact QR code. Explain vCard format, contact information storage, and QR code business cards. Discuss applications in agricultural networking."
        
        else:
            # Default query for unknown types - universal analysis
            query = f"Analyze this QR code content: {raw_data[:200]}"
            query += ". Explain what type of QR code this is, what information it contains, and its potential applications. Provide comprehensive analysis of its purpose and uses."
        
        return query

    def _fetch_url_content(self, url: str) -> str:
        """Fetch content from a URL for QR code analysis"""
        try:
            logger.info(f"🌐 Fetching content from URL: {url}")
            
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                logger.warning(f"Invalid URL format: {url}")
                return ""
            
            # Make request with timeout
            response = self.session.get(url, timeout=10, allow_redirects=True)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Extract title
            title = ""
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
            
            # Extract main content
            content_parts = []
            
            # Try different content selectors
            content_selectors = [
                'main', 'article', '.content', '.main-content', 
                '.post-content', '.entry-content', '.product-description',
                '.description', 'p', '.text'
            ]
            
            for selector in content_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text().strip()
                    if len(text) > 20:  # Filter out very short text
                        content_parts.append(text)
            
            # Combine content
            content = "\n".join(content_parts)
            
            # Clean up content
            content = re.sub(r'\s+', ' ', content)  # Remove extra whitespace
            content = content[:2000]  # Limit content length
            
            # Format result
            if title and content:
                result = f"Title: {title}\n\nContent: {content}"
            elif content:
                result = content
            else:
                result = f"URL: {url}\nUnable to extract content from this page."
            
            logger.info(f"✅ Successfully fetched content from {url}")
            return result
            
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout while fetching URL: {url}")
            return f"URL: {url}\nRequest timed out while trying to fetch content."
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request error while fetching URL {url}: {e}")
            return f"URL: {url}\nUnable to access this URL."
        except Exception as e:
            logger.error(f"Error fetching URL content: {e}")
            return f"URL: {url}\nError occurred while fetching content."
            qr_code = qr_codes[0]
            qr_data = qr_code.data.decode('utf-8')
            
            # Get product information
            product_info = self._extract_product_info(qr_data)
            
            return {
                "success": True,
                "qr_data": qr_data,
                "product_info": product_info,
                "confidence": self._calculate_confidence(qr_data, product_info),
                "format": qr_code.type,
                "position": {
                    "x": qr_code.rect.x,
                    "y": qr_code.rect.y,
                    "width": qr_code.rect.width,
                    "height": qr_code.rect.height
                }
            }
            
        except Exception as e:
            logger.error(f"QR scanning failed: {e}")
            return {
                "success": False,
                "error": f"Failed to scan QR code: {str(e)}",
                "qr_data": None,
                "product_info": None
            }
    
    def _extract_product_info(self, qr_data):
        """
        Extract product information from QR data.
        Supports URLs, text, and structured data.
        """
        if not qr_data:
            return None
        
        # Check if QR data is a URL
        if qr_data.startswith(('http://', 'https://')):
            return self._extract_from_url(qr_data)
        
        # Check if it's structured data (JSON-like)
        if '{' in qr_data and '}' in qr_data:
            return self._extract_structured_data(qr_data)
        
        # Check if it's product barcode/ID
        if self._is_product_id(qr_data):
            return self._search_product_by_id(qr_data)
        
        # Treat as general text
        return {
            "type": "text",
            "data": qr_data,
            "description": f"QR Code contains: {qr_data[:100]}{'...' if len(qr_data) > 100 else ''}",
            "raw_data": qr_data
        }
    
    def _extract_from_url(self, url):
        """Extract product information from URL."""
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract common product information
                title = self._safe_extract(soup.find('title'))
                description = self._safe_extract(soup.find('meta', attrs={'name': 'description'}))
                
                # Look for product-specific elements
                product_name = None
                price = None
                
                # Common product name selectors
                name_selectors = ['h1', '.product-title', '.product-name', '[data-product-name]']
                for selector in name_selectors:
                    element = soup.select_one(selector)
                    if element:
                        product_name = self._safe_extract(element)
                        break
                
                # Common price selectors
                price_selectors = ['.price', '.product-price', '[data-price]']
                for selector in price_selectors:
                    element = soup.select_one(selector)
                    if element:
                        price_text = self._safe_extract(element)
                        price = self._extract_price(price_text)
                        break
                
                return {
                    "type": "url",
                    "url": url,
                    "title": title,
                    "product_name": product_name,
                    "description": description,
                    "price": price,
                    "raw_data": url
                }
            
        except Exception as e:
            logger.error(f"Failed to extract from URL {url}: {e}")
        
        return {
            "type": "url",
            "url": url,
            "description": f"QR Code contains URL: {url}",
            "raw_data": url
        }
    
    def _extract_structured_data(self, data):
        """Extract information from structured QR data."""
        try:
            # Simple parsing for key-value pairs
            info = {"type": "structured", "raw_data": data}
            
            # Parse common patterns
            patterns = {
                'product': r'product[:\s]+([^\n]+)',
                'name': r'name[:\s]+([^\n]+)',
                'batch': r'batch[:\s]+([^\n]+)',
                'date': r'date[:\s]+([^\n]+)',
                'price': r'price[:\s]+([^\n]+)',
                'id': r'id[:\s]+([^\n]+)'
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, data, re.IGNORECASE)
                if match:
                    info[key] = match.group(1).strip()
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to parse structured data: {e}")
            return {
                "type": "text",
                "description": f"QR Code contains structured data: {data[:100]}...",
                "raw_data": data
            }
    
    def _is_product_id(self, data):
        """Check if data looks like a product ID/barcode."""
        # Common patterns for product IDs
        patterns = [
            r'^\d{8,13}$',  # 8-13 digits (common barcode length)
            r'^[A-Z]{2,4}\d{4,8}$',  # Letter prefix + digits
            r'^\d{4}-\d{4}-\d{4}$',  # Grouped digits
        ]
        
        return any(re.match(pattern, data) for pattern in patterns)
    
    def _search_product_by_id(self, product_id):
        """Search for product information by ID."""
        # For now, return basic info
        # In a real implementation, you could integrate with product databases
        return {
            "type": "product_id",
            "product_id": product_id,
            "description": f"Product ID: {product_id}",
            "note": "This appears to be a product identifier. For detailed information, please check the product packaging or contact the manufacturer.",
            "raw_data": product_id
        }
    
    def _safe_extract(self, element):
        """Safely extract text from HTML element."""
        if element:
            if hasattr(element, 'get_text'):
                return element.get_text().strip()
            elif hasattr(element, 'get'):
                return element.get('content', '').strip()
        return None
    
    def _extract_price(self, price_text):
        """Extract price from text."""
        if not price_text:
            return None
        
        # Look for price patterns
        price_match = re.search(r'[\$₹€£]\s*\d+(?:,\d{3})*(?:\.\d{2})?', price_text)
        if price_match:
            return price_match.group()
        
        # Look for just numbers
        number_match = re.search(r'\d+(?:,\d{3})*(?:\.\d{2})?', price_text)
        if number_match:
            return number_match.group()
        
        return price_text.strip()
    
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
