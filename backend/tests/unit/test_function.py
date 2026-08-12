from src.core.test_validation_system import TestValidationSystem, assert_response_format, assert_error, assert_success
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
