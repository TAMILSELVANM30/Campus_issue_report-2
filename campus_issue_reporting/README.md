# CAMPUS ISSUE REPORTING & TRACKING SYSTEM

A complete, reliable, end-to-end web application for reporting, managing, and tracking campus infrastructure and maintenance issues. Built with Python Flask, SQLite, HTML5, CSS3, and Vanilla JavaScript.

---

## 🌟 Project Description
The **Campus Issue Reporting & Tracking System** enables Students and Faculty members to submit maintenance requests (electrical, plumbing, furniture, IT/network, cleaning, etc.) with location details, priority, and optional photos. 

Campus Managers can monitor all submitted issues via an interactive dashboard, search/filter issues, change priority, assign maintenance personnel, and update status. Maintenance Staff can view work orders assigned to them, update status progress, add resolution notes, and mark issues as Resolved. Every status update is permanently recorded in an audit trail (`issue_history`) and automatically sends database notifications to the reporter.

---

## ⚙️ Features
1. **User Authentication & Role-Based Access Control**:
   - Student & Faculty registration and login.
   - Manager & Maintenance Staff pre-seeded demo accounts.
   - Protected routes and session management with Werkzeug password hashing.
2. **Issue Reporting & Photo Upload**:
   - Structured form (Category, Location, Priority, Description).
   - Local file storage for optional image attachment (`uploads/`).
3. **Manager Operations**:
   - Dashboard with statistics cards & custom HTML5 canvas donut chart.
   - Multi-parameter search & filtering (Category, Status, Priority, Search Query).
   - Maintenance staff assignment & priority management.
   - Soft/hard issue deletion.
4. **Maintenance Staff Operations**:
   - Filtered view showing only assigned work orders.
   - Status updates (`In Progress`, `Resolved`) with mandatory resolution notes.
5. **Real-time Notifications**:
   - In-app notification system notifying users when issue status changes or work is assigned.
   - Unread badge counter in top navbar.
6. **Audit History & Status Timeline**:
   - Complete tracking log for every issue showing who changed status, when, and with what remarks.

---

## 💻 Technology Stack
- **Backend**: Python 3.10+ & Flask 3.0
- **Database**: SQLite3 (`campus.db`)
- **Frontend**: HTML5, CSS3 (Custom Responsive Styling), Vanilla JavaScript
- **Template Engine**: Jinja2
- **Offline Charting**: Pure HTML5 2D Canvas

---

## 📁 Folder Structure
```
campus_issue_reporting/
│
├── app.py                  # Core Flask web server & SQLite database logic
├── campus.db               # SQLite database (auto-generated on app startup)
├── requirements.txt        # Python dependencies
├── README.md               # Documentation & setup guide
│
├── templates/
│   ├── base.html           # Layout shell (navbar, sidebar, flash messages)
│   ├── login.html          # Authentication login page
│   ├── register.html       # Student / Faculty account registration page
│   ├── dashboard.html      # Dynamic role-based dashboard & statistics
│   ├── report_issue.html   # Issue submission form with photo upload
│   ├── my_issues.html      # Personal issue list for Students/Faculty
│   ├── all_issues.html     # Manager all-issues management table with filters
│   ├── issue_details.html  # Detailed issue view, assignment form & timeline
│   ├── notifications.html  # User notification center
│   └── profile.html        # Account profile & password update
│
├── static/
│   ├── style.css           # Custom responsive CSS design system
│   └── script.js           # Client interactions & Canvas status chart renderer
│
└── uploads/                # Local directory for uploaded issue photos
```

---

## 🗄️ Database Description (`campus.db`)

1. `users`:
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `name`: TEXT NOT NULL
   - `username`: TEXT UNIQUE NOT NULL
   - `password`: TEXT NOT NULL (Hashed)
   - `role`: TEXT NOT NULL (`Student`, `Faculty`, `Manager`, `Maintenance Staff`)
   - `created_at`: TIMESTAMP

2. `issues`:
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `user_id`: INTEGER NOT NULL (FOREIGN KEY -> `users.id`)
   - `student_name`: TEXT NOT NULL
   - `category`: TEXT NOT NULL
   - `location`: TEXT NOT NULL
   - `description`: TEXT NOT NULL
   - `priority`: TEXT NOT NULL (`Low`, `Medium`, `High`, `Urgent`)
   - `status`: TEXT NOT NULL (`Pending`, `Assigned`, `In Progress`, `Resolved`)
   - `assigned_to`: INTEGER (FOREIGN KEY -> `users.id`)
   - `image_path`: TEXT
   - `created_at`, `updated_at`: TIMESTAMP

3. `issue_history`:
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `issue_id`: INTEGER NOT NULL (FOREIGN KEY -> `issues.id`)
   - `status`: TEXT NOT NULL
   - `updated_by`: INTEGER NOT NULL (FOREIGN KEY -> `users.id`)
   - `remarks`: TEXT
   - `updated_at`: TIMESTAMP

4. `notifications`:
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `user_id`: INTEGER NOT NULL (FOREIGN KEY -> `users.id`)
   - `issue_id`: INTEGER NOT NULL (FOREIGN KEY -> `issues.id`)
   - `message`: TEXT NOT NULL
   - `is_read`: INTEGER DEFAULT 0
   - `created_at`: TIMESTAMP

---

## 🔑 Demo Login Credentials

On first run, the system automatically initializes the database and seeds demo staff accounts:

| Role | Username | Password |
| :--- | :--- | :--- |
| **Manager** | `manager` | `manager123` |
| **Maintenance Staff** | `maintenance` | `maintenance123` |
| **Student / Faculty** | Register a new account on the `/register` page |

---

## 🚀 Installation & How to Run

### Step 1: Clone or Navigate to Project Directory
```bash
cd campus_issue_reporting
```

### Step 2: Create & Activate Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run Application
```bash
python app.py
```

Open your browser and navigate to: **`http://127.0.0.1:5000`**

---

## 🔄 Complete End-to-End Workflow

1. **Student / Faculty Registration**:
   - Go to `http://127.0.0.1:5000/register`.
   - Register account (e.g. `john_doe` / `password123`).
2. **Report Issue**:
   - Log in as `john_doe`.
   - Click **Report New Issue**. Select Category (e.g. `Electrical`), Location (e.g. `Science Lab 3`), Priority (`High`), enter Description, and upload an optional image.
   - Status is set to **`Pending`** and initial entry created in `issue_history`.
3. **Manager Review & Assignment**:
   - Log out and log in as Manager (`manager` / `manager123`).
   - Navigate to **All Issues**. View reported issue `#1`.
   - Assign issue to `Maintenance Staff`. Status automatically updates to **`Assigned`**.
4. **Maintenance Resolution**:
   - Log out and log in as Maintenance (`maintenance` / `maintenance123`).
   - View assigned work orders. Click **View**.
   - Change status to **`In Progress`** and later **`Resolved`** with resolution notes.
5. **Student Tracking**:
   - Log in back as `john_doe`.
   - Check notifications badge and view updated issue `#1` with completed status timeline.
