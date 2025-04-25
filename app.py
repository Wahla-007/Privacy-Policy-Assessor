from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
import conn
import os
import io
from functools import wraps
import json
import datetime
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a random string in production

# Custom JSON encoder to handle ObjectId and datetime
class MongoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        if isinstance(obj, ObjectId):
            return str(obj)
        return super(MongoJSONEncoder, self).default(obj)

app.json_encoder = MongoJSONEncoder

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
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        success, user = conn.validate_user(username, password)
        if success:
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            session['name'] = user['name']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        email = request.form.get('email')
        
        success, message = conn.create_user(username, password, name, email)
        if success:
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash(message, 'error')
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    policies = conn.get_user_policies(user_id)
    return render_template('dashboard.html', policies=policies)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = session['user_id']
    user = conn.get_user(user_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if password and len(password.strip()) > 0:
            conn.update_user_profile(user_id, name, email, password)
        else:
            conn.update_user_profile(user_id, name, email)
        
        session['name'] = name
        flash('Profile updated successfully', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile.html', user=user)

@app.route('/policy/new', methods=['GET', 'POST'])
@login_required
def new_policy():
    if request.method == 'POST':
        # Extract form data
        website_name = request.form.get('website_name')
        website_url = request.form.get('website_url')
        data_collected = request.form.getlist('data_collected')
        third_party_sharing = request.form.get('third_party_sharing') == 'yes'
        
        # Calculate GDPR and CCPA compliance
        gdpr_compliant = evaluate_gdpr_compliance(request.form)
        ccpa_compliant = evaluate_ccpa_compliance(request.form)
        
        # Calculate vulnerability score
        vulnerability_score = calculate_vulnerability_score(request.form)
        
        # Generate policy text
        policy_text = generate_privacy_policy(
            website_name, 
            website_url, 
            data_collected, 
            third_party_sharing, 
            gdpr_compliant, 
            ccpa_compliant,
            request.form
        )
        
        # Save policy
        policy_id = conn.create_policy(
            session['user_id'],
            website_name,
            website_url,
            data_collected,
            third_party_sharing,
            gdpr_compliant,
            ccpa_compliant,
            vulnerability_score,
            policy_text
        )
        
        flash('Privacy policy generated successfully', 'success')
        return redirect(url_for('view_policy', policy_id=policy_id))
    
    return render_template('policy_generator.html')

@app.route('/policy/<policy_id>')
@login_required
def view_policy(policy_id):
    policy = conn.get_policy(policy_id)
    if not policy or str(policy['user_id']) != session['user_id']:
        flash('Policy not found or access denied', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('policy_view.html', policy=policy)

@app.route('/policy/<policy_id>/download')
@login_required
def download_policy(policy_id):
    policy = conn.get_policy(policy_id)
    if not policy or str(policy['user_id']) != session['user_id']:
        flash('Policy not found or access denied', 'error')
        return redirect(url_for('dashboard'))
    
    # Create policy text file
    policy_text = policy['policy_text']
    filename = f"{policy['website_name'].replace(' ', '_').lower()}_privacy_policy.txt"
    
    # Return file for download
    return send_file(
        io.BytesIO(policy_text.encode('utf-8')),
        mimetype='text/plain',
        as_attachment=True,
        download_name=filename
    )

@app.route('/policy/<policy_id>/delete', methods=['POST'])
@login_required
def delete_policy(policy_id):
    policy = conn.get_policy(policy_id)
    if not policy or str(policy['user_id']) != session['user_id']:
        flash('Policy not found or access denied', 'error')
        return redirect(url_for('dashboard'))
    
    conn.delete_policy(policy_id)
    flash('Privacy policy deleted successfully', 'success')
    return redirect(url_for('dashboard'))

# Helper functions for policy generation
def evaluate_gdpr_compliance(form_data):
    # Logic to evaluate GDPR compliance based on responses
    compliant = True
    
    # Example checks (these would be more comprehensive in a real application)
    if 'consent_mechanism' not in form_data or form_data['consent_mechanism'] != 'explicit':
        compliant = False
    
    if 'data_retention' not in form_data or form_data['data_retention'] == 'indefinite':
        compliant = False
    
    if 'user_rights' not in form_data or 'right_to_erasure' not in form_data.getlist('user_rights'):
        compliant = False
        
    return compliant

def evaluate_ccpa_compliance(form_data):
    # Logic to evaluate CCPA compliance based on responses
    compliant = True
    
    # Example checks
    if 'opt_out_option' not in form_data or form_data['opt_out_option'] != 'yes':
        compliant = False
    
    if 'data_sale' in form_data and form_data['data_sale'] == 'yes' and 'do_not_sell' not in form_data:
        compliant = False
        
    return compliant

def calculate_vulnerability_score(form_data):
    # Calculate vulnerability score (0-100)
    # Higher scores mean better security/privacy practices
    score = 50  # Start with a neutral score
    
    # Data minimization
    if 'data_minimization' in form_data and form_data['data_minimization'] == 'yes':
        score += 10
    
    # Encryption
    if 'encryption' in form_data:
        if form_data['encryption'] == 'all':
            score += 15
        elif form_data['encryption'] == 'partial':
            score += 7
    
    # Data retention
    if 'data_retention' in form_data:
        if form_data['data_retention'] == 'specific_purpose':
            score += 10
        elif form_data['data_retention'] == 'limited_time':
            score += 5
    
    # Third-party sharing
    if 'third_party_sharing' in form_data and form_data['third_party_sharing'] == 'no':
        score += 15
    
    # Data breach procedure
    if 'breach_procedure' in form_data and form_data['breach_procedure'] == 'yes':
        score += 10
    
    # Children's data
    if 'collects_children_data' in form_data and form_data['collects_children_data'] == 'no':
        score += 10
    
    # Ensure score is within bounds
    return max(0, min(score, 100))

def generate_privacy_policy(website_name, website_url, data_collected, third_party_sharing, gdpr_compliant, ccpa_compliant, form_data):
    # Generate a tailored privacy policy based on responses
    policy = f"""PRIVACY POLICY FOR {website_name.upper()}

Last Updated: {datetime.datetime.now().strftime('%B %d, %Y')}

1. INTRODUCTION

Welcome to {website_name} ({website_url}). We respect your privacy and are committed to protecting your personal data. This Privacy Policy will inform you about how we look after your personal data when you visit our website and tell you about your privacy rights and how the law protects you.

2. DATA WE COLLECT

We collect the following types of information:
"""

    # Add data collected
    for data_type in data_collected:
        policy += f"- {data_type}\n"
    
    # Third-party sharing
    policy += "\n3. SHARING YOUR INFORMATION\n\n"
    if third_party_sharing:
        policy += "We share your personal information with selected third parties to help us provide our services. These third parties are required to respect the security of your personal data and to treat it in accordance with the law.\n"
    else:
        policy += "We do not share your personal information with any third parties except where required by law.\n"
    
    # User rights
    policy += "\n4. YOUR RIGHTS\n\n"
    policy += "You have the right to:\n"
    policy += "- Access your personal data\n"
    policy += "- Request correction of your personal data\n"
    
    if 'user_rights' in form_data:
        if 'right_to_erasure' in form_data.getlist('user_rights'):
            policy += "- Request erasure of your personal data\n"
        if 'data_portability' in form_data.getlist('user_rights'):
            policy += "- Request the transfer of your personal data\n"
        if 'restrict_processing' in form_data.getlist('user_rights'):
            policy += "- Object to processing of your personal data\n"
    
    # Data security
    policy += "\n5. DATA SECURITY\n\n"
    if 'encryption' in form_data:
        if form_data['encryption'] == 'all':
            policy += "We have put in place appropriate security measures to prevent your personal data from being accidentally lost, used or accessed in an unauthorized way, altered or disclosed. All data is encrypted both in transit and at rest.\n"
        elif form_data['encryption'] == 'partial':
            policy += "We have put in place security measures to protect your personal data. Sensitive information is encrypted during transmission.\n"
        else:
            policy += "We have put in place basic security measures to protect your personal data.\n"
    
    # Retention period
    policy += "\n6. DATA RETENTION\n\n"
    if 'data_retention' in form_data:
        if form_data['data_retention'] == 'specific_purpose':
            policy += "We will only retain your personal data for as long as necessary to fulfill the purposes for which we collected it.\n"
        elif form_data['data_retention'] == 'limited_time':
            policy += "We will retain your personal data for a limited period as specified in our internal policies.\n"
        else:
            policy += "We retain your personal data in accordance with our internal policies.\n"
    
    # Children's privacy
    policy += "\n7. CHILDREN'S PRIVACY\n\n"
    if 'collects_children_data' in form_data and form_data['collects_children_data'] == 'yes':
        policy += "Our service may collect data from children under 13 with parental consent. We implement additional protections to ensure compliance with applicable laws like COPPA.\n"
    else:
        policy += "Our service is not directed at children under 13. We do not knowingly collect personal data from children under 13.\n"
    
    # Compliance information
    policy += "\n8. REGULATORY COMPLIANCE\n\n"
    if gdpr_compliant:
        policy += "This privacy policy is designed to comply with the General Data Protection Regulation (GDPR).\n"
    else:
        policy += "This privacy policy may not fully comply with all requirements of the General Data Protection Regulation (GDPR).\n"
    
    if ccpa_compliant:
        policy += "This privacy policy is designed to comply with the California Consumer Privacy Act (CCPA).\n"
    else:
        policy += "This privacy policy may not fully comply with all requirements of the California Consumer Privacy Act (CCPA).\n"
    
    # Contact information
    policy += "\n9. CONTACT US\n\n"
    policy += f"If you have any questions about this Privacy Policy, please contact us at [CONTACT EMAIL] or visit {website_url}.\n"
    
    return policy

if __name__ == '__main__':
    app.run(debug=True)