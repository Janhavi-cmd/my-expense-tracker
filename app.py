from flask import Flask, render_template, request, redirect, session, make_response, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Expense
from datetime import datetime
from sqlalchemy import extract, func
from fpdf import FPDF
from functools import wraps
import os
import json
import urllib.request

app = Flask(__name__)

# Use environment variables for production security
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-this')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///expenses.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Admin credentials (set via environment variables)
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@expensetracker.com')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

db.init_app(app)

with app.app_context():
    db.create_all()

# ---------------- AUTH DECORATOR ----------------

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'is_admin' not in session or not session['is_admin']:
            flash("Access denied. Admin only.", "danger")
            return redirect('/')
        return f(*args, **kwargs)
    return wrapper

# ---------------- AUTH ROUTES ----------------

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Check if admin login
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session['user_id'] = 0  # Special ID for admin
            session['is_admin'] = True
            session['email'] = ADMIN_EMAIL
            flash("Admin login successful", "success")
            return redirect('/admin')
        
        # Regular user login
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['is_admin'] = False
            session['email'] = user.email
            flash("Login successful", "success")
            return redirect('/')
        
        flash("Invalid email or password", "danger")
    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        
        # Prevent admin email registration
        if email == ADMIN_EMAIL:
            flash("This email is reserved", "danger")
            return redirect('/register')
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered", "danger")
            return redirect('/register')
        
        hashed = generate_password_hash(request.form['password'])
        user = User(email=email, password=hashed)
        db.session.add(user)
        db.session.commit()
        flash("Account created successfully! Please login.", "success")
        return redirect('/login')
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect('/login')

# ---------------- USER DASHBOARD ----------------

@app.route('/', methods=['GET','POST'])
@login_required
def index():
    # Redirect admin to admin panel
    if session.get('is_admin'):
        return redirect('/admin')
    
    # ADD EXPENSE
    if request.method == 'POST':
        try:
            expense = Expense(
                amount=float(request.form['amount']),
                category=request.form['category'],
                note=request.form.get('note', ''),
                date=datetime.strptime(request.form['date'], '%Y-%m-%d'),
                user_id=session['user_id']
            )
            db.session.add(expense)
            db.session.commit()
            flash("Expense added successfully", "success")
        except Exception as e:
            flash("Error adding expense", "danger")
            db.session.rollback()
        return redirect('/')

    # FILTER
    month = request.args.get('month')

    query = Expense.query.filter_by(
        user_id=session['user_id'],
        status="active"
    )

    if month:
        y, m = month.split('-')
        query = query.filter(
            extract('year', Expense.date) == int(y),
            extract('month', Expense.date) == int(m)
        )

    expenses = query.order_by(Expense.date.desc()).all()
    total = sum(e.amount for e in expenses)

    return render_template('index.html', expenses=expenses, total=total, selected_month=month)

# ---------------- EDIT ----------------

@app.route('/edit/<int:expense_id>', methods=['GET','POST'])
@login_required
def edit_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)

    if expense.user_id != session['user_id']:
        flash("Unauthorized access", "danger")
        return redirect('/')

    if request.method == 'POST':
        try:
            expense.amount = float(request.form['amount'])
            expense.category = request.form['category']
            expense.note = request.form.get('note', '')
            expense.date = datetime.strptime(request.form['date'], '%Y-%m-%d')
            db.session.commit()
            flash("Expense updated successfully", "info")
        except Exception as e:
            flash("Error updating expense", "danger")
            db.session.rollback()
        return redirect('/')

    return render_template('edit_expense.html', expense=expense)

# ---------------- DELETE ----------------

@app.route('/delete/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)

    if expense.user_id == session['user_id']:
        db.session.delete(expense)
        db.session.commit()
        flash("Expense deleted successfully", "danger")
    else:
        flash("Unauthorized access", "danger")

    return redirect('/')

# ---------------- SETTLE LENT MONEY ----------------

@app.route('/settle/<int:expense_id>', methods=['POST'])
@login_required
def settle_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)

    if expense.user_id == session['user_id'] and expense.category == "Lent":
        expense.status = "settled"
        db.session.commit()
        flash("Lent amount settled successfully", "success")
    else:
        flash("Cannot settle this expense", "danger")

    return redirect('/')

# ---------------- PDF GENERATION ----------------

