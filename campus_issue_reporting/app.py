import os
import re
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, send_from_directory, g
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from pymongo import MongoClient, ReturnDocument

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# MongoDB Atlas Connection URI
MONGO_URI = "mongodb+srv://tamilselvan30112006_db_user:Tamil%402006@cluster1.jkll2sg.mongodb.net/campus_db?retryWrites=true&w=majority"

app = Flask(__name__)
app.secret_key = 'campus_issue_tracking_secret_key_2026'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ----------------------------------------------------
# DATABASE HELPERS (PyMongo)
# ----------------------------------------------------

_mongo_client = None

def get_db():
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(MONGO_URI)
    return _mongo_client['campus_db']

def get_next_sequence(name):
    db = get_db()
    counter = db.counters.find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    return counter["seq"]

def init_db():
    db = get_db()
    # Create unique index on username
    db.users.create_index("username", unique=True)
    db.users.create_index("id", unique=True)
    db.issues.create_index("id", unique=True)

    # Seed default accounts if users collection is empty
    if db.users.count_documents({}) == 0:
        default_manager_pwd = generate_password_hash("manager123")
        default_maint_pwd = generate_password_hash("maintenance123")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        db.users.insert_one({
            "id": 1,
            "name": "Campus Manager",
            "username": "manager",
            "password": default_manager_pwd,
            "role": "Manager",
            "created_at": now_str
        })
        db.users.insert_one({
            "id": 2,
            "name": "Maintenance Staff",
            "username": "maintenance",
            "password": default_maint_pwd,
            "role": "Maintenance Staff",
            "created_at": now_str
        })

        db.counters.update_one({"_id": "user_id"}, {"$set": {"seq": 2}}, upsert=True)
        print("MongoDB Atlas database initialized and demo accounts created.")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ----------------------------------------------------
# AUTH & ACCESS DECORATORS
# ----------------------------------------------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def roles_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for('login'))
            if session.get('role') not in roles:
                flash("Access denied: You do not have permission to view that page.", "danger")
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.context_processor
def inject_global_data():
    if 'user_id' in session:
        db = get_db()
        unread_count = db.notifications.count_documents({
            "user_id": session['user_id'],
            "is_read": 0
        })
        return dict(unread_notifications_count=unread_count, current_user=session)
    return dict(unread_notifications_count=0, current_user=None)

# ----------------------------------------------------
# ROUTES
# ----------------------------------------------------

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash("Please fill in all fields.", "danger")
            return render_template('login.html')

        db = get_db()
        user = db.users.find_one({"username": username})

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['name'] = user['name']
            session['role'] = user['role']

            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password.", "danger")

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', '').strip()

        if not name or not username or not password or not role:
            flash("All required fields must be completed.", "danger")
            return render_template('register.html')

        valid_roles = ['Student', 'Faculty', 'Maintenance Staff', 'Technician']
        if role not in valid_roles:
            flash("Invalid account type selected.", "danger")
            return render_template('register.html')

        # Map Technician to Maintenance Staff role for system compatibility
        if role == 'Technician':
            role = 'Maintenance Staff'

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('register.html')

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template('register.html')

        db = get_db()
        if db.users.find_one({"username": username}):
            flash("Username is already taken. Please choose another.", "danger")
            return render_template('register.html')

        new_user_id = get_next_sequence("user_id")
        hashed_pwd = generate_password_hash(password)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        db.users.insert_one({
            "id": new_user_id,
            "name": name,
            "username": username,
            "password": hashed_pwd,
            "role": role,
            "created_at": now_str
        })

        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    role = session['role']
    user_id = session['user_id']

    stats = {
        'total': 0,
        'pending': 0,
        'assigned': 0,
        'in_progress': 0,
        'resolved': 0
    }
    recent_issues = []
    maintenance_staff_list = []

    if role in ['Student', 'Faculty']:
        stats['total'] = db.issues.count_documents({"user_id": user_id})
        stats['pending'] = db.issues.count_documents({"user_id": user_id, "status": "Pending"})
        stats['in_progress'] = db.issues.count_documents({"user_id": user_id, "status": "In Progress"})
        stats['resolved'] = db.issues.count_documents({"user_id": user_id, "status": "Resolved"})

        cursor = db.issues.find({"user_id": user_id}).sort("created_at", -1).limit(5)
        recent_issues = list(cursor)

    elif role == 'Manager':
        stats['total'] = db.issues.count_documents({})
        stats['pending'] = db.issues.count_documents({"status": "Pending"})
        stats['assigned'] = db.issues.count_documents({"status": "Assigned"})
        stats['in_progress'] = db.issues.count_documents({"status": "In Progress"})
        stats['resolved'] = db.issues.count_documents({"status": "Resolved"})

        cursor = db.issues.find({}).sort("created_at", -1).limit(8)
        recent_issues = list(cursor)

        maintenance_staff_list = list(db.users.find({"role": "Maintenance Staff"}).sort("name", 1))

    elif role == 'Maintenance Staff':
        stats['total'] = db.issues.count_documents({})
        stats['pending'] = db.issues.count_documents({"status": "Pending"})
        stats['assigned'] = db.issues.count_documents({"assigned_to": user_id})
        stats['in_progress'] = db.issues.count_documents({"status": "In Progress"})
        stats['resolved'] = db.issues.count_documents({"status": "Resolved"})

        cursor = db.issues.find({}).sort("created_at", -1).limit(8)
        recent_issues = list(cursor)
        maintenance_staff_list = list(db.users.find({"role": "Maintenance Staff"}).sort("name", 1))

    # Attach assigned staff names
    for issue in recent_issues:
        if issue.get('assigned_to'):
            staff_user = db.users.find_one({"id": issue['assigned_to']})
            if staff_user:
                issue['assigned_staff_name'] = staff_user['name']

    return render_template(
        'dashboard.html',
        stats=stats,
        recent_issues=recent_issues,
        maintenance_staff_list=maintenance_staff_list
    )

