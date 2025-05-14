import os
import json
import hashlib
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get admin password from environment variable
admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
print(f"Using admin password from .env: {admin_password}")

# Create storage directory if it doesn't exist
storage_dir = os.path.join(os.path.dirname(__file__), 'storage')
os.makedirs(storage_dir, exist_ok=True)

# Path to users.json
users_db_path = os.path.join(storage_dir, 'users.json')

# Generate salt and hash password
salt = uuid.uuid4().hex
hashed_password = hashlib.sha256((admin_password + salt).encode()).hexdigest()

# Create admin user
users = {
    "admin": {
        "username": "admin",
        "salt": salt,
        "hashed_password": hashed_password,
        "is_admin": True,
        "created_at": datetime.now().isoformat()
    }
}

# Save to file
with open(users_db_path, 'w') as f:
    json.dump(users, f, indent=2)

print(f"Created users.json with admin user at: {users_db_path}")
print("You can now log in with username 'admin' and your configured password.") 