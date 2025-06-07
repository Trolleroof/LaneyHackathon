"""
Authentication utilities
For development, this provides a simple placeholder user
In production, this would handle JWT tokens and real user authentication
"""

async def get_current_user():
    """
    Get current authenticated user
    For development, returns a mock user
    In production, this would validate JWT tokens
    """
    # Mock user for development
    return {
        "id": 1,
        "email": "demo@tenant-rights.com",
        "name": "Demo User"
    } 