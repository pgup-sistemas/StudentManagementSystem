import calendar
from datetime import datetime, date
from urllib.parse import quote
from flask import render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import extract, func
from app import app, db
from models import Student, LessonType, Payment

# Month names in Portuguese
MONTH_NAMES = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto', 
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get current month and year
    today = date.today()
    current_month = today.month
    current_year = today.year

    # Get filter parameters
    month = request.args.get('month', type=int, default=current_month)
    year = request.args.get('year', type=int, default=current_year)
    lesson_type_id = request.args.get('lesson_type_id', type=int)
    
    # Base query
    payments_query = Payment.query.filter(
        Payment.reference_month == month,
        Payment.reference_year == year
    )
    
    # Apply lesson type filter if provided
    if lesson_type_id:
        payments_query = payments_query.filter(Payment.lesson_type_id == lesson_type_id)
    
    # Get paid and pending payments
    paid_payments = payments_query.filter(Payment.status == 'Pago').all()
    pending_payments = payments_query.filter(Payment.status == 'Pendente').all()
    
    # Calculate totals
    total_paid = sum(payment.amount for payment in paid_payments)
    total_pending = sum(payment.amount for payment in pending_payments)
    
    # Get count of active students (students with payments in current month)
    active_students_count = db.session.query(func.count(func.distinct(Payment.student_id))).filter(
        Payment.reference_month == month,
        Payment.reference_year == year
    ).scalar()
    
    # Get all lesson types for filter dropdown
    lesson_types = LessonType.query.all()
    
    # Generate years for filter (current year and 5 years back)
    years = list(range(current_year - 5, current_year + 1))
    
    return render_template(
        'dashboard.html',
        paid_count=len(paid_payments),
        pending_count=len(pending_payments),
        total_paid=total_paid,
        total_pending=total_pending,
        active_students=active_students_count,
        month=month,
        year=year,
        month_name=MONTH_NAMES[month],
        years=years,
        lesson_types=lesson_types,
        selected_lesson_type_id=lesson_type_id,
        current_month=current_month,
        current_year=current_year
    )

@app.route('/dashboard/chart-data')
@login_required
def dashboard_chart_data():
    # Get current month and year
    today = date.today()
    year = request.args.get('year', type=int, default=today.year)
    
    # Prepare data for all months
    months_data = []
    for month in range(1, 13):
        # Get paid amount for this month
        paid_amount = db.session.query(func.sum(Payment.amount)).filter(
            Payment.reference_month == month,
            Payment.reference_year == year,
            Payment.status == 'Pago'
        ).scalar() or 0
        
        # Get pending amount for this month
        pending_amount = db.session.query(func.sum(Payment.amount)).filter(
            Payment.reference_month == month,
            Payment.reference_year == year,
            Payment.status == 'Pendente'
        ).scalar() or 0
        
        months_data.append({
            'month': MONTH_NAMES[month],
            'paid': round(paid_amount, 2),
            'pending': round(pending_amount, 2)
        })
    
    return jsonify(months_data)

# ========= Student Routes =========
@app.route('/students')
@login_required
def students():
    students_list = Student.query.order_by(Student.name).all()
    return render_template('students.html', students=students_list)

@app.route('/students/new', methods=['GET', 'POST'])
@login_required
def new_student():
    if request.method == 'POST':
        name = request.form.get('name')
        birth_date_str = request.form.get('birth_date')
        phone = request.form.get('phone')
        notes = request.form.get('notes')
        
        # Simple validation
        if not name or not birth_date_str or not phone:
            flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
            return render_template('student_form.html')
        
        try:
            birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Data de nascimento inválida.', 'danger')
            return render_template('student_form.html')
        
        student = Student(
            name=name,
            birth_date=birth_date,
            phone=phone,
            notes=notes
        )
        
        db.session.add(student)
        db.session.commit()
        
        flash('Aluno cadastrado com sucesso!', 'success')
        return redirect(url_for('students'))
    
    return render_template('student_form.html')

