from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import datetime

# Connection to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['privacy_policy_generator']
users_collection = db['users']
policies_collection = db['policies']

# Create unique index for username
users_collection.create_index("username", unique=True)

# User functions
def create_user(username, password, name, email):
    """Create a new user with hashed password"""
    if users_collection.find_one({"username": username}):
        return False, "Username already exists"
    
    new_user = {
        "username": username,
        "password": generate_password_hash(password),
        "name": name,
        "email": email,
        "created_at": datetime.datetime.now(),
        "last_login": datetime.datetime.now()
    }
    
    result = users_collection.insert_one(new_user)
    return True, str(result.inserted_id)

def validate_user(username, password):
    """Validate user credentials"""
    user = users_collection.find_one({"username": username})
    if user and check_password_hash(user["password"], password):
        users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.datetime.now()}}
        )
        return True, user
    return False, None

def update_user_profile(user_id, name, email, password=None):
    """Update user profile information"""
    update_data = {
        "name": name,
        "email": email,
        "updated_at": datetime.datetime.now()
    }
    
    if password:
        update_data["password"] = generate_password_hash(password)
    
    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    return True

def get_user(user_id):
    """Get user by ID"""
    return users_collection.find_one({"_id": ObjectId(user_id)})

# Policy functions
def create_policy(user_id, website_name, website_url, data_collected, third_party_sharing, 
                 gdpr_compliant, ccpa_compliant, vulnerability_score, policy_text):
    """Create a new privacy policy"""
    new_policy = {
        "user_id": ObjectId(user_id),
        "website_name": website_name,
        "website_url": website_url,
        "data_collected": data_collected,
        "third_party_sharing": third_party_sharing,
        "gdpr_compliant": gdpr_compliant,
        "ccpa_compliant": ccpa_compliant,
        "vulnerability_score": vulnerability_score,
        "policy_text": policy_text,
        "created_at": datetime.datetime.now(),
        "updated_at": datetime.datetime.now()
    }
    
    result = policies_collection.insert_one(new_policy)
    return str(result.inserted_id)

def get_user_policies(user_id):
    """Get all policies for a user"""
    return list(policies_collection.find({"user_id": ObjectId(user_id)}).sort("created_at", -1))

def get_policy(policy_id):
    """Get a specific policy by ID"""
    return policies_collection.find_one({"_id": ObjectId(policy_id)})

def update_policy(policy_id, website_name, website_url, data_collected, third_party_sharing, 
                 gdpr_compliant, ccpa_compliant, vulnerability_score, policy_text):
    """Update an existing policy"""
    policies_collection.update_one(
        {"_id": ObjectId(policy_id)},
        {"$set": {
            "website_name": website_name,
            "website_url": website_url,
            "data_collected": data_collected,
            "third_party_sharing": third_party_sharing,
            "gdpr_compliant": gdpr_compliant,
            "ccpa_compliant": ccpa_compliant,
            "vulnerability_score": vulnerability_score,
            "policy_text": policy_text,
            "updated_at": datetime.datetime.now()
        }}
    )
    return True

def delete_policy(policy_id):
    """Delete a policy"""
    policies_collection.delete_one({"_id": ObjectId(policy_id)})
    return True