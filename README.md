# KMTC ERP System

A comprehensive Enterprise Resource Planning (ERP) system designed specifically for Kenya Medical Training College (KMTC) to manage all aspects of medical education and training.

## 🏥 Overview

The KMTC ERP System is a Django-based web application that provides a complete solution for managing medical training institutions. It covers student management, academic records, clinical training, fee management, hostel accommodation, library services, and much more.

## ✨ Features

### 🎓 Academic Management
- **Programme Management**: Manage diplomas, certificates, and higher diplomas across various medical fields
- **Unit/Subject Management**: Handle core, elective, clinical, and practical units
- **Curriculum Management**: Define programme structures with year and semester breakdown
- **Academic Calendar**: Manage academic years and semesters

### 👥 User Management
- **Multi-role System**: Support for students, instructors, clinical instructors, staff, registrars, and admins
- **Student Profiles**: Comprehensive student information including guardian details and medical records
- **Instructor Management**: Track qualifications, experience, and employment details
- **Staff Management**: Manage administrative and support staff

### 📚 Academic Records
- **Enrollment Management**: Track student unit enrollments by semester
- **Grading System**: Comprehensive grading with theory, practical, and clinical components
- **Transcript Generation**: Automated GPA calculation and academic progress tracking
- **Examination Management**: Schedule and manage various types of examinations

### 💰 Financial Management
- **Fee Structure**: Flexible fee management with multiple components
- **Payment Processing**: Support for various payment methods including M-Pesa
- **Government Subsidies**: Handle government-sponsored students
- **Financial Reporting**: Track payments and generate financial reports

### 🏥 Clinical Training
- **Clinical Site Management**: Manage partnerships with hospitals and health facilities
- **Student Placements**: Assign students to clinical sites for practical training
- **Clinical Supervision**: Track clinical supervisors and completion reports
- **MOU Management**: Manage Memorandums of Understanding with clinical partners

### 🏠 Hostel Management
- **Accommodation**: Manage hostels, rooms, and student allocations
- **Room Types**: Support for single, double, triple rooms, and dormitories
- **Warden Management**: Track hostel wardens and their responsibilities
- **Occupancy Tracking**: Monitor room availability and capacity

### 📖 Library Management
- **Book Catalog**: Comprehensive book management with ISBN tracking
- **Issue/Return System**: Track book borrowing and returns
- **Fine Management**: Automated fine calculation for overdue books
- **Unit Integration**: Link books to specific academic units

### 📅 Timetable Management
- **Schedule Creation**: Create and manage class schedules
- **Venue Management**: Track classrooms, labs, and other facilities
- **Instructor Assignment**: Assign instructors to teaching sessions
- **Conflict Detection**: Prevent scheduling conflicts

### 📊 Attendance Tracking
- **Daily Attendance**: Track student attendance for theory, practical, and clinical sessions
- **Multiple Status Types**: Present, absent, late, excused, sick leave
- **Instructor Integration**: Allow instructors to mark attendance
- **Reporting**: Generate attendance reports and analytics

### 📢 Communication System
- **Notifications**: Send targeted notifications to specific groups or individuals
- **Priority Levels**: Urgent, high, medium, and low priority notifications
- **Multi-channel**: Support for various notification types (academic, fee, exam, etc.)
- **Read Tracking**: Monitor notification read status

### 🔬 Research & Projects
- **Project Management**: Track final year projects and research work
- **Supervisor Assignment**: Assign faculty supervisors to student projects
- **Progress Monitoring**: Monitor project milestones and completion
- **Grading Integration**: Grade projects within the main system

### 🏆 Professional Registration
- **Professional Bodies**: Manage relationships with medical professional bodies
- **Registration Tracking**: Track student registrations with professional bodies
- **Certificate Management**: Store and manage professional certificates
- **Status Monitoring**: Monitor registration status and renewals

### 👩‍⚕️ Student Services
- **Medical Services**: Track student health records and medical visits
- **Counseling Services**: Manage student counseling and support services
- **Service Requests**: Handle various student service requests
- **Emergency Contacts**: Maintain emergency contact information

### 📈 Quality Assurance
- **Assessment Tools**: Create and manage quality assessments
- **Feedback Collection**: Collect feedback on units, instructors, and facilities
- **Response Analysis**: Analyze quality assessment responses
- **Improvement Tracking**: Track quality improvement initiatives

