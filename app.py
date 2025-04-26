# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta
from functools import wraps
from pymongo import MongoClient
from bson.objectid import ObjectId
# import markdown
from markupsafe import Markup

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.permanent_session_lifetime = timedelta(days=7)

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['privacy_policy_generator']
users_collection = db['users']
policies_collection = db['policies']

# Ensure indexes
users_collection.create_index("username", unique=True)
users_collection.create_index("email", unique=True)

# Custom markdown filter
@app.template_filter('markdown')
def render_markdown(text):
    return Markup(markdown.markdown(text))

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        name = request.form.get('name')
        email = request.form.get('email')
        
        # Validate input
        if not all([username, password, confirm_password, name, email]):
            flash('All fields are required', 'error')
            return render_template('signup.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('signup.html')
        
        # Check if username exists
        if users_collection.find_one({"username": username}):
            flash('Username already exists', 'error')
            return render_template('signup.html')
        
        # Check if email exists
        if users_collection.find_one({"email": email}):
            flash('Email already exists', 'error')
            return render_template('signup.html')
        
        # Create new user
        new_user = {
            "username": username,
            "password": generate_password_hash(password),
            "name": name,
            "email": email,
            "created_at": datetime.utcnow(),
            "last_login": datetime.utcnow()
        }
        
        result = users_collection.insert_one(new_user)
        
        if result.inserted_id:
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Something went wrong. Please try again.', 'error')
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        
        user = users_collection.find_one({"username": username})
        
        if user and check_password_hash(user["password"], password):
            # Update last login
            users_collection.update_one(
                {"_id": user["_id"]},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            
            # Set session
            session.permanent = remember
            session['user_id'] = str(user["_id"])
            session['username'] = user["username"]
            session['name'] = user["name"]
            
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('name', None)
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session.get('user_id')
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    
    # Get count of user's policies
    policy_count = policies_collection.count_documents({"user_id": user_id})
    
    return render_template('dashboard.html', user=user, policy_count=policy_count)

@app.route('/create-policy', methods=['GET', 'POST'])
@login_required
def create_policy():
    if request.method == 'POST':
        # Get form data
        website_name = request.form.get('website_name')
        website_url = request.form.get('website_url')
        company_name = request.form.get('company_name')
        contact_email = request.form.get('contact_email')
        
        # Compliance options
        gdpr_compliant = request.form.get('gdpr_compliant') == 'on'
        ccpa_compliant = request.form.get('ccpa_compliant') == 'on'
        
        # Data collection options
        collects_personal_info = request.form.get('collects_personal_info') == 'on'
        collects_cookies = request.form.get('collects_cookies') == 'on'
        shares_data = request.form.get('shares_data') == 'on'
        uses_analytics = request.form.get('uses_analytics') == 'on'
        
        # Create policy document
        policy_content = generate_privacy_policy(
            website_name, website_url, company_name, contact_email,
            gdpr_compliant, ccpa_compliant, collects_personal_info,
            collects_cookies, shares_data, uses_analytics
        )
        
        # Save policy to database
        new_policy = {
            "user_id": session.get('user_id'),
            "website_name": website_name,
            "website_url": website_url,
            "company_name": company_name,
            "content": policy_content,
            "created_at": datetime.utcnow(),
            "last_updated": datetime.utcnow(),
            "gdpr_compliant": gdpr_compliant,
            "ccpa_compliant": ccpa_compliant
        }
        
        result = policies_collection.insert_one(new_policy)
        
        if result.inserted_id:
            flash('Privacy policy created successfully!', 'success')
            return redirect(url_for('view_policy', policy_id=str(result.inserted_id)))
        else:
            flash('Something went wrong. Please try again.', 'error')
    
    return render_template('create_policy.html')

@app.route('/my-policies')
@login_required
def my_policies():
    user_id = session.get('user_id')
    policies = policies_collection.find({"user_id": user_id}).sort("created_at", -1)
    return render_template('my_policies.html', policies=policies)

@app.route('/policy/<policy_id>')
@login_required
def view_policy(policy_id):
    user_id = session.get('user_id')
    policy = policies_collection.find_one({"_id": ObjectId(policy_id), "user_id": user_id})
    
    if not policy:
        flash('Policy not found or you do not have permission to view it', 'error')
        return redirect(url_for('my_policies'))
    
    return render_template('view_policy.html', policy=policy)

def generate_privacy_policy(website_name, website_url, company_name, contact_email,
                          gdpr_compliant, ccpa_compliant, collects_personal_info,
                          collects_cookies, shares_data, uses_analytics):
    """Generate a privacy policy based on provided information"""
    
    # Base policy content
    policy = f"""# Privacy Policy for {website_name}

## Last Updated: {datetime.now().strftime('%B %d, %Y')}

### Introduction

Welcome to {website_name}. This Privacy Policy explains how {company_name} ("we", "us", or "our") collects, uses, and discloses your information when you use our website {website_url} (the "Service").

We respect your privacy and are committed to protecting your personal data. Please read this Privacy Policy carefully to understand how we handle your information.

### Information We Collect

"""
    
    # Add sections based on collected information
    if collects_personal_info:
        policy += """We may collect personal information that you provide directly to us, such as:
- Name
- Email address
- Phone number
- Billing and shipping address
- Payment information
- Any other information you choose to provide

"""
    else:
        policy += """We do not collect personally identifiable information unless you voluntarily provide it to us.

"""
    
    if collects_cookies:
        policy += """### Cookies and Tracking Technologies

We use cookies and similar tracking technologies to track activity on our Service and hold certain information. Cookies are files with a small amount of data which may include an anonymous unique identifier.

You can instruct your browser to refuse all cookies or to indicate when a cookie is being sent. However, if you do not accept cookies, you may not be able to use some portions of our Service.

"""
    
    if uses_analytics:
        policy += """### Analytics

We may use third-party Service Providers to monitor and analyze the use of our Service, such as:
- Google Analytics
- Facebook Pixel
- Other analytics services

"""
    
    if shares_data:
        policy += """### Sharing Your Information

We may share your personal information with:
- Service providers who perform services on our behalf
- Business partners with whom we jointly offer products or services
- As required by law or to comply with legal process
- To protect and defend our rights and property

"""
    
    # Add compliance sections
    if gdpr_compliant:
        policy += f"""### GDPR Compliance

For users in the European Union (EU) and European Economic Area (EEA), we process your data in accordance with the General Data Protection Regulation (GDPR). You have the following rights:
- Right to access your personal data
- Right to rectification if your data is inaccurate or incomplete
- Right to erasure (right to be forgotten)
- Right to restrict processing
- Right to data portability
- Right to object to processing
- Rights in relation to automated decision making and profiling

To exercise these rights, please contact us at {contact_email}.

"""
    
    if ccpa_compliant:
        policy += f"""### CCPA Compliance

For California residents, the California Consumer Privacy Act (CCPA) provides you with specific rights regarding your personal information. You have the right to:
- Know what personal information is being collected about you
- Know whether your personal information is sold or disclosed and to whom
- Opt out of the sale of your personal information
- Access your personal information
- Request deletion of your personal information
- Not be discriminated against for exercising your CCPA rights

To exercise these rights, please contact us at {contact_email}.

"""
    
    # Contact information
    policy += f"""### Contact Us

If you have any questions about this Privacy Policy, please contact us at:
- Email: {contact_email}
- Website: {website_url}
- Company: {company_name}

"""
    
    return policy

if __name__ == '__main__':
    app.run(debug=True)