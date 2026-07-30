import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import jwt
from datetime import datetime, timedelta, timezone

from app.main import app
from app.core.database import Base, get_db
from app.core.security.auth import SECRET_KEY, ALGORITHM

# Use an in-memory SQLite DB for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def test_websocket_auth_failure():
    # Attempt to connect without a token
    with pytest.raises(Exception): # Usually websockets.exceptions.ConnectionClosed
        with client.websocket_connect("/notifications/ws") as websocket:
            pass

def test_websocket_connection_and_receive():
    # First, create a mock user in the test DB
    from app.modules.users.models.user import User
    db = TestingSessionLocal()
    # Check if user exists
    user = db.query(User).filter(User.email == "test_ws@adam.com").first()
    if not user:
        user = User(name="Test WS", email="test_ws@adam.com", hashed_password="fake", is_active=True)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    token = create_access_token({"sub": user.email})
    
    # Try connecting with valid token
    with client.websocket_connect(f"/notifications/ws?token={token}") as websocket:
        # Here we manually trigger a broadcast using the notifier to see if the client receives it
        from app.core.websockets.manager import notifier
        import asyncio
        
        # Test sending personal message
        payload = {"message": "Hello WS Test"}
        # Since we are in sync land in TestClient, we can use an event loop to run async
        loop = asyncio.get_event_loop()
        loop.run_until_complete(notifier.send_personal_message(user.id, payload))
        
        data = websocket.receive_json()
        assert data["message"] == "Hello WS Test"

