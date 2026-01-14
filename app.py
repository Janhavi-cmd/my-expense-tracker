from flask import Flask, render_template, request, redirect, session, make_response, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Expense
from datetime import datetime
from sqlalchemy import extract
from fpdf import FPDF
from functools import wraps

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SECRET_KEY'] = 'super-secret-key-change-in-production'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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

# ---------------- AUTH ROUTES ----------------

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            return redirect('/')
        flash("Invalid email or password", "danger")
    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        
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
@login_required
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect('/login')

# ---------------- DASHBOARD ----------------

@app.route('/', methods=['GET','POST'])
@login_required
def index():
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
            # Remove non-ASCII characters
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


if __name__ == '__main__':
    app.run(debug=True)