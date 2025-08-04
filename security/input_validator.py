
"""
Input Validation and Sanitization Module
Protects against XSS, SQL injection, and malicious inputs
"""
import re
import html
import bleach
from typing import Any, Dict, List, Optional

class InputValidator:
    """Comprehensive input validation and sanitization"""
    
    # Allowed HTML tags for rich text (if needed)
    ALLOWED_TAGS = ['b', 'i', 'em', 'strong', 'p', 'br']
    ALLOWED_ATTRIBUTES = {}
    
    # Regex patterns for validation
    PATTERNS = {
        'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
        'mobile': re.compile(r'^\+?[1-9]\d{1,14}$'),
        'username': re.compile(r'^[a-zA-Z0-9_]{3,20}$'),
        'ucc': re.compile(r'^[A-Z0-9]{5,6}$'),
        'alphanumeric': re.compile(r'^[a-zA-Z0-9]+$'),
        'numeric': re.compile(r'^\d+$'),
        'decimal': re.compile(r'^\d+\.?\d*$'),
        'time_format': re.compile(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$'),
    }
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 255) -> str:
        """Sanitize string input to prevent XSS attacks"""
        if not isinstance(value, str):
            return ""
        
        # Remove null bytes and control characters
        value = value.replace('\x00', '').strip()
        
        # Limit length
        value = value[:max_length]
        
        # HTML escape
        value = html.escape(value)
        
        return value
    
    @staticmethod
    def sanitize_html(value: str) -> str:
        """Sanitize HTML content using bleach"""
        if not isinstance(value, str):
            return ""
        
        return bleach.clean(
            value,
            tags=InputValidator.ALLOWED_TAGS,
            attributes=InputValidator.ALLOWED_ATTRIBUTES,
            strip=True
        )
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        if not email or len(email) > 254:
            return False
        return bool(InputValidator.PATTERNS['email'].match(email))
    
    @staticmethod
    def validate_mobile(mobile: str) -> bool:
        """Validate mobile number format"""
        if not mobile:
            return False
        # Remove spaces and special characters
        mobile_clean = re.sub(r'[^\d+]', '', mobile)
        return bool(InputValidator.PATTERNS['mobile'].match(mobile_clean))
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """Validate username format"""
        if not username:
            return False
        return bool(InputValidator.PATTERNS['username'].match(username))
    
    @staticmethod
    def validate_ucc(ucc: str) -> bool:
        """Validate UCC format"""
        if not ucc:
            return False
        return bool(InputValidator.PATTERNS['ucc'].match(ucc.upper()))
    
    @staticmethod
    def validate_time_format(time_str: str) -> bool:
        """Validate time format (HH:MM)"""
        if not time_str:
            return False
        return bool(InputValidator.PATTERNS['time_format'].match(time_str))
    
    @staticmethod
    def validate_numeric(value: str, min_val: float = None, max_val: float = None) -> bool:
        """Validate numeric input with optional range"""
        if not value:
            return False
        
        try:
            num_val = float(value)
            if min_val is not None and num_val < min_val:
                return False
            if max_val is not None and num_val > max_val:
                return False
            return True
        except ValueError:
            return False
    
    @staticmethod
    def sanitize_sql_input(value: str) -> str:
        """Additional SQL injection protection"""
        if not isinstance(value, str):
            return ""
        
        # Remove dangerous SQL keywords and characters
        dangerous_patterns = [
            r"('|(\\'))",
            r"(;|\\x00)",
            r"(\\n|\\r|\\x1a)",
            r"(\\x00|\\n|\\r|\\x1a|\\x1b)"
        ]
        
        for pattern in dangerous_patterns:
            value = re.sub(pattern, "", value, flags=re.IGNORECASE)
        
        return value
    
    @staticmethod
    def validate_api_request(data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate API request against schema"""
        validated_data = {}
        errors = []
        
        for field, rules in schema.items():
            value = data.get(field)
            
            # Check required fields
            if rules.get('required', False) and not value:
                errors.append(f"{field} is required")
                continue
            
            if value is None:
                continue
            
            # Type validation
            expected_type = rules.get('type', str)
            if not isinstance(value, expected_type):
                try:
                    value = expected_type(value)
                except (ValueError, TypeError):
                    errors.append(f"{field} must be of type {expected_type.__name__}")
                    continue
            
            # String validation
            if isinstance(value, str):
                value = InputValidator.sanitize_string(value, rules.get('max_length', 255))
                
                # Pattern validation
                pattern = rules.get('pattern')
                if pattern and not InputValidator.PATTERNS.get(pattern, re.compile(pattern)).match(value):
                    errors.append(f"{field} format is invalid")
                    continue
            
            # Numeric validation
            if isinstance(value, (int, float)):
                min_val = rules.get('min')
                max_val = rules.get('max')
                if min_val is not None and value < min_val:
                    errors.append(f"{field} must be at least {min_val}")
                    continue
                if max_val is not None and value > max_val:
                    errors.append(f"{field} must be at most {max_val}")
                    continue
            
            validated_data[field] = value
        
        if errors:
            raise ValueError(f"Validation errors: {', '.join(errors)}")
        
        return validated_data


# Validation schemas for common API requests
VALIDATION_SCHEMAS = {
    'login': {
        'username': {'required': True, 'type': str, 'max_length': 50, 'pattern': 'username'},
        'password': {'required': True, 'type': str, 'max_length': 255}
    },
    'register': {
        'email': {'required': True, 'type': str, 'max_length': 120, 'pattern': 'email'},
        'mobile': {'required': True, 'type': str, 'max_length': 15, 'pattern': 'mobile'},
        'password': {'required': True, 'type': str, 'max_length': 255},
        'confirm_password': {'required': True, 'type': str, 'max_length': 255}
    },
    'trading_order': {
        'symbol': {'required': True, 'type': str, 'max_length': 20},
        'quantity': {'required': True, 'type': int, 'min': 1, 'max': 10000},
        'price': {'required': True, 'type': float, 'min': 0.01, 'max': 100000},
        'order_type': {'required': True, 'type': str, 'max_length': 10}
    }
}
