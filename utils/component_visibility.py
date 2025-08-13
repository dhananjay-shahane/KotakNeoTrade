"""
Component Visibility Manager
Handles dynamic showing/hiding of UI components based on admin panel settings
"""

import logging
from typing import Dict, List, Optional
try:
    from config.database_config import DatabaseConfig
except ImportError:
    DatabaseConfig = None

logger = logging.getLogger(__name__)

class ComponentVisibilityManager:
    """Manages component visibility for users based on admin panel settings"""
    
    def __init__(self):
        if DatabaseConfig:
            self.db_config = DatabaseConfig()
        else:
            self.db_config = None
    
    def get_user_component_settings(self, username: str) -> Dict[str, bool]:
        """
        Get component visibility settings for a specific user
        
        Args:
            username: The username to get settings for
            
        Returns:
            Dictionary mapping component names to their visibility status
        """
        try:
            query = """
                SELECT component_name, status 
                FROM admin_panel.component_controls 
                WHERE username = %s
            """
            
            if not self.db_config:
                logger.error("Database config not available")
                return self._get_default_settings()
                
            conn = self.db_config.get_dict_connection()
            if not conn:
                logger.error("Failed to get database connection")
                return self._get_default_settings()
                
            try:
                with conn.cursor() as cursor:
                    cursor.execute(query, (username,))
                    results = cursor.fetchall()
                    
                    # Convert to dictionary
                    settings = {}
                    for row in results:
                        settings[row['component_name']] = row['status']
                    
                    logger.info(f"Retrieved component settings for {username}: {settings}")
                    return settings
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Error retrieving component settings for {username}: {e}")
            return self._get_default_settings()
    
    def is_component_visible(self, username: str, component_name: str) -> bool:
        """
        Check if a specific component should be visible for a user
        
        Args:
            username: The username to check
            component_name: The component to check (e.g., 'portfolio', 'charts')
            
        Returns:
            True if component should be visible, False otherwise
        """
        try:
            query = """
                SELECT status 
                FROM admin_panel.component_controls 
                WHERE username = %s AND component_name = %s
            """
            
            if not self.db_config:
                logger.error("Database config not available")
                return True
                
            conn = self.db_config.get_dict_connection()
            if not conn:
                logger.error("Failed to get database connection")
                return True  # Default to visible if DB error
                
            try:
                with conn.cursor() as cursor:
                    cursor.execute(query, (username, component_name))
                    result = cursor.fetchone()
                    
                    if result:
                        return result['status']
                    else:
                        # Component not found in settings, default to visible
                        logger.warning(f"Component '{component_name}' not found for user '{username}', defaulting to visible")
                        return True
            finally:
                conn.close()
                    
        except Exception as e:
            logger.error(f"Error checking component visibility for {username}.{component_name}: {e}")
            return True  # Default to visible on error
    
    def update_component_status(self, username: str, component_name: str, status: bool) -> bool:
        """
        Update the visibility status of a component for a user
        
        Args:
            username: The username
            component_name: The component name
            status: New visibility status
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            query = """
                INSERT INTO admin_panel.component_controls 
                (username, component_name, status, updated_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (username, component_name) 
                DO UPDATE SET 
                    status = EXCLUDED.status,
                    updated_at = CURRENT_TIMESTAMP
            """
            
            if not self.db_config:
                logger.error("Database config not available")
                return False
                
            conn = self.db_config.get_connection()
            if not conn:
                logger.error("Failed to get database connection")
                return False
                
            try:
                with conn.cursor() as cursor:
                    cursor.execute(query, (username, component_name, status))
                    conn.commit()
                    
                    logger.info(f"Updated component {component_name} for {username} to {status}")
                    return True
            except Exception as e:
                logger.error(f"Error updating component status: {e}")
                conn.rollback()
                return False
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Error updating component status: {e}")
            return False
    
    def get_available_components(self) -> List[str]:
        """
        Get list of all available components that can be controlled
        
        Returns:
            List of component names
        """
        return [
            'portfolio',
            'trading_signals', 
            'deals',
            'market_watch',
            'default_deals',
            'charts',
            'dashboard',
            'orders',
            'positions',
            'holdings'
        ]
    
    def _get_default_settings(self) -> Dict[str, bool]:
        """
        Get default component settings (all visible) when database is unavailable
        
        Returns:
            Dictionary with all components set to visible
        """
        components = self.get_available_components()
        return {component: True for component in components}
    
    def initialize_user_settings(self, username: str, default_visible: bool = False) -> bool:
        """
        Initialize component settings for a new user
        
        Args:
            username: Username to initialize
            default_visible: Whether components should be visible by default
            
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            if not self.db_config:
                logger.error("Database config not available")
                return False
                
            components = self.get_available_components()
            
            conn = self.db_config.get_connection()
            if not conn:
                logger.error("Failed to get database connection")
                return False
                
            try:
                with conn.cursor() as cursor:
                    for component in components:
                        query = """
                            INSERT INTO admin_panel.component_controls 
                            (username, component_name, status, created_at, updated_at)
                            VALUES (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                            ON CONFLICT (username, component_name) DO NOTHING
                        """
                        cursor.execute(query, (username, component, default_visible))
                    
                    conn.commit()
                    logger.info(f"Initialized component settings for user {username}")
                    return True
            except Exception as e:
                logger.error(f"Error initializing user settings: {e}")
                conn.rollback()
                return False
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Error initializing user settings: {e}")
            return False

# Global instance for use throughout the application
component_manager = ComponentVisibilityManager()