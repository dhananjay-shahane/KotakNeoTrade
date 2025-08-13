"""
Template helper functions for component visibility and other utilities
"""

from flask import session
from utils.component_visibility import component_manager

def is_component_visible(component_name):
    """
    Template filter to check if a component is visible for the current user
    
    Args:
        component_name: Name of the component to check
        
    Returns:
        Boolean indicating if component should be visible
    """
    username = session.get('username')
    if not username:
        return True  # Default to visible if not logged in
    
    return component_manager.is_component_visible(username, component_name)

def get_user_component_settings():
    """
    Get all component settings for the current user
    
    Returns:
        Dictionary of component visibility settings
    """
    username = session.get('username')
    if not username:
        return {}
    
    return component_manager.get_user_component_settings(username)

def register_template_helpers(app):
    """Register template filters and context processors with Flask app"""
    
    # Register template filter
    app.jinja_env.filters['is_component_visible'] = is_component_visible
    
    # Register context processor to make component settings available in all templates
    @app.context_processor
    def inject_component_settings():
        return {
            'component_settings': get_user_component_settings(),
            'is_component_visible': is_component_visible
        }