@app.route('/report', methods=['GET', 'POST'])
@roles_required('Student', 'Faculty')
def report_issue():
    if request.method == 'POST':
        category = request.form.get('category', '').strip()
        location = request.form.get('location', '').strip()
        description = request.form.get('description', '').strip()
        priority = request.form.get('priority', 'Medium').strip()
        image = request.files.get('image')

        if not category or not location or not description:
            flash("Category, Location, and Description are required fields.", "danger")
            return render_template('report_issue.html')

        if priority not in ['Low', 'Medium', 'High', 'Urgent']:
            priority = 'Medium'

        image_filename = None
        if image and image.filename != '':
            if allowed_file(image.filename):
                filename = secure_filename(image.filename)
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                image_filename = f"{timestamp_str}_{filename}"
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
                image.save(save_path)
            else:
                flash("Invalid image file format. Allowed: PNG, JPG, JPEG, GIF, WEBP.", "danger")
                return render_template('report_issue.html')

        db = get_db()
        issue_id = get_next_sequence("issue_id")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        db.issues.insert_one({
            "id": issue_id,
            "user_id": session['user_id'],
            "student_name": session['name'],
            "category": category,
            "location": location,
            "description": description,
            "priority": priority,
            "status": "Pending",
            "assigned_to": None,
            "image_path": image_filename,
            "created_at": now_str,
            "updated_at": now_str
        })

        # Insert initial issue_history record
        db.issue_history.insert_one({
            "id": get_next_sequence("history_id"),
            "issue_id": issue_id,
            "status": "Pending",
            "updated_by": session['user_id'],
            "updated_by_name": session['name'],
            "updated_by_role": session['role'],
            "remarks": "Issue reported by user.",
            "updated_at": now_str
        })

        flash(f"Issue #{issue_id} reported successfully!", "success")
        return redirect(url_for('my_issues'))

    return render_template('report_issue.html')

@app.route('/my-issues')
@roles_required('Student', 'Faculty')
def my_issues():
    db = get_db()
    issues = list(db.issues.find({"user_id": session['user_id']}).sort("created_at", -1))
    
    for issue in issues:
        if issue.get('assigned_to'):
            staff = db.users.find_one({"id": issue['assigned_to']})
            if staff:
                issue['assigned_staff_name'] = staff['name']

    return render_template('my_issues.html', issues=issues)

@app.route('/all-issues')
@roles_required('Manager', 'Maintenance Staff')
def all_issues():
    db = get_db()

    search_query = request.args.get('q', '').strip()
    category_filter = request.args.get('category', '').strip()
    status_filter = request.args.get('status', '').strip()
    priority_filter = request.args.get('priority', '').strip()

    filter_dict = {}

    if search_query:
        regex = re.compile(re.escape(search_query), re.IGNORECASE)
        try:
            query_id = int(search_query)
            filter_dict["$or"] = [
                {"id": query_id},
                {"student_name": regex},
                {"category": regex},
                {"location": regex},
                {"description": regex}
            ]
        except ValueError:
            filter_dict["$or"] = [
                {"student_name": regex},
                {"category": regex},
                {"location": regex},
                {"description": regex}
            ]

    if category_filter:
        filter_dict["category"] = category_filter

    if status_filter:
        filter_dict["status"] = status_filter

    if priority_filter:
        filter_dict["priority"] = priority_filter

    issues = list(db.issues.find(filter_dict).sort("created_at", -1))

    for issue in issues:
        if issue.get('assigned_to'):
            staff = db.users.find_one({"id": issue['assigned_to']})
            if staff:
                issue['assigned_staff_name'] = staff['name']
        
        reporter = db.users.find_one({"id": issue['user_id']})
        if reporter:
            issue['reporter_role'] = reporter.get('role', '')

    staff_members = list(db.users.find({"role": "Maintenance Staff"}).sort("name", 1))

    return render_template(
        'all_issues.html',
        issues=issues,
        staff_members=staff_members,
        search_query=search_query,
        category_filter=category_filter,
        status_filter=status_filter,
        priority_filter=priority_filter
    )