### 🎓 Alumni Management
- **Graduate Tracking**: Maintain contact with program graduates
- **Career Tracking**: Monitor alumni career progression
- **Mentorship Programs**: Connect alumni with current students
- **Achievement Records**: Track alumni achievements and contributions

## 🛠️ Technical Stack

- **Backend**: Django 4.x
- **Database**: PostgreSQL (recommended) / MySQL / SQLite
- **Frontend**: Django Templates + Bootstrap (can be extended with React/Vue.js)
- **Authentication**: Django's built-in authentication system
- **File Storage**: Django's file handling system
- **API**: Django REST Framework (for mobile apps or third-party integrations)

## 📋 Requirements

```
Django>=4.0
Pillow>=9.0  # For image handling
python-decouple>=3.6  # For environment variables
psycopg2-binary>=2.9  # For PostgreSQL
reportlab>=3.6  # For PDF generation
xlsxwriter>=3.0  # For Excel reports
celery>=5.2  # For background tasks (optional)
redis>=4.0  # For caching and Celery broker (optional)
```

## 🚀 Installation

1. **Clone the repository**
```bash
git clone https://github.com/your-org/kmtc-erp.git
cd kmtc-erp
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment Configuration**
Create a `.env` file in the root directory:
```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/kmtc_erp
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

5. **Database Setup**
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

6. **Load Initial Data (Optional)**
```bash
python manage.py loaddata fixtures/initial_data.json
```

7. **Run Development Server**
```bash
python manage.py runserver
```

## 📊 Database Schema

The system uses a comprehensive database schema with the following main entity groups:

### Core Entities
- `User` - Extended Django user model with role-based access
- `School` - KMTC schools (Nursing, Medical Lab, etc.)
- `Programme` - Academic programmes offered
- `Unit` - Academic units/subjects

### People Management
- `Student` - Student profiles and academic information
- `Instructor` - Teaching staff information
- `Staff` - Administrative and support staff

### Academic Operations
- `AcademicYear` & `Semester` - Academic calendar management
- `Enrollment` - Student unit enrollments
- `Grade` - Academic grades and assessments
- `Attendance` - Student attendance tracking

### Clinical Training
- `ClinicalSite` - Partner hospitals and health facilities
- `ClinicalPlacement` - Student clinical assignments

### Financial Management
- `FeeStructure` - Programme fee definitions
- `FeePayment` - Student payment records

### Support Services
- `Hostel`, `Room`, `RoomAllocation` - Accommodation management
- `Book`, `BookIssue` - Library management
- `Venue`, `Schedule` - Timetable and facility management

## 🔐 User Roles & Permissions

### Administrator
- Full system access
- User management
- System configuration
- Reports and analytics

### Registrar
- Student registration and management
- Academic records
- Fee management
- Transcript generation

### Instructor
- Mark attendance
- Grade students
- Manage class schedules
- View student performance

### Clinical Instructor
- Manage clinical placements
- Assess clinical performance
- Monitor student progress in clinical settings

### Student
- View academic records
- Check timetables
- Make service requests
- View notifications

### Staff
- Manage assigned services
- Process service requests
- Generate relevant reports

## 📱 API Endpoints

The system provides RESTful API endpoints for mobile applications and third-party integrations:

```
/api/v1/students/          # Student management
/api/v1/instructors/       # Instructor management
/api/v1/programmes/        # Programme information
/api/v1/units/            # Unit management
/api/v1/enrollments/      # Enrollment data
/api/v1/grades/           # Grade management
/api/v1/attendance/       # Attendance tracking
/api/v1/notifications/    # Notification system
/api/v1/timetable/       # Schedule information
/api/v1/fees/            # Fee management
```

## 📈 Reporting & Analytics

The system includes comprehensive reporting capabilities:

- **Academic Reports**: Student transcripts, grade summaries, academic progress
- **Financial Reports**: Fee collection, outstanding balances, payment analysis
- **Attendance Reports**: Class attendance, student attendance patterns
- **Clinical Reports**: Placement tracking, clinical site utilization
- **Administrative Reports**: Enrollment statistics, programme performance

## 🔧 Configuration

### System Settings
Key configuration options available through the admin interface:

- Academic calendar settings
- Fee calculation parameters
- Notification preferences
- Grade calculation rules
- System-wide announcements

### Email Configuration
Configure email settings for notifications:
- SMTP server settings
- Email templates
- Automated notifications
- Bulk email capabilities

## 🧪 Testing

Run the test suite