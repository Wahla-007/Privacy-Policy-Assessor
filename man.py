from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["privacy_policy_generator"]

# Create 'users' collection
users_collection = db["users"]

# Create 'policies' collection
policies_collection = db["policies"]

# Insert a sample user
user_data = {
    "username": "johndoe",
    "password": "hashed_password_here",  # Replace with actual hashed password
    "name": "John Doe",
    "email": "john@example.com",
    "created_at": datetime.utcnow(),
    "last_login": datetime.utcnow()
}
user_result = users_collection.insert_one(user_data)
user_id = user_result.inserted_id
print(f"Inserted user with _id: {user_id}")

# Insert a sample policy associated with the user
policy_data = {
    "user_id": user_id,
    "website_name": "Example Site",
    "website_url": "https://www.example.com",
    "data_collected": ["email", "name", "location"],
    "third_party_sharing": True,
    "gdpr_compliant": True,
    "ccpa_compliant": False,
    "vulnerability_score": 85,
    "policy_text": "This is a sample privacy policy.",
    "created_at": datetime.utcnow(),
    "updated_at": datetime.utcnow()
}
policy_result = policies_collection.insert_one(policy_data)
print(f"Inserted policy with _id: {policy_result.inserted_id}")
