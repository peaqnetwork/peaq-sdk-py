import pytest
import uuid

@pytest.fixture(params=["test-role"])
def role_name(request):
    return request.param

@pytest.fixture
def role_id():
    """Generate a unique 32-character role ID for each test."""
    return str(uuid.uuid4())[:32]

@pytest.fixture(params=["test-group"])
def group_name(request):
    return request.param

@pytest.fixture
def group_id():
    """Generate a unique 32-character group ID for each test."""
    return str(uuid.uuid4())[:32]

@pytest.fixture(params=["test-permission"])
def permission_name(request):
    return request.param

@pytest.fixture
def permission_id():
    """Generate a unique 32-character permission ID for each test."""
    return str(uuid.uuid4())[:32]

@pytest.fixture
def user_id():
    """Generate a unique 32-character user ID for each test."""
    return str(uuid.uuid4())[:32]