@app.route('/issue/<int:issue_id>')
@login_required
def issue_details(issue_id):
    db = get_db()
    issue = db.issues.find_one({"id": issue_id})

    if not issue:
        flash("Issue not found.", "danger")
        return redirect(url_for('dashboard'))

    role = session['role']
    user_id = session['user_id']

    if role in ['Student', 'Faculty'] and issue['user_id'] != user_id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('my_issues'))

    # Attach reporter and staff details
    if issue.get('assigned_to'):
        staff = db.users.find_one({"id": issue['assigned_to']})
        if staff:
            issue['assigned_staff_name'] = staff['name']

    reporter = db.users.find_one({"id": issue['user_id']})
    if reporter:
        issue['reporter_name'] = reporter['name']
        issue['reporter_username'] = reporter['username']
        issue['reporter_role'] = reporter['role']

    history = list(db.issue_history.find({"issue_id": issue_id}).sort("updated_at", 1))

    maintenance_staff_list = []
    if role in ['Manager', 'Maintenance Staff']:
        maintenance_staff_list = list(db.users.find({"role": "Maintenance Staff"}).sort("name", 1))

    return render_template(
        'issue_details.html',
        issue=issue,
        history=history,
        maintenance_staff_list=maintenance_staff_list
    )

@app.route('/issue/<int:issue_id>/assign', methods=['POST'])
@roles_required('Manager', 'Maintenance Staff')
def assign_issue(issue_id):
    staff_id_str = request.form.get('assigned_to')
    remarks = request.form.get('remarks', '').strip()

    if not staff_id_str:
        flash("Please select a maintenance staff member / technician.", "danger")
        return redirect(url_for('issue_details', issue_id=issue_id))

    staff_id = int(staff_id_str)
    db = get_db()
    issue = db.issues.find_one({"id": issue_id})
    if not issue:
        flash("Issue not found.", "danger")
        return redirect(url_for('all_issues'))

    staff = db.users.find_one({"id": staff_id, "role": "Maintenance Staff"})
    if not staff:
        flash("Invalid technician / maintenance staff selected.", "danger")
        return redirect(url_for('issue_details', issue_id=issue_id))

    new_status = 'Assigned' if issue['status'] == 'Pending' else issue['status']
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    db.issues.update_one(
        {"id": issue_id},
        {"$set": {"assigned_to": staff_id, "status": new_status, "updated_at": now_str}}
    )

    assign_remark = f"Assigned to {staff['name']}." + (f" Note: {remarks}" if remarks else "")
    db.issue_history.insert_one({
        "id": get_next_sequence("history_id"),
        "issue_id": issue_id,
        "status": new_status,
        "updated_by": session['user_id'],
        "updated_by_name": session['name'],
        "updated_by_role": session['role'],
        "remarks": assign_remark,
        "updated_at": now_str
    })

    # Notify Maintenance Staff
    maint_msg = f"Issue #{issue_id} ('{issue['category']} - {issue['location']}') has been assigned to you."
    db.notifications.insert_one({
        "id": get_next_sequence("notification_id"),
        "user_id": staff_id,
        "issue_id": issue_id,
        "message": maint_msg,
        "is_read": 0,
        "created_at": now_str
    })

    # Notify Reporter
    reporter_msg = f"Your issue #{issue_id} has been assigned to technician / maintenance staff ({staff['name']})."
    db.notifications.insert_one({
        "id": get_next_sequence("notification_id"),
        "user_id": issue['user_id'],
        "issue_id": issue_id,
        "message": reporter_msg,
        "is_read": 0,
        "created_at": now_str
    })

    flash(f"Issue #{issue_id} assigned to {staff['name']}.", "success")
    return redirect(url_for('issue_details', issue_id=issue_id))