@app.route('/pdf')
@login_required
def download_pdf():
    expenses = Expense.query.filter_by(
        user_id=session['user_id'],
        status="active"
    ).order_by(Expense.date.desc()).all()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Arial", style="B", size=16)
    pdf.cell(0, 10, "Expense Report", ln=True, align="C")
    pdf.ln(5)
    
    # User email
    user = User.query.get(session['user_id'])
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 6, f"User: {user.email}", ln=True)
    pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.ln(5)

    if not expenses:
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, "No active expenses found.", ln=True)
    else:
        total = 0

        # Table Header
        pdf.set_font("Arial", style="B", size=10)
        pdf.cell(30, 8, "Date", border=1, align="C")
        pdf.cell(40, 8, "Category", border=1, align="C")
        pdf.cell(30, 8, "Amount", border=1, align="C")
        pdf.cell(80, 8, "Note", border=1, align="C")
        pdf.ln()

        # Table Rows
        pdf.set_font("Arial", size=9)
        for e in expenses:
            pdf.cell(30, 8, str(e.date.strftime('%Y-%m-%d')), border=1)
            pdf.cell(40, 8, e.category[:15], border=1)
            pdf.cell(30, 8, f"Rs. {e.amount:.2f}", border=1, align="R")
            
            # Handle note text (ASCII safe)
            note_text = (e.note or "-")[:30]
            note_text = ''.join(char if ord(char) < 128 else '?' for char in note_text)
            pdf.cell(80, 8, note_text, border=1)
            pdf.ln()
            total += e.amount

        # Total
        pdf.ln(3)
        pdf.set_font("Arial", style="B", size=12)
        pdf.cell(0, 10, f"Total Active Expenses: Rs. {total:.2f}", ln=True, align="R")

    response = make_response(pdf.output(dest='S').encode('latin-1'))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=expenses.pdf'
    return response

# ============================================================
# SIMPLE ADMIN PANEL - READ ONLY
# ============================================================

@app.route('/admin')
@admin_required
def admin_panel():
    # Get all users
    users = User.query.order_by(User.created_at.desc()).all()
    
    # Get all expenses
    expenses = Expense.query.order_by(Expense.created_at.desc()).all()
    
    # Statistics
    total_users = len(users)
    total_expenses = len(expenses)
    
    return render_template('admin_simple.html',
                         users=users,
                         expenses=expenses,
                         total_users=total_users,
                         total_expenses=total_expenses)


# ============================================================
# AI FEATURES - Spending Insights & Budget Recommendations
# ============================================================

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

