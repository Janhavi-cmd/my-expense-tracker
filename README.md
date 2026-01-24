# 💰 Expense Tracker

A full-stack web application for tracking personal expenses with a beautiful modern UI. Built with Flask (Python) and deployed on Render.

## 🌐 Live Demo

**[View Live Application](https://my-expense-tracker-7zb4.onrender.com)**

> **Note:** First load may take 30-50 seconds as the server wakes up (free tier hosting). Subsequent loads are instant.

## ✨ Features

- 🔐 **User Authentication** - Secure login and registration
- 💵 **Expense Management** - Add, edit, delete expenses
- 📊 **Categories** - Food, Transport, Shopping, Bills, Entertainment, Health, Education, Lent, Other
- 📅 **Filter by Month** - View expenses for specific time periods
- 💸 **Lent Money Tracking** - Track money lent and mark as settled
- 📄 **PDF Reports** - Download expense reports as PDF
- 🔒 **Admin Panel** - View all users and expenses (admin only)
- 📱 **Responsive Design** - Works on mobile and desktop
- 🎨 **Modern UI** - Beautiful gradient design with smooth animations

## 🛠️ Tech Stack

### Backend
- **Python 3.12**
- **Flask** - Web framework
- **SQLAlchemy** - ORM for database operations
- **SQLite** - Database
- **Werkzeug** - Password hashing
- **FPDF** - PDF generation

### Frontend
- **HTML5**
- **CSS3** - Modern gradients and animations
- **JavaScript** - Interactive features
- **Jinja2** - Template engine

### Deployment
- **Render** - Cloud hosting
- **Gunicorn** - Production WSGI server

## 📦 Installation

### Prerequisites
- Python 3.12 or higher
- pip
- Git

### Local Setup

1. **Clone the repository**
```bash
git clone https://github.com/Janhavi-cmd/my-expense-tracker.git
cd my-expense-tracker
```

2. **Create virtual environment**
```bash
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set environment variables** (optional)
```bash
# Windows PowerShell:
$env:SECRET_KEY="your-secret-key"
$env:ADMIN_EMAIL="admin@example.com"
$env:ADMIN_PASSWORD="admin123"

# macOS/Linux:
export SECRET_KEY="your-secret-key"
export ADMIN_EMAIL="admin@example.com"
export ADMIN_PASSWORD="admin123"
```

5. **Run the application**
```bash
python app.py
```

6. **Open in browser**
```
http://localhost:5000
```

## 🎯 Usage

### User Registration & Login
1. Navigate to the application
2. Click "Create Account"
3. Enter email and password (minimum 6 characters)
4. Login with your credentials

### Adding Expenses
1. After login, you'll see the dashboard
2. Fill in the "Add New Expense" form:
   - Amount (in Rupees)
   - Category (select from dropdown)
   - Date
   - Note (optional)
3. Click "Add Expense"

### Managing Expenses
- **Edit**: Click the "Edit" button on any expense
- **Delete**: Click the "Delete" button (requires confirmation)
- **Settle Lent Money**: If category is "Lent", click "Settle" when paid back

### Filtering
- Use the month filter to view expenses for a specific month
- Click "Clear Filter" to view all expenses

### PDF Reports
- Click "Download PDF Report" to generate and download a PDF of all active expenses

### Admin Access
- Login with admin credentials (set via environment variables)
- View all registered users and their expenses
- Read-only access for monitoring

## 📁 Project Structure

```
my-expense-tracker/
├── app.py                 # Main application file with routes
├── models.py              # Database models (User, Expense)
├── requirements.txt       # Python dependencies
├── templates/             # HTML templates
│   ├── index.html        # User dashboard
│   ├── login.html        # Login page
│   ├── register.html     # Registration page
│   ├── edit_expense.html # Edit expense form
│   └── admin_simple.html # Admin panel
├── static/                # Static files (CSS, JS)
│   ├── style.css
│   └── script.js
└── instance/              # Database files
    └── expenses.db       # SQLite database
```

## 🔑 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key for sessions | `dev-secret-key-change-this` |
| `DATABASE_URL` | Database connection string | `sqlite:///expenses.db` |
| `ADMIN_EMAIL` | Admin login email | `admin@expensetracker.com` |
| `ADMIN_PASSWORD` | Admin login password | `admin123` |

## 🚀 Deployment

This application is deployed on [Render](https://render.com). To deploy your own:

1. Fork this repository
2. Sign up on Render
3. Create a new Web Service
4. Connect your GitHub repository
5. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Environment Variables**: Add SECRET_KEY, ADMIN_EMAIL, ADMIN_PASSWORD

## 📸 Screenshots

### Login Page
Beautiful gradient login screen with form validation.

### Dashboard
Modern expense tracker with add, edit, delete functionality.

### Admin Panel
Monitor all users and expenses with database overview.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - feel free to use this for learning or your own projects.

## 👨‍💻 Developer

**Janhavi Chaturvedi**
- GitHub: [@Janhavi-cmd](https://github.com/Janhavi-cmd)
- Email: janhavichaturvedi0511@gmail.com

## 🙏 Acknowledgments

- Built while learning Flask and full-stack web development
- Inspired by personal finance tracking needs
- Thanks to the Flask and Python communities

## 📞 Contact

For questions, suggestions, or issues, please open an issue on GitHub or reach out via email.

---

**⭐ If you found this project helpful, please give it a star!**