@app.route('/issue/<int:issue_id>/update-status', methods=['POST'])
@login_required
def update_issue_status(issue_id):
    role = session['role']
    user_id = session['user_id']

    if role not in ['Manager', 'Maintenance Staff']:
        flash("Unauthorized action.", "danger")
        return redirect(url_for('dashboard'))

    new_status = request.form.get('status', '').strip()
    new_priority = request.form.get('priority', '').strip()
    remarks = request.form.get('remarks', '').strip()

    valid_statuses = ['Pending', 'Assigned', 'In Progress', 'Resolved']
    if new_status not in valid_statuses:
        flash("Invalid status selection.", "danger")
        return redirect(url_for('issue_details', issue_id=issue_id))

    db = get_db()
    issue = db.issues.find_one({"id": issue_id})
    if not issue:
        flash("Issue not found.", "danger")
        return redirect(url_for('dashboard'))

    priority_to_set = issue['priority']
    if role == 'Manager' and new_priority in ['Low', 'Medium', 'High', 'Urgent']:
        priority_to_set = new_priority

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # If Technician/Maintenance updates an unassigned issue, automatically assign to them!
    assigned_to_set = issue.get('assigned_to')
    if role == 'Maintenance Staff' and not assigned_to_set:
        assigned_to_set = user_id
        if new_status == 'Pending':
            new_status = 'In Progress'

    db.issues.update_one(
        {"id": issue_id},
        {"$set": {"status": new_status, "priority": priority_to_set, "assigned_to": assigned_to_set, "updated_at": now_str}}
    )

    remark_entry = remarks if remarks else f"Status updated to '{new_status}'."
    db.issue_history.insert_one({
        "id": get_next_sequence("history_id"),
        "issue_id": issue_id,
        "status": new_status,
        "updated_by": user_id,
        "updated_by_name": session['name'],
        "updated_by_role": session['role'],
        "remarks": remark_entry,
        "updated_at": now_str
    })

    # Send Notification to Reporter
    reporter_msg = f"Your issue #{issue_id} status has been updated to '{new_status}'."
    if new_status == 'Resolved':
        reporter_msg = f"Your issue #{issue_id} has been marked as Resolved!"
    elif new_status == 'In Progress':
        reporter_msg = f"Work has started on your issue #{issue_id} (In Progress)."

    db.notifications.insert_one({
        "id": get_next_sequence("notification_id"),
        "user_id": issue['user_id'],
        "issue_id": issue_id,
        "message": reporter_msg,
        "is_read": 0,
        "created_at": now_str
    })

    flash(f"Status of Issue #{issue_id} updated to '{new_status}'.", "success")
    return redirect(url_for('issue_details', issue_id=issue_id))


@app.route('/issue/<int:issue_id>/delete', methods=['POST'])
@roles_required('Manager')
def delete_issue(issue_id):
    db = get_db()
    if not db.issues.find_one({"id": issue_id}):
        flash("Issue not found.", "danger")
        return redirect(url_for('all_issues'))

    db.issues.delete_one({"id": issue_id})
    db.issue_history.delete_many({"issue_id": issue_id})
    db.notifications.delete_many({"issue_id": issue_id})

    flash(f"Issue #{issue_id} deleted successfully.", "info")
    return redirect(url_for('all_issues'))

@app.route('/notifications')
@login_required
def notifications():
    db = get_db()
    notifications_list = list(db.notifications.find({"user_id": session['user_id']}).sort("created_at", -1))
    return render_template('notifications.html', notifications=notifications_list)

@app.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    db = get_db()
    db.notifications.update_many({"user_id": session['user_id']}, {"$set": {"is_read": 1}})
    flash("All notifications marked as read.", "success")
    return redirect(url_for('notifications'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    db = get_db()
    user_id = session['user_id']

    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not current_password or not new_password or not confirm_password:
            flash("All password fields are required to change password.", "danger")
            return redirect(url_for('profile'))

        if new_password != confirm_password:
            flash("New passwords do not match.", "danger")
            return redirect(url_for('profile'))

        if len(new_password) < 6:
            flash("New password must be at least 6 characters long.", "danger")
            return redirect(url_for('profile'))

        user = db.users.find_one({"id": user_id})
        if not user or not check_password_hash(user['password'], current_password):
            flash("Incorrect current password.", "danger")
            return redirect(url_for('profile'))

        hashed_pwd = generate_password_hash(new_password)
        db.users.update_one({"id": user_id}, {"$set": {"password": hashed_pwd}})

        flash("Password updated successfully!", "success")
        return redirect(url_for('profile'))

    user_details = db.users.find_one({"id": user_id})
    return render_template('profile.html', user_details=user_details)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ----------------------------------------------------
# MAIN APPLICATION LAUNCHER
# ----------------------------------------------------

if __name__ == '__main__':
    init_db()
    print("Starting Campus Issue Reporting & Tracking System (MongoDB Atlas Connected) on http://127.0.0.1:5000 ...")
    app.run(host='127.0.0.1', port=5000, debug=True)