def call_claude(prompt, system_prompt, max_tokens=1024):
    """Call Claude API via urllib (no extra deps needed)."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None, "ANTHROPIC_API_KEY environment variable not set."

    payload = json.dumps({
        "model": "claude-sonnet-4-5-20250929",
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": [{"role": "user", "content": prompt}]
    }).encode("utf-8")

    req = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["content"][0]["text"], None
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return None, f"API error {e.code}: {body}"
    except Exception as e:
        return None, str(e)


def build_expense_summary(expenses):
    """Build a structured summary of expenses for the AI prompt."""
    if not expenses:
        return None

    category_totals = {}
    monthly_totals = {}
    for e in expenses:
        category_totals[e.category] = category_totals.get(e.category, 0) + e.amount
        month_key = e.date.strftime("%Y-%m")
        monthly_totals[month_key] = monthly_totals.get(month_key, 0) + e.amount

    grand_total = sum(category_totals.values())
    sorted_cats = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    sorted_months = sorted(monthly_totals.items())

    lines = [f"Total spending across all time: ₹{grand_total:.2f}",
             f"Number of expenses: {len(expenses)}",
             "",
             "Spending by category:"]
    for cat, amt in sorted_cats:
        pct = (amt / grand_total * 100) if grand_total else 0
        lines.append(f"  - {cat}: ₹{amt:.2f} ({pct:.1f}%)")

    if sorted_months:
        lines.append("")
        lines.append("Monthly totals (recent 6 months):")
        for m, amt in sorted_months[-6:]:
            lines.append(f"  - {m}: ₹{amt:.2f}")

    return "\n".join(lines)


@app.route('/ai/insights', methods=['GET'])
@login_required
def ai_insights():
    """AI Spending Insights – analyses the user's full expense history."""
    expenses = Expense.query.filter_by(
        user_id=session['user_id'],
        status="active"
    ).order_by(Expense.date.asc()).all()

    summary = build_expense_summary(expenses)
    if not summary:
        return render_template('ai_features.html',
                               active_tab='insights',
                               error="No expenses found. Add some expenses first!",
                               insights=None,
                               budgets=None)

    system_prompt = (
        "You are a personal finance analyst helping users understand their spending patterns. "
        "Give clear, actionable, empathetic insights. Use Indian Rupee (₹) formatting. "
        "Structure your response with these exact sections using plain text headers (no markdown bold/stars):\n"
        "OVERVIEW\n"
        "TOP SPENDING AREAS\n"
        "NOTABLE PATTERNS\n"
        "ACTIONABLE TIPS\n"
        "Keep each section concise (2-4 sentences). Be specific with numbers from the data."
    )

    user_prompt = (
        f"Here is my expense data:\n\n{summary}\n\n"
        "Please analyse my spending and provide personalized insights."
    )

    result, error = call_claude(user_prompt, system_prompt, max_tokens=900)

    if error:
        return render_template('ai_features.html',
                               active_tab='insights',
                               error=f"AI service error: {error}",
                               insights=None,
                               budgets=None)

    # Parse sections
    sections = {}
    current = None
    SECTION_KEYS = ["OVERVIEW", "TOP SPENDING AREAS", "NOTABLE PATTERNS", "ACTIONABLE TIPS"]
    lines = result.strip().splitlines()
    buf = []
    for line in lines:
        stripped = line.strip()
        matched = next((k for k in SECTION_KEYS if stripped.upper().startswith(k)), None)
        if matched:
            if current and buf:
                sections[current] = " ".join(buf).strip()
            current = matched
            buf = []
        elif current:
            if stripped:
                buf.append(stripped)
    if current and buf:
        sections[current] = " ".join(buf).strip()

    return render_template('ai_features.html',
                           active_tab='insights',
                           insights=sections,
                           raw_insights=result,
                           budgets=None,
                           error=None)


@app.route('/ai/budgets', methods=['GET'])
@login_required
def ai_budgets():
    """AI Budget Recommendations – suggests per-category monthly budgets."""
    expenses = Expense.query.filter_by(
        user_id=session['user_id'],
        status="active"
    ).order_by(Expense.date.asc()).all()

    summary = build_expense_summary(expenses)
    if not summary:
        return render_template('ai_features.html',
                               active_tab='budgets',
                               error="No expenses found. Add some expenses first!",
                               insights=None,
                               budgets=None)

    system_prompt = (
        "You are a personal finance coach. Suggest realistic monthly budgets based on actual spending. "
        "Respond ONLY with a valid JSON object – no markdown, no extra text. "
        "Format: {\"monthly_income_assumption\": \"string\", \"total_suggested_budget\": number, "
        "\"categories\": [{\"name\": \"string\", \"current_avg\": number, \"suggested\": number, "
        "\"change\": \"increase|decrease|maintain\", \"reason\": \"string\"}], "
        "\"overall_advice\": \"string\"}"
    )

    user_prompt = (
        f"Here is my expense data:\n\n{summary}\n\n"
        "Based on this spending history, suggest a realistic monthly budget for each category. "
        "Return ONLY valid JSON as specified."
    )

    result, error = call_claude(user_prompt, system_prompt, max_tokens=900)

    if error:
        return render_template('ai_features.html',
                               active_tab='budgets',
                               error=f"AI service error: {error}",
                               insights=None,
                               budgets=None)

    # Strip any accidental markdown fences
    cleaned = result.strip()
    if cleaned.startswith("```"):
        cleaned = "\n".join(cleaned.splitlines()[1:])
    if cleaned.endswith("```"):
        cleaned = "\n".join(cleaned.splitlines()[:-1])
    cleaned = cleaned.strip()

    try:
        budgets = json.loads(cleaned)
    except json.JSONDecodeError:
        return render_template('ai_features.html',
                               active_tab='budgets',
                               error="Could not parse AI budget response. Please try again.",
                               insights=None,
                               budgets=None)

    return render_template('ai_features.html',
                           active_tab='budgets',
                           budgets=budgets,
                           insights=None,
                           error=None)


if __name__ == '__main__':
    app.run(debug=True)