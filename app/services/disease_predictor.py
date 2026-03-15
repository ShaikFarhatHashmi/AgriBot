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
                "diseases": ["Squash___Powdery_mildew"]
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
            
            # Leaf shape scoring
            shape = characteristics["leaf_shape"]
            if shape == "oval_rounded" and 0.4 < circularity < 0.8:
                score += 25
            elif shape == "compound_lobed" and circularity < 0.3:
                score += 25
            elif shape == "large_elliptical" and aspect_ratio > 1.5 and leaf_coverage > 0.6:
                score += 25
            elif shape == "lanceolate" and aspect_ratio > 2.0:
                score += 25
            elif shape == "linear_lanceolate" and aspect_ratio > 3.0:
                score += 25
            elif shape == "trifoliate" and area < 8000:
                score += 25
            elif shape == "palmately_lobed" and circularity < 0.2 and edge_complexity > 0.1:
                score += 25
            
            # Leaf size scoring
            size = characteristics["leaf_size"]
            if size == "very_large" and leaf_coverage > 0.7:
                score += 20
            elif size == "large" and leaf_coverage > 0.5:
                score += 20
            elif size == "medium_large" and 0.3 < leaf_coverage < 0.6:
                score += 20
            elif size == "medium" and 0.2 < leaf_coverage < 0.5:
                score += 20
            
            # Color range scoring
            color_range = characteristics["color_range"]
            if color_range == "bright_green" and avg_green_intensity > 150:
                score += 20
            elif color_range == "medium_green" and 100 < avg_green_intensity < 150:
                score += 20
            elif color_range == "dark_green" and avg_green_intensity < 100:
                score += 20
            elif color_range == "light_green" and avg_green_intensity > 180:
                score += 20
            elif color_range == "grayish_green" and avg_green_intensity < 120:
                score += 20
            
            # Texture/edge pattern scoring
            edge_pattern = characteristics["edge_pattern"]
            if edge_pattern == "serrated" and edge_complexity > 0.08:
                score += 15
            elif edge_pattern == "irregular_lobes" and edge_complexity > 0.1:
                score += 15
            elif edge_pattern == "entire_smooth" and edge_complexity < 0.05:
                score += 15
            elif edge_pattern == "entire" and edge_complexity < 0.06:
                score += 15
            elif edge_pattern == "deep_lobes" and edge_complexity > 0.12:
                score += 15
            elif edge_pattern == "rounded_lobes" and 0.05 < edge_complexity < 0.08:
                score += 15
            
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
                if green_ratio > 0.8:
                    score = 100
                elif green_ratio > 0.6:
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
                if yellow_ratio > 0.3 and green_ratio > 0.3:
                    score = 90
                elif yellow_ratio > 0.2:
                    score = 70
                else:
                    score = 0
                    
            elif signature == "white_powdery_coating":
                if white_ratio > 0.3:
                    score = 95
                elif white_ratio > 0.2:
                    score = 75
                else:
                    score = 0
                    
            elif signature == "circular_spots":
                if brown_ratio > 0.2:
                    score = 85
                elif brown_ratio > 0.15:
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
                else:
                    # Fallback to healthy
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
            
            return {
                "disease": predicted_disease,
                "display_name": predicted_disease.replace("___", " — ").replace("_", " "),
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
                    "name": predicted_disease.replace("___", " — ").replace("_", " "),
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
    
    query_parts = [
        f"Provide detailed agricultural information about {disease}",
        f"Plant type identified: {plant_type}",
        f"Disease type: {disease_type}",
        f"Symptoms: {disease_info.get('symptoms', 'Not specified')}",
        f"Treatment: {disease_info.get('treatment', 'Not specified')}"
    ]
    
    query_parts.append("Include information relevant to Indian farming conditions and plant-specific disease management practices.")
    
    return " ".join(query_parts)

print("[AgriBot] ✅ INTELLIGENT disease detector loaded - identifies plant type, then disease!")
