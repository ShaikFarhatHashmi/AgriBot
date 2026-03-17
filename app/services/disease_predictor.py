"""
app/services/disease_predictor_final.py - Final Solution
Intelligent plant type identification + disease detection
"""
import os
import json
import numpy as np
from PIL import Image, ImageDraw
import cv2
from settings import AppConfig

print("[AgriBot] Using FINAL intelligent disease detector")

class IntelligentPlantDiseaseDetector:
    def __init__(self):
        # Load the actual class mapping
        with open(AppConfig.CLASS_MAPPING_PATH, "r") as f:
            self.class_mapping = json.load(f)
        
        # Create reverse mapping (disease_name -> class_id)
        self.reverse_mapping = {v: k for k, v in self.class_mapping.items()}
        
        # Plant characteristics database
        self.plant_characteristics = {
            "Apple": {
                "leaf_shape": "oval_rounded",
                "leaf_size": "medium",
                "edge_pattern": "serrated",
                "color_range": "medium_green",
                "texture": "smooth",
                "diseases": ["Apple___healthy", "Apple___Apple_scab", "Apple___Black_rot", "Apple___Cedar_apple_rust"]
            },
            "Tomato": {
                "leaf_shape": "compound_lobed",
                "leaf_size": "medium",
                "edge_pattern": "irregular_lobes",
                "color_range": "bright_green",
                "texture": "hairy",
                "diseases": ["Tomato___healthy", "Tomato___Bacterial_spot", "Tomato___Early_blight", "Tomato___Late_blight", "Tomato___Leaf_Mold", "Tomato___Septoria_leaf_spot", "Tomato___Spider_mites Two-spotted_spider_mite", "Tomato___Target_Spot", "Tomato___Tomato_Yellow_Leaf_Curl_Virus", "Tomato___Tomato_mosaic_virus"]
            },
            "Banana": {
                "leaf_shape": "large_elliptical",
                "leaf_size": "very_large",
                "edge_pattern": "entire_smooth",
                "color_range": "bright_green",
                "texture": "smooth_glossy",
                "diseases": ["Banana___healthy", "Banana___Leaf_Spot", "Banana___Panama_Disease"]
            },
            "Mango": {
                "leaf_shape": "lanceolate",
                "leaf_size": "large",
                "edge_pattern": "entire",
                "color_range": "dark_green",
                "texture": "glossy",
                "diseases": ["Mango___healthy", "Mango___Anthracnose"]
            },
            "Corn": {
                "leaf_shape": "linear_lanceolate",
                "leaf_size": "very_large",
                "edge_pattern": "entire",
                "color_range": "light_green",
                "texture": "parallel_veins",
                "diseases": ["Corn_(maize)___healthy", "Corn_(maize)___Common_rust_", "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot", "Corn_(maize)___Northern_Leaf_Blight"]
            },
            "Potato": {
                "leaf_shape": "compound_oval",
                "leaf_size": "medium_large",
                "edge_pattern": "rounded_lobes",
                "color_range": "dark_green",
                "texture": "slightly_hairy",
                "diseases": ["Potato___healthy", "Potato___Early_blight", "Potato___Late_blight"]
            },
            "Soybean": {
                "leaf_shape": "trifoliate",
                "leaf_size": "medium",
                "edge_pattern": "entire",
                "color_range": "bright_green",
                "texture": "smooth",
                "diseases": ["Soybean___healthy"]
            },
            "Squash": {
                "leaf_shape": "palmately_lobed",
                "leaf_size": "very_large",
                "edge_pattern": "deep_lobes",
                "color_range": "grayish_green",
                "texture": "rough_hairy",
                "diseases": ["Squash___Powdery_mildew", "Squash___healthy"]
            }
        }
        
        # Disease patterns
        self.disease_patterns = {
            # Healthy patterns
            "healthy": {
                "color_signature": "dominant_green",
                "symptoms": "No visible disease symptoms, healthy leaves",
                "treatment": "Continue regular care, proper watering, and monitoring"
            },
            # Disease patterns
            "scab": {
                "color_signature": "olive_green_spots",
                "symptoms": "Olive-green spots on leaves, corky lesions",
                "treatment": "Apply fungicide sprays, remove infected parts, improve air circulation"
            },
            "rot": {
                "color_signature": "brown_black_lesions",
                "symptoms": "Brown to black rot, concentric rings, decay",
                "treatment": "Remove infected parts, apply copper fungicide, improve drainage"
            },
            "rust": {
                "color_signature": "orange_rust_pustules",
                "symptoms": "Orange to rust-colored pustules, premature death",
                "treatment": "Apply fungicide, use resistant varieties, crop rotation"
            },
            "blight": {
                "color_signature": "brown_target_spots",
                "symptoms": "Brown patches, target-shaped spots, rapid spread",
                "treatment": "Apply fungicide, ensure good drainage, proper spacing"
            },
            "virus": {
                "color_signature": "mosaic_yellowing",
                "symptoms": "Mosaic patterns, yellowing, curling, stunted growth",
                "treatment": "Remove infected plants, control vectors, use resistant varieties"
            },
            "powdery": {
                "color_signature": "white_powdery_coating",
                "symptoms": "White powdery coating, yellowing, leaf distortion",
                "treatment": "Apply fungicide, improve air circulation, resistant varieties"
            },
            "spot": {
                "color_signature": "circular_spots",
                "symptoms": "Circular spots with distinct borders, yellowing",
                "treatment": "Remove infected leaves, apply copper fungicide, avoid overhead watering"
            }
        }
    
    def identify_plant_type(self, img_array):
        """Intelligent plant type identification based on visual characteristics"""
        hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Analyze color characteristics
        green_mask = ((hsv[:,:,0] >= 35) & (hsv[:,:,0] <= 85)) & (hsv[:,:,1] >= 40) & (hsv[:,:,2] >= 40)
        green_ratio = np.sum(green_mask) / (hsv.shape[0] * hsv.shape[1])
        
        # Calculate average green intensity (darker vs lighter green)
        green_pixels = img_array[green_mask > 0]
        if len(green_pixels) > 0:
            avg_green_intensity = np.mean(green_pixels[:, 1])  # Green channel
        else:
            avg_green_intensity = 0
        
        # Analyze leaf shape and size
        contours, _ = cv2.findContours(green_mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # Get the largest contour (main leaf)
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            perimeter = cv2.arcLength(largest_contour, True)
            
            if perimeter > 0:
                circularity = 4 * np.pi * area / (perimeter * perimeter)
            else:
                circularity = 0
            
            # Aspect ratio (width/height)
            x, y, w, h = cv2.boundingRect(largest_contour)
            aspect_ratio = w / h if h > 0 else 1
            
            # Leaf size classification
            img_area = img_array.shape[0] * img_array.shape[1]
            leaf_coverage = area / img_area
            
            # Edge complexity (number of edge points)
            edges = cv2.Canny(gray, 50, 150)
            edge_points = np.sum(edges > 0)
            edge_complexity = edge_points / (img_array.shape[0] * img_array.shape[1])
        else:
            area = 0
            circularity = 0
            aspect_ratio = 1
            leaf_coverage = 0
            edge_complexity = 0
        
        # Plant type scoring
        plant_scores = {}
        
        for plant_type, characteristics in self.plant_characteristics.items():
            score = 0
            
            # Enhanced leaf shape scoring with more specific conditions
            shape = characteristics["leaf_shape"]
            if shape == "large_elliptical" and aspect_ratio > 1.4 and leaf_coverage > 0.5:
                score += 50  # Very high score for banana's distinctive large elliptical shape
            elif shape == "palmately_lobed" and circularity < 0.3 and edge_complexity > 0.08:
                score += 45  # High score for squash's distinctive palmate shape
            elif shape == "compound_lobed" and circularity < 0.4 and edge_complexity > 0.06:
                score += 40  # High score for tomato's compound leaves
            elif shape == "linear_lanceolate" and aspect_ratio > 2.5:
                score += 45  # High score for corn's distinctive long narrow leaves
            elif shape == "oval_rounded" and 0.5 < circularity < 0.8 and edge_complexity < 0.08:
                score += 35  # Moderate score for apple's oval shape
            elif shape == "trifoliate" and area < 10000:
                score += 30
            else:
                score += 5  # Minimal score for non-matching shapes
            
            # Leaf size scoring - more distinctive
            size = characteristics["leaf_size"]
            if size == "very_large" and leaf_coverage > 0.7:
                score += 25  # Higher score for very large leaves
            elif size == "large" and leaf_coverage > 0.5:
                score += 22
            elif size == "medium_large" and 0.3 < leaf_coverage < 0.6:
                score += 20
            elif size == "medium" and 0.2 < leaf_coverage < 0.5:
                score += 18  # Lower score for medium leaves (apple)
            
            # Enhanced color scoring with more specific ranges
            color_range = characteristics["color_range"]
            if color_range == "dark_green" and avg_green_intensity < 110:
                score += 25  # High score for dark green (banana, mango)
            elif color_range == "grayish_green" and 80 < avg_green_intensity < 120:
                score += 25  # High score for grayish green (squash)
            elif color_range == "bright_green" and avg_green_intensity > 140:
                score += 20
            elif color_range == "medium_green" and 110 < avg_green_intensity < 140:
                score += 20
            elif color_range == "light_green" and avg_green_intensity > 160:
                score += 20
            else:
                score += 5
            
            # Enhanced edge pattern scoring
            edge_pattern = characteristics["edge_pattern"]
            if edge_pattern == "entire_smooth" and edge_complexity < 0.06:
                score += 20  # High score for smooth edges (banana)
            elif edge_pattern == "deep_lobes" and edge_complexity > 0.1:
                score += 20  # High score for deep lobes (squash)
            elif edge_pattern == "serrated" and 0.06 < edge_complexity < 0.1:
                score += 20  # High score for serrated edges (apple)
            elif edge_pattern == "irregular_lobes" and edge_complexity > 0.08:
                score += 15
            else:
                score += 5
            
            plant_scores[plant_type] = score
        
        # Get best plant type
        best_plant_type = max(plant_scores, key=plant_scores.get)
        best_score = plant_scores[best_plant_type]
        
        return best_plant_type, best_score, plant_scores
    
    def analyze_disease_symptoms(self, img_array, plant_type):
        """Analyze disease symptoms for the identified plant type"""
        hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
        
        # Color analysis
        green_mask = ((hsv[:,:,0] >= 35) & (hsv[:,:,0] <= 85)) & (hsv[:,:,1] >= 40) & (hsv[:,:,2] >= 40)
        green_ratio = np.sum(green_mask) / (hsv.shape[0] * hsv.shape[1])
        
        yellow_mask = ((hsv[:,:,0] >= 20) & (hsv[:,:,0] <= 60)) & (hsv[:,:,1] >= 50)
        yellow_ratio = np.sum(yellow_mask) / (hsv.shape[0] * hsv.shape[1])
        
        brown_mask = ((hsv[:,:,0] >= 10) & (hsv[:,:,0] <= 30)) & (hsv[:,:,1] >= 30) & (hsv[:,:,2] <= 255)
        brown_ratio = np.sum(brown_mask) / (hsv.shape[0] * hsv.shape[1])
        
        orange_mask = ((hsv[:,:,0] >= 10) & (hsv[:,:,0] <= 20)) & (hsv[:,:,1] >= 100) & (hsv[:,:,2] >= 100)
        orange_ratio = np.sum(orange_mask) / (hsv.shape[0] * hsv.shape[1])
        
        white_mask = (hsv[:,:,1] < 30) & (hsv[:,:,2] > 200)
        white_ratio = np.sum(white_mask) / (hsv.shape[0] * hsv.shape[1])
        
        # Disease scoring
        disease_scores = {}
        
        for disease_type, pattern in self.disease_patterns.items():
            score = 0
            signature = pattern["color_signature"]
            
            if signature == "dominant_green":
                # Only classify as healthy if there's very little disease symptoms
                disease_symptoms = (brown_ratio + yellow_ratio + orange_ratio + white_ratio)
                if green_ratio > 0.7 and disease_symptoms < 0.05:
                    score = 100
                elif green_ratio > 0.6 and disease_symptoms < 0.1:
                    score = 80
                else:
                    score = 0
                    
            elif signature == "olive_green_spots":
                if green_ratio > 0.4 and brown_ratio > 0.1:
                    score = 90
                elif brown_ratio > 0.05:
                    score = 70
                else:
                    score = 0
                    
            elif signature == "brown_black_lesions":
                if brown_ratio > 0.3:
                    score = 95
                elif brown_ratio > 0.2:
                    score = 75
                else:
                    score = 0
                    
            elif signature == "orange_rust_pustules":
                if orange_ratio > 0.3:
                    score = 95
                elif orange_ratio > 0.2:
                    score = 75
                else:
                    score = 0
                    
            elif signature == "brown_target_spots":
                if brown_ratio > 0.3:
                    score = 90
                elif brown_ratio > 0.2:
                    score = 70
                else:
                    score = 0
                    
            elif signature == "mosaic_yellowing":
                if yellow_ratio > 0.15 and green_ratio > 0.3:  # Lower threshold
                    score = 90
                elif yellow_ratio > 0.1:
                    score = 70
                else:
                    score = 0
                    
            elif signature == "white_powdery_coating":
                if white_ratio > 0.1:  # Lower threshold for detection
                    score = 95
                elif white_ratio > 0.05:
                    score = 75
                else:
                    score = 0
                    
            elif signature == "circular_spots":
                if brown_ratio > 0.1:  # Lower threshold for detection
                    score = 85
                elif brown_ratio > 0.05:
                    score = 65
                else:
                    score = 0
            
            disease_scores[disease_type] = score
        
        # Get best disease type
        best_disease_type = max(disease_scores, key=disease_scores.get)
        best_score = disease_scores[best_disease_type]
        
        return best_disease_type, best_score, disease_scores
    
    def predict_disease_intelligent(self, image_file):
        """Intelligent plant disease prediction"""
        try:
            img = Image.open(image_file).convert("RGB")
            img_array = np.array(img)
            
            # Step 1: Identify plant type
            plant_type, plant_score, all_plant_scores = self.identify_plant_type(img_array)
            
            # Step 2: Analyze disease symptoms
            disease_type, disease_score, all_disease_scores = self.analyze_disease_symptoms(img_array, plant_type)
            
            # Step 3: Combine plant type and disease type
            if plant_type in self.plant_characteristics:
                possible_diseases = self.plant_characteristics[plant_type]["diseases"]
                
                # Find the best matching disease
                if disease_type == "healthy":
                    predicted_disease = f"{plant_type}___healthy"
                elif disease_type == "scab" and any("scab" in d for d in possible_diseases):
                    predicted_disease = next(d for d in possible_diseases if "scab" in d)
                elif disease_type == "rot" and any("rot" in d for d in possible_diseases):
                    predicted_disease = next(d for d in possible_diseases if "rot" in d)
                elif disease_type == "rust" and any("rust" in d for d in possible_diseases):
                    predicted_disease = next(d for d in possible_diseases if "rust" in d)
                elif disease_type == "blight" and any("blight" in d for d in possible_diseases):
                    predicted_disease = next(d for d in possible_diseases if "blight" in d)
                elif disease_type == "virus" and any("virus" in d for d in possible_diseases):
                    predicted_disease = next(d for d in possible_diseases if "virus" in d)
                elif disease_type == "powdery" and any("powdery" in d for d in possible_diseases):
                    predicted_disease = next(d for d in possible_diseases if "powdery" in d)
                elif disease_type == "spot" and any("spot" in d for d in possible_diseases):
                    predicted_disease = next(d for d in possible_diseases if "spot" in d)
                elif disease_type == "mold" and any("mold" in d for d in possible_diseases):
                    predicted_disease = next(d for d in possible_diseases if "mold" in d)
                elif disease_type == "bacterial" and any("Bacterial" in d for d in possible_diseases):
                    predicted_disease = next(d for d in possible_diseases if "Bacterial" in d)
                else:
                    # Simplified disease matching - use detected disease directly
                    if disease_score > 60:  # Use disease if we're confident
                        # Map detected disease to available plant diseases
                        if plant_type == "Apple":
                            if disease_type in ["scab", "spot"]:
                                predicted_disease = "Apple___Apple_scab"
                            elif disease_type in ["rot", "blight"]:
                                predicted_disease = "Apple___Black_rot"
                            elif disease_type == "rust":
                                predicted_disease = "Apple___Cedar_apple_rust"
                            else:
                                predicted_disease = f"{plant_type}___healthy"
                        elif plant_type == "Tomato":
                            if disease_type == "spot":
                                predicted_disease = "Tomato___Septoria_leaf_spot"
                            elif disease_type == "blight":
                                predicted_disease = "Tomato___Early_blight"
                            elif disease_type == "mold":
                                predicted_disease = "Tomato___Leaf_Mold"
                            elif disease_type == "virus":
                                predicted_disease = "Tomato___Tomato_mosaic_virus"
                            elif disease_type == "rust":
                                predicted_disease = "Tomato___Spider_mites Two-spotted_spider_mite"
                            else:
                                predicted_disease = f"{plant_type}___healthy"
                        elif plant_type == "Corn":
                            if disease_type == "rust":
                                predicted_disease = "Corn_(maize)___Common_rust_"
                            elif disease_type == "blight":
                                predicted_disease = "Corn_(maize)___Northern_Leaf_Blight"
                            elif disease_type == "spot":
                                predicted_disease = "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot"
                            else:
                                predicted_disease = f"{plant_type}___healthy"
                        elif plant_type == "Squash":
                            if disease_type == "powdery":
                                predicted_disease = "Squash___Powdery_mildew"
                            else:
                                predicted_disease = f"{plant_type}___healthy"
                        else:
                            # For other plants, try to find a match
                            if disease_type == "scab" and any("scab" in d for d in possible_diseases):
                                predicted_disease = next(d for d in possible_diseases if "scab" in d)
                            elif disease_type == "rot" and any("rot" in d for d in possible_diseases):
                                predicted_disease = next(d for d in possible_diseases if "rot" in d)
                            elif disease_type == "rust" and any("rust" in d for d in possible_diseases):
                                predicted_disease = next(d for d in possible_diseases if "rust" in d)
                            elif disease_type == "blight" and any("blight" in d for d in possible_diseases):
                                predicted_disease = next(d for d in possible_diseases if "blight" in d)
                            elif disease_type == "virus" and any("virus" in d for d in possible_diseases):
                                predicted_disease = next(d for d in possible_diseases if "virus" in d)
                            elif disease_type == "powdery" and any("powdery" in d for d in possible_diseases):
                                predicted_disease = next(d for d in possible_diseases if "powdery" in d)
                            elif disease_type == "spot" and any("spot" in d for d in possible_diseases):
                                predicted_disease = next(d for d in possible_diseases if "spot" in d)
                            elif disease_type == "mold" and any("mold" in d for d in possible_diseases):
                                predicted_disease = next(d for d in possible_diseases if "mold" in d)
                            else:
                                predicted_disease = f"{plant_type}___healthy"
                    else:
                        # Low confidence - use healthy
                        predicted_disease = f"{plant_type}___healthy"
            else:
                predicted_disease = "Unknown_Plant_Condition"
            
            # Step 4: Get disease info
            disease_info = self.disease_patterns.get(disease_type, {
                "symptoms": "Unable to determine specific symptoms",
                "treatment": "Consult agricultural expert for proper diagnosis"
            })
            
            # Step 5: Calculate confidence
            confidence = min(95, max(30, (plant_score + disease_score) * 0.4))
            
            # Get class index
            class_index = self.reverse_mapping.get(predicted_disease, "0")
            
            # Provide meaningful display name based on detected disease
            if disease_score > 60 and disease_type != "healthy":
                display_name = f"Detected {disease_type.replace('_', ' ').title()} - {disease_info['symptoms'][:50]}..."
            else:
                display_name = predicted_disease.replace("___", " — ").replace("_", " ")
            
            return {
                "disease": predicted_disease,
                "display_name": display_name,
                "confidence": confidence,
                "class_index": class_index,
                "reliable": confidence >= AppConfig.CNN_CONFIDENCE_MIN,
                "method": "intelligent_plant_analysis",
                "identified_plant_type": plant_type,
                "plant_type_score": plant_score,
                "identified_disease_type": disease_type,
                "disease_score": disease_score,
                "all_plant_scores": all_plant_scores,
                "all_disease_scores": all_disease_scores,
                "disease_info": {
                    "name": f"{disease_type.replace('_', ' ').title()} Detection" if disease_score > 60 and disease_type != "healthy" else predicted_disease.replace("___", " — ").replace("_", " "),
                    "symptoms": disease_info["symptoms"],
                    "treatment": disease_info["treatment"]
                },
                "is_known_plant": predicted_disease in self.reverse_mapping
            }
            
        except Exception as e:
            return self._fallback_prediction()
    
    def _fallback_prediction(self):
        """Fallback prediction"""
        return {
            "disease": "Unknown_Plant_Condition",
            "display_name": "Unknown Plant Condition",
            "confidence": 30.0,
            "class_index": "0",
            "reliable": False,
            "method": "fallback",
            "identified_plant_type": "unknown",
            "plant_type_score": 0,
            "identified_disease_type": "unknown",
            "disease_score": 0,
            "all_plant_scores": {},
            "all_disease_scores": {},
            "disease_info": {
                "name": "Unknown Plant Condition",
                "symptoms": "Unable to analyze the provided image",
                "treatment": "Please provide a clear, well-lit image showing the affected areas"
            },
            "is_known_plant": False
        }

# Global detector instance
_detector = IntelligentPlantDiseaseDetector()

def predict_disease(image_file):
    """Main prediction function - intelligent plant identification"""
    return _detector.predict_disease_intelligent(image_file)

def build_rag_query(prediction_result):
    """RAG query builder with plant and disease context"""
    disease = prediction_result["display_name"]
    plant_type = prediction_result.get("identified_plant_type", "unknown")
    disease_type = prediction_result.get("identified_disease_type", "unknown")
    disease_info = prediction_result.get("disease_info", {})
    
    # Check if this is a healthy plant
    if "healthy" in disease.lower() or disease_type.lower() == "healthy":
        query_parts = [
            f"Provide detailed agricultural information about {plant_type} plants",
            f"Plant type: {plant_type}",
            f"Condition: Healthy",
            f"Status: No disease detected - plant appears healthy",
            f"Focus: General care, maintenance, and best practices for {plant_type} cultivation"
        ]
    else:
        # This is actually a disease case
        query_parts = [
            f"Provide detailed agricultural information about {disease}",
            f"Plant type identified: {plant_type}",
            f"Disease type: {disease_type}",
            f"Symptoms: {disease_info.get('symptoms', 'Not specified')}",
            f"Treatment: {disease_info.get('treatment', 'Not specified')}"
        ]
    
    query_parts.append("Include information relevant to Indian farming conditions and plant-specific management practices.")
    
    return " ".join(query_parts)

print("[AgriBot] ✅ INTELLIGENT disease detector loaded - identifies plant type, then disease!")
