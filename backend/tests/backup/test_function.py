
from src.core.exceptions import ValidationError, AuthenticationError, NotFoundError
async def test_func():
    """
    Test docstring
    
    Returns:
        Test return
    """
    return {"test": "value"}

# Try to import
try:
    import test_function
    print("Test function imported successfully")
except Exception as e:
    print(f"Error: {e}")
