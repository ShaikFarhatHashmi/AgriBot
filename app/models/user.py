"""
app/models/user.py — User Model
================================
LAYER  : Model
PURPOSE: User data management and authentication
"""

import hashlib
import secrets
from datetime import datetime
from typing import Optional, Dict, Any

class UserModel:
    """Simple file-based user model for demonstration"""
    
    def __init__(self, users_file: str = "data/users.json"):
        self.users_file = users_file
        self._ensure_data_dir()
        self._load_users()
    
    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        import os
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
    
    def _load_users(self):
        """Load users from JSON file"""
        import json
        import os
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r') as f:
                    self.users = json.load(f)
            else:
                self.users = {}
        except Exception:
            self.users = {}
    
    def _save_users(self):
        """Save users to JSON file"""
        import json
        try:
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2)
        except Exception as e:
            print(f"Error saving users: {e}")
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            salt, password_hash = hashed.split(':')
            return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
        except:
            return False
    
    def create_user(self, email: str, password: str, first_name: str = "", 
                   last_name: str = "", phone: str = "", state: str = "") -> Dict[str, Any]:
        """Create a new user"""
        if email in self.users:
            return {"success": False, "error": "User already exists"}
        
        if len(password) < 8:
            return {"success": False, "error": "Password must be at least 8 characters"}
        
        user_data = {
            "email": email,
            "password": self._hash_password(password),
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone,
            "state": state,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "is_active": True
        }
        
        self.users[email] = user_data
        self._save_users()
        
        # Remove password from return data
        user_data_copy = user_data.copy()
        del user_data_copy["password"]
        
        return {"success": True, "user": user_data_copy}
    
    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user with email and password"""
        if email not in self.users:
            return {"success": False, "error": "Invalid credentials"}
        
        user = self.users[email]
        
        if not user.get("is_active", True):
            return {"success": False, "error": "Account is deactivated"}
        
        if not self._verify_password(password, user["password"]):
            return {"success": False, "error": "Invalid credentials"}
        
        # Update last login
        user["last_login"] = datetime.now().isoformat()
        self._save_users()
        
        # Remove password from return data
        user_data = user.copy()
        del user_data["password"]
        
        return {"success": True, "user": user_data}
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email (without password)"""
        if email not in self.users:
            return None
        
        user = self.users[email].copy()
        del user["password"]
        return user
    
    def update_user(self, email: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user data"""
        if email not in self.users:
            return {"success": False, "error": "User not found"}
        
        # Don't allow password updates through this method
        if "password" in updates:
            del updates["password"]
        
        self.users[email].update(updates)
        self._save_users()
        
        user_data = self.users[email].copy()
        del user_data["password"]
        
        return {"success": True, "user": user_data}
    
    def change_password(self, email: str, old_password: str, new_password: str) -> Dict[str, Any]:
        """Change user password"""
        if email not in self.users:
            return {"success": False, "error": "User not found"}
        
        user = self.users[email]
        
        if not self._verify_password(old_password, user["password"]):
            return {"success": False, "error": "Current password is incorrect"}
        
        if len(new_password) < 8:
            return {"success": False, "error": "New password must be at least 8 characters"}
        
        user["password"] = self._hash_password(new_password)
        self._save_users()
        
        return {"success": True, "message": "Password updated successfully"}