@app.route('/students/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_student(id):
    student = Student.query.get_or_404(id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        birth_date_str = request.form.get('birth_date')
        phone = request.form.get('phone')
        notes = request.form.get('notes')
        
        # Simple validation
        if not name or not birth_date_str or not phone:
            flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
            return render_template('student_form.html', student=student)
        
        try:
            birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Data de nascimento inválida.', 'danger')
            return render_template('student_form.html', student=student)
        
        student.name = name
        student.birth_date = birth_date
        student.phone = phone
        student.notes = notes
        
        db.session.commit()
        
        flash('Aluno atualizado com sucesso!', 'success')
        return redirect(url_for('students'))
    
    return render_template('student_form.html', student=student)

@app.route('/students/<int:id>/delete', methods=['POST'])
@login_required
def delete_student(id):
    student = Student.query.get_or_404(id)
    
    try:
        db.session.delete(student)
        db.session.commit()
        flash('Aluno excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Não foi possível excluir o aluno. Verifique se há mensalidades associadas.', 'danger')
    
    return redirect(url_for('students'))

# ========= Lesson Type Routes =========
@app.route('/lesson-types')
@login_required
def lesson_types():
    types_list = LessonType.query.order_by(LessonType.name).all()
    return render_template('lesson_types.html', lesson_types=types_list)

@app.route('/lesson-types/new', methods=['GET', 'POST'])
@login_required
def new_lesson_type():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        default_price_str = request.form.get('default_price')
        
        # Simple validation
        if not name:
            flash('Por favor, informe o nome do tipo de aula.', 'danger')
            return render_template('lesson_type_form.html')
        
        default_price = None
        if default_price_str:
            try:
                default_price = float(default_price_str.replace(',', '.'))
            except ValueError:
                flash('Valor padrão inválido.', 'danger')
                return render_template('lesson_type_form.html')
        
        lesson_type = LessonType(
            name=name,
            description=description,
            default_price=default_price
        )
        
        db.session.add(lesson_type)
        db.session.commit()
        
        flash('Tipo de aula cadastrado com sucesso!', 'success')
        return redirect(url_for('lesson_types'))
    
    return render_template('lesson_type_form.html')

@app.route('/lesson-types/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_lesson_type(id):
    lesson_type = LessonType.query.get_or_404(id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        default_price_str = request.form.get('default_price')
        
        # Simple validation
        if not name:
            flash('Por favor, informe o nome do tipo de aula.', 'danger')
            return render_template('lesson_type_form.html', lesson_type=lesson_type)
        
        default_price = None
        if default_price_str:
            try:
                default_price = float(default_price_str.replace(',', '.'))
            except ValueError:
                flash('Valor padrão inválido.', 'danger')
                return render_template('lesson_type_form.html', lesson_type=lesson_type)
        
        lesson_type.name = name
        lesson_type.description = description
        lesson_type.default_price = default_price
        
        db.session.commit()
        
        flash('Tipo de aula atualizado com sucesso!', 'success')
        return redirect(url_for('lesson_types'))
    
    return render_template('lesson_type_form.html', lesson_type=lesson_type)

@app.route('/lesson-types/<int:id>/delete', methods=['POST'])
@login_required
def delete_lesson_type(id):
    lesson_type = LessonType.query.get_or_404(id)
    
    try:
        db.session.delete(lesson_type)
        db.session.commit()
        flash('Tipo de aula excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Não foi possível excluir o tipo de aula. Verifique se há mensalidades associadas.', 'danger')
    
    return redirect(url_for('lesson_types'))

# ========= Payment Routes =========
@app.route('/payments')
@login_required
def payments():
    # Get filter parameters
    student_id = request.args.get('student_id', type=int)
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    status = request.args.get('status')
    
    # Base query
    query = Payment.query
    
    # Apply filters
    if student_id:
        query = query.filter(Payment.student_id == student_id)
    if month:
        query = query.filter(Payment.reference_month == month)
    if year:
        query = query.filter(Payment.reference_year == year)
    if status:
        query = query.filter(Payment.status == status)
    
    # Order by year (desc), month (desc), and student name
    payments_list = query.join(Student).order_by(
        Payment.reference_year.desc(),
        Payment.reference_month.desc(),
        Student.name
    ).all()
    
    # Get students for filter dropdown
    students = Student.query.order_by(Student.name).all()
    
    # Get current year for filter
    current_year = datetime.now().year
    years = list(range(current_year - 5, current_year + 1))
    
    return render_template(
        'payments.html',
        payments=payments_list,
        students=students,
        months=MONTH_NAMES,
        years=years,
        selected_student_id=student_id,
        selected_month=month,
        selected_year=year,
        selected_status=status
    )

@app.route('/payments/new', methods=['GET', 'POST'])
@login_required
def new_payment():
    if request.method == 'POST':
        student_id = request.form.get('student_id', type=int)
        lesson_type_id = request.form.get('lesson_type_id', type=int)
        reference_month = request.form.get('reference_month', type=int)
        reference_year = request.form.get('reference_year', type=int)
        amount_str = request.form.get('amount')
        status = request.form.get('status')
        
        # Simple validation
        if not student_id or not lesson_type_id or not reference_month or not reference_year or not amount_str or not status:
            flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
            students = Student.query.order_by(Student.name).all()
            lesson_types = LessonType.query.order_by(LessonType.name).all()
            current_year = datetime.now().year
            years = list(range(current_year - 5, current_year + 2))
            return render_template('payment_form.html', students=students, lesson_types=lesson_types, months=MONTH_NAMES, years=years)
        
        try:
            amount = float(amount_str.replace(',', '.'))
        except ValueError:
            flash('Valor inválido.', 'danger')
            students = Student.query.order_by(Student.name).all()
            lesson_types = LessonType.query.order_by(LessonType.name).all()
            current_year = datetime.now().year
            years = list(range(current_year - 5, current_year + 2))
            return render_template('payment_form.html', students=students, lesson_types=lesson_types, months=MONTH_NAMES, years=years)
        
        # Check if there's already a payment for this student, lesson type, month and year
        existing_payment = Payment.query.filter_by(
            student_id=student_id,
            lesson_type_id=lesson_type_id,
            reference_month=reference_month,
            reference_year=reference_year
        ).first()
        
        if existing_payment:
            flash('Já existe uma mensalidade cadastrada para este aluno, tipo de aula, mês e ano.', 'warning')
            students = Student.query.order_by(Student.name).all()
            lesson_types = LessonType.query.order_by(LessonType.name).all()
            current_year = datetime.now().year
            years = list(range(current_year - 5, current_year + 2))
            return render_template('payment_form.html', students=students, lesson_types=lesson_types, months=MONTH_NAMES, years=years)
        
        payment = Payment(
            student_id=student_id,
            lesson_type_id=lesson_type_id,
            reference_month=reference_month,
            reference_year=reference_year,
            amount=amount,
            status=status,
            payment_date=datetime.now() if status == 'Pago' else None
        )
        
        db.session.add(payment)
        db.session.commit()
        
        flash('Mensalidade cadastrada com sucesso!', 'success')
        return redirect(url_for('payments'))
    
    students = Student.query.order_by(Student.name).all()
    lesson_types = LessonType.query.order_by(LessonType.name).all()
    
    # Get current month and year for default values
    current_date = datetime.now()
    current_year = current_date.year
    years = list(range(current_year - 5, current_year + 2))
    
    return render_template('payment_form.html', students=students, lesson_types=lesson_types, months=MONTH_NAMES, years=years)

@app.route('/payments/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_payment(id):
    payment = Payment.query.get_or_404(id)
    
    if request.method == 'POST':
        student_id = request.form.get('student_id', type=int)
        lesson_type_id = request.form.get('lesson_type_id', type=int)
        reference_month = request.form.get('reference_month', type=int)
        reference_year = request.form.get('reference_year', type=int)
        amount_str = request.form.get('amount')
        status = request.form.get('status')
        
        # Simple validation
        if not student_id or not lesson_type_id or not reference_month or not reference_year or not amount_str or not status:
            flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
            students = Student.query.order_by(Student.name).all()
            lesson_types = LessonType.query.order_by(LessonType.name).all()
            current_year = datetime.now().year
            years = list(range(current_year - 5, current_year + 2))
            return render_template('payment_form.html', payment=payment, students=students, lesson_types=lesson_types, months=MONTH_NAMES, years=years)
        
        try:
            amount = float(amount_str.replace(',', '.'))
        except ValueError:
            flash('Valor inválido.', 'danger')
            students = Student.query.order_by(Student.name).all()
            lesson_types = LessonType.query.order_by(LessonType.name).all()
            current_year = datetime.now().year
            years = list(range(current_year - 5, current_year + 2))
            return render_template('payment_form.html', payment=payment, students=students, lesson_types=lesson_types, months=MONTH_NAMES, years=years)
        
        # Check for duplicate, but exclude the current payment
        existing_payment = Payment.query.filter(
            Payment.id != id,
            Payment.student_id == student_id,
            Payment.lesson_type_id == lesson_type_id,
            Payment.reference_month == reference_month,
            Payment.reference_year == reference_year
        ).first()
        
        if existing_payment:
            flash('Já existe uma mensalidade cadastrada para este aluno, tipo de aula, mês e ano.', 'warning')
            students = Student.query.order_by(Student.name).all()
            lesson_types = LessonType.query.order_by(LessonType.name).all()
            current_year = datetime.now().year
            years = list(range(current_year - 5, current_year + 2))
            return render_template('payment_form.html', payment=payment, students=students, lesson_types=lesson_types, months=MONTH_NAMES, years=years)
        
        # Check if status is changing from 'Pendente' to 'Pago'
        was_status_changed_to_paid = payment.status == 'Pendente' and status == 'Pago'
        
        payment.student_id = student_id
        payment.lesson_type_id = lesson_type_id
        payment.reference_month = reference_month
        payment.reference_year = reference_year
        payment.amount = amount
        payment.status = status
        
        # Update payment date if status changed to 'Pago'
        if was_status_changed_to_paid:
            payment.payment_date = datetime.now()
        elif status == 'Pendente':
            payment.payment_date = None
        
        db.session.commit()
        
        flash('Mensalidade atualizada com sucesso!', 'success')
        
        # If status changed to 'Pago', redirect to receipt page
        if was_status_changed_to_paid:
            return redirect(url_for('payment_receipt', id=payment.id))
        
        return redirect(url_for('payments'))
    
    students = Student.query.order_by(Student.name).all()
    lesson_types = LessonType.query.order_by(LessonType.name).all()
    current_year = datetime.now().year
    years = list(range(current_year - 5, current_year + 2))
    
    return render_template('payment_form.html', payment=payment, students=students, lesson_types=lesson_types, months=MONTH_NAMES, years=years)

@app.route('/payments/<int:id>/delete', methods=['POST'])
@login_required
def delete_payment(id):
    payment = Payment.query.get_or_404(id)
    
    db.session.delete(payment)
    db.session.commit()
    
    flash('Mensalidade excluída com sucesso!', 'success')
    return redirect(url_for('payments'))

@app.route('/payments/<int:id>/toggle-status', methods=['POST'])
@login_required
def toggle_payment_status(id):
    payment = Payment.query.get_or_404(id)
    
    # Toggle status
    was_status_changed_to_paid = payment.status == 'Pendente'
    payment.status = 'Pago' if payment.status == 'Pendente' else 'Pendente'
    
    # Update payment date
    if payment.status == 'Pago':
        payment.payment_date = datetime.now()
    else:
        payment.payment_date = None
    
    db.session.commit()
    
    status_text = 'paga' if payment.status == 'Pago' else 'pendente'
    flash(f'Mensalidade marcada como {status_text} com sucesso!', 'success')
    
    # If status changed to 'Pago', redirect to receipt page
    if was_status_changed_to_paid:
        return redirect(url_for('payment_receipt', id=payment.id))
    
    return redirect(url_for('payments'))

@app.route('/payments/<int:id>/receipt')
@login_required
def payment_receipt(id):
    payment = Payment.query.get_or_404(id)
    
    if payment.status != 'Pago':
        flash('Esta mensalidade ainda não foi paga.', 'warning')
        return redirect(url_for('payments'))
    
    # Create WhatsApp message
    student_name = payment.student.name
    lesson_type = payment.lesson_type.name
    month_name = MONTH_NAMES[payment.reference_month]
    year = payment.reference_year
    amount = f'R$ {payment.amount:.2f}'.replace('.', ',')
    
    message = f"Olá! Confirmo o recebimento da mensalidade:\n\n"
    message += f"Aluno: {student_name}\n"
    message += f"Tipo de aula: {lesson_type}\n"
    message += f"Referência: {month_name}/{year}\n"
    message += f"Valor: {amount}\n"
    message += f"Status: PAGO\n\n"
    message += f"Obrigado pelo pagamento!"
    
    # Create WhatsApp link
    # Format phone number (remove non-numeric characters)
    phone = ''.join(filter(str.isdigit, payment.student.phone))
    
    # Ensure phone has country code (55 for Brazil)
    if not phone.startswith('55'):
        phone = '55' + phone
    
    whatsapp_url = f"https://wa.me/{phone}?text={quote(message)}"
    
    return render_template(
        'payment_receipt.html',
        payment=payment,
        student_name=student_name,
        lesson_type=lesson_type,
        month_name=month_name,
        year=year,
        amount=amount,
        whatsapp_url=whatsapp_url,
        message=message
    )

@app.route('/get-lesson-type-price/<int:id>')
@login_required
def get_lesson_type_price(id):
    lesson_type = LessonType.query.get_or_404(id)
    return jsonify({'default_price': lesson_type.default_price})
