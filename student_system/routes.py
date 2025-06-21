# routes.py
import os
from datetime import datetime, date
from urllib.parse import quote

from flask import (Blueprint, render_template, request, redirect, url_for, flash, 
                 send_file, jsonify, session, abort, current_app, make_response)
from flask_login import login_required, current_user
from sqlalchemy import func
from werkzeug.utils import secure_filename

import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from openpyxl.drawing.image import Image as XLSXImage
# import matplotlib.pyplot as plt  # Temporariamente comentado devido a problemas de instalação
import tempfile
import os

from .models import Student, LessonType, Payment, Notification, File
from . import db

bp = Blueprint('main', __name__)

# Month names in Portuguese
MONTH_NAMES = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto', 
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}

# File upload helper functions
def allowed_file(filename):
    from flask import current_app
    
    if not filename or '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', set())
    
    return extension in allowed_extensions

def get_file_type(filename):
    ext = filename.rsplit('.', 1)[1].lower()
    if ext in ['jpg', 'jpeg', 'png', 'gif']:
        return 'image'
    elif ext in ['mp3', 'wav', 'ogg']:
        return 'audio'
    elif ext in ['mp4', 'avi', 'mov']:
        return 'video'
    elif ext == 'pdf':
        return 'pdf'
    else:
        return 'document'

def save_file(file):
    """Save the file with a unique filename and return the path"""
    from werkzeug.utils import secure_filename
    import os
    import uuid
    from flask import current_app
    
    # Verifica se o arquivo tem um nome
    if not file or not file.filename:
        raise ValueError("Nenhum arquivo fornecido ou nome de arquivo inválido")
    
    # Gera um nome de arquivo seguro e único
    safe_filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{safe_filename}"
    
    # Obtém o diretório de uploads da configuração
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    file_path = os.path.join(upload_folder, unique_filename)
    
    try:
        # Cria o diretório de uploads se não existir
        os.makedirs(upload_folder, exist_ok=True)
        
        # Verifica se o arquivo já existe (embora improvável com UUID)
        if os.path.exists(file_path):
            raise FileExistsError(f"Arquivo com o nome {unique_filename} já existe.")
        
        # Salva o arquivo
        file.save(file_path)
        
        # Verifica se o arquivo foi salvo corretamente
        if not os.path.exists(file_path):
            raise IOError(f"Falha ao salvar o arquivo {unique_filename}.")
            
        return file_path
        
    except Exception:
        # Remove o arquivo se ele foi criado parcialmente
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        raise

@bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@bp.route('/dashboard')
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
        months=MONTH_NAMES,
        years=years,
        lesson_types=lesson_types,
        selected_lesson_type_id=lesson_type_id,
        current_month=current_month,
        current_year=current_year
    )

@bp.route('/dashboard/chart-data')
@login_required
def dashboard_chart_data():
    """Retorna dados para o gráfico do dashboard"""
    try:
        # Obter parâmetros da URL
        year = request.args.get('year', type=int, default=datetime.now().year)
        lesson_type_id = request.args.get('lesson_type_id', type=int)
        
        # Construir a consulta base
        query = db.session.query(
            func.extract('month', Payment.payment_date).label('month'),
            func.sum(Payment.amount).label('total')
        ).filter(
            Payment.payment_date.isnot(None)
        )
        
        # Filtrar por ano
        query = query.filter(func.extract('year', Payment.payment_date) == year)
        
        # Filtrar por tipo de aula se especificado
        if lesson_type_id:
            query = query.join(Student).filter(Student.lesson_type_id == lesson_type_id)
        
        # Agrupar por mês e ordenar
        query = query.group_by('month').order_by('month')
        
        # Executar a consulta
        query_result = query.all()
        
        # Preparar os dados para o gráfico
        result = []
        
        for month_num in range(1, 13):
            month_name = MONTH_NAMES.get(month_num, str(month_num))
            # Encontrar o total para este mês
            total = next((float(item[1]) for item in query_result if int(item[0]) == month_num), 0.0)
            
            # Adicionar objeto com os dados do mês
            result.append({
                'month': month_name,
                'paid': total,
                'pending': 0.0  # Adicione lógica para pendentes se necessário
            })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_dashboard_data(year, month=None, lesson_type_id=None):
    """Helper function to get dashboard data for export"""
    # Base query
    payments_query = Payment.query.filter(
        Payment.reference_year == year
    )
    
    if month:
        payments_query = payments_query.filter(Payment.reference_month == month)
    
    if lesson_type_id:
        payments_query = payments_query.filter(Payment.lesson_type_id == lesson_type_id)
    
    # Get paid and pending payments
    paid_payments = payments_query.filter(Payment.status == 'Pago').all()
    pending_payments = payments_query.filter(Payment.status == 'Pendente').all()
    
    # Calculate totals
    total_paid = sum(payment.amount for payment in paid_payments)
    total_pending = sum(payment.amount for payment in pending_payments)
    
    # Get count of active students (students with payments in the period)
    active_students_count = db.session.query(func.count(func.distinct(Payment.student_id))).filter(
        Payment.reference_year == year
    )
    
    if month:
        active_students_count = active_students_count.filter(Payment.reference_month == month)
    
    if lesson_type_id:
        active_students_count = active_students_count.filter(Payment.lesson_type_id == lesson_type_id)
    
    active_students_count = active_students_count.scalar()
    
    # Get chart data
    chart_data = []
    months_to_show = [month] if month else range(1, 13)
    
    for m in months_to_show:
        month_paid = sum(
            p.amount for p in paid_payments 
            if not month or p.reference_month == m
        )
        month_pending = sum(
            p.amount for p in pending_payments 
            if not month or p.reference_month == m
        )
        
        chart_data.append({
            'month': MONTH_NAMES[m],
            'paid': float(month_paid or 0),
            'pending': float(month_pending or 0)
        })
    
    return {
        'paid_count': len(paid_payments),
        'pending_count': len(pending_payments),
        'total_paid': float(total_paid or 0),
        'total_pending': float(total_pending or 0),
        'active_students': active_students_count,
        'chart_data': chart_data,
        'month': month,
        'year': year,
        'month_name': MONTH_NAMES[month] if month else None,
        'current_month': datetime.now().month,
        'current_year': datetime.now().year
    }

@bp.route('/dashboard/export/excel')
@login_required
def export_dashboard_excel():
    """Exporta os dados do dashboard para Excel"""
    try:
        # Get filter parameters
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int, default=datetime.now().year)
        lesson_type_id = request.args.get('lesson_type_id', type=int)
        
        # Get dashboard data
        data = get_dashboard_data(year, month, lesson_type_id)
        
        # Create a workbook and add a worksheet
        output = io.BytesIO()
        wb = Workbook()
        ws = wb.active
        ws.title = f"Relatório {year}"
        
        # Add headers
        headers = ['Mês', 'Valor Pago (R$)', 'Valor Pendente (R$)']
        ws.append(['Relatório Financeiro'])
        ws.append([f'Período: {data["month_name"] if data["month_name"] else "Ano inteiro"} {year}'])
        ws.append([])  # Empty row
        
        # Add data
        ws.append(headers)
        for row in data['chart_data']:
            ws.append([
                row['month'],
                row['paid'],
                row['pending']
            ])
        
        # Add summary
        ws.append([])  # Empty row
        ws.append(['Resumo'])
        ws.append(['Total Pago:', data['total_paid']])
        ws.append(['Total Pendente:', data['total_pending']])
        ws.append(['Alunos Ativos:', data['active_students']])
        
        # Format cells
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2) * 1.2
            ws.column_dimensions[column].width = adjusted_width
        
        # Save workbook to BytesIO
        wb.save(output)
        output.seek(0)
        
        # Create response
        filename = f"relatorio_{year}"
        if data['month_name']:
            filename += f"_{data['month_name'].lower()}"
        filename += ".xlsx"
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        flash('Erro ao gerar o arquivo Excel. Por favor, tente novamente.', 'danger')
        return redirect(url_for('main.dashboard'))

@bp.route('/dashboard/export/pdf')
@login_required
def export_dashboard_pdf():
    """Exporta os dados do dashboard para PDF"""
    # Função para adicionar número de página
    def add_page_number(canvas, doc):
        page_num = canvas.getPageNumber()
        text = f"Página {page_num}"
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#7f8c8d'))
        canvas.drawRightString(doc.width + doc.rightMargin - 20, 20, text)
        
        # Add footer line
        canvas.setStrokeColor(colors.HexColor('#bdc3c7'))
        canvas.setLineWidth(0.5)
        canvas.line(doc.leftMargin, 30, doc.width + doc.leftMargin, 30)
        
        # Add generated timestamp
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
        canvas.setFont('Helvetica', 7)
        canvas.drawString(doc.leftMargin, 20, f"Gerado em: {timestamp}")
        canvas.restoreState()
    
    try:
        # Get filter parameters
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int, default=datetime.now().year)
        lesson_type_id = request.args.get('lesson_type_id', type=int)
        
        # Get dashboard data
        data = get_dashboard_data(year, month, lesson_type_id)
        
        # Create PDF with smaller margins for more content space
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,  # 0.5 inch
            leftMargin=36,   # 0.5 inch
            topMargin=72,    # 1 inch
            bottomMargin=36  # 0.5 inch
        )
        elements = []
        
        # Custom Styles
        styles = getSampleStyleSheet()
        
        # Title Style
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=12,
            alignment=0,  # Left aligned
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#2c3e50')
        )
        
        # Subtitle Style
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=24,
            textColor=colors.HexColor('#7f8c8d')
        )
        
        # Header with logo and info
        logo_path = os.path.join('app', 'static', 'img', 'logo.png')
        
        # Header Table
        header_data = []
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=120, height=40)
            header_data.append([logo, ''])
        else:
            header_data.append([Paragraph("<b>Sonaris</b>", title_style), ''])
        
        header_table = Table(header_data, colWidths=[doc.width/2.0]*2)
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        elements.append(header_table)
        
        # Add report title and period
        period = f"{data['month_name']} {year}" if data['month_name'] else f"Ano {year}"
        elements.append(Paragraph("Relatório Financeiro", title_style))
        elements.append(Paragraph(f"Período: {period}", subtitle_style))
        
        # Add a line separator
        elements.append(HRFlowable(width="100%", thickness=1, lineCap='round', 
                                 color=colors.HexColor('#bdc3c7'), 
                                 spaceBefore=6, spaceAfter=12))
        
        # Add summary cards
        summary_data = [
            [
                Paragraph('<b>Total Pago</b>', styles['Normal']),
                Paragraph('<b>Total Pendente</b>', styles['Normal']),
                Paragraph('<b>Alunos Ativos</b>', styles['Normal'])
            ],
            [
                Paragraph(f"<font size='14'><b>R$ {data['total_paid']:,.2f}</b></font>", styles['Normal']),
                Paragraph(f"<font size='14'><b>R$ {data['total_pending']:,.2f}</b></font>", styles['Normal']),
                Paragraph(f"<font size='14'><b>{data['active_students']}</b></font>", styles['Normal'])
            ]
        ]
        
        summary_table = Table(summary_data, colWidths=[doc.width/3.0]*3)
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 0),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        # Add background colors to summary cards
        for i in range(3):
            summary_table.setStyle([
                ('BACKGROUND', (i, 0), (i, -1), colors.HexColor(['#e3f2fd', '#e8f5e9', '#fff8e1'][i])),
                ('BOX', (i, 0), (i, -1), 1, colors.HexColor('#e0e0e0')),
                ('BOTTOMPADDING', (i, 0), (i, -1), 12),
            ])
        
        elements.append(summary_table)
        elements.append(Spacer(1, 24))
        
        # Add detailed monthly data
        section_title_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.HexColor('#2c3e50'),
            fontName='Helvetica-Bold'
        )
        
        elements.append(Paragraph("Detalhamento Mensal", section_title_style))
        
        # Prepare table data with currency formatting
        table_data = [
            [
                Paragraph('<b>Mês</b>', styles['Normal']),
                Paragraph('<b>Valor Pago (R$)</b>', styles['Normal']),
                Paragraph('<b>Valor Pendente (R$)</b>', styles['Normal']),
                Paragraph('<b>Total (R$)</b>', styles['Normal'])
            ]
        ]
        
        # Add rows with data
        for row in data['chart_data']:
            total = row['paid'] + row['pending']
            table_data.append([
                row['month'],
                f"{row['paid']:,.2f}",
                f"{row['pending']:,.2f}",
                f"{total:,.2f}"
            ])
        
        # Calculate column widths (30% for month, 23.33% for each value column)
        col_widths = [doc.width * 0.3] + [doc.width * 0.233] * 3
        
        # Create and style the table
        chart_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        chart_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            
            # Data rows
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            
            # Grid and borders
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')])
        ]))
        
        elements.append(chart_table)
        
        # Add some space before the footer
        elements.append(Spacer(1, 30))
        
        # Build the PDF with the footer function
        doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
        buffer.seek(0)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"relatorio_financeiro_{timestamp}.pdf"
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        current_app.logger.error(f"Erro ao gerar relatório PDF: {str(e)}")
        flash('Erro ao gerar o arquivo PDF. Por favor, tente novamente.', 'danger')
        return redirect(url_for('main.dashboard'))

# ========= Student Routes =========
@bp.route('/students')
@login_required
def students():
    # Número de itens por página
    per_page = 10
    
    # Página atual (padrão: 1)
    page = request.args.get('page', 1, type=int)
    
    # Filtro de busca
    search = request.args.get('search', '').strip()
    
    # Consulta base
    query = Student.query
    
    # Aplicar filtro de busca se existir
    if search:
        search = f"%{search}%"
        query = query.filter(
            (Student.name.ilike(search)) |
            (Student.phone.ilike(search)) |
            (Student.notes.ilike(search))
        )
    
    # Ordenar e paginar
    students_pagination = query.order_by(Student.name).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('students.html', 
                         students=students_pagination.items,
                         pagination=students_pagination,
                         search=request.args.get('search', ''))

@bp.route('/students/new', methods=['GET', 'POST'])
@login_required
def new_student():
    # Obter todos os tipos de aula para o formulário
    lesson_types_list = LessonType.query.order_by(LessonType.name).all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        birth_date_str = request.form.get('birth_date')
        phone = request.form.get('phone')
        notes = request.form.get('notes')
        lesson_type_ids = request.form.getlist('lesson_type_ids')  # Lista de IDs selecionados
        
        # Simple validation
        if not name or not birth_date_str or not phone:
            flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
            return render_template('student_form.html', lesson_types=lesson_types_list)
        
        try:
            birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Data de nascimento inválida.', 'danger')
            return render_template('student_form.html', lesson_types=lesson_types_list)
        
        student = Student()
        student.name = name
        student.birth_date = birth_date
        student.phone = phone
        student.notes = notes
        
        # Adicionar os tipos de aula selecionados
        if lesson_type_ids:
            for lesson_type_id in lesson_type_ids:
                if lesson_type_id.isdigit():
                    lesson_type = LessonType.query.get(int(lesson_type_id))
                    if lesson_type:
                        student.lesson_types.append(lesson_type)
        
        db.session.add(student)
        db.session.commit()
        
        flash('Aluno cadastrado com sucesso!', 'success')
        return redirect(url_for('main.students'))
    
    return render_template('student_form.html', lesson_types=lesson_types_list)

@bp.route('/students/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_student(id):
    student = Student.query.get_or_404(id)
    # Obter todos os tipos de aula para o formulário
    lesson_types_list = LessonType.query.order_by(LessonType.name).all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        birth_date_str = request.form.get('birth_date')
        phone = request.form.get('phone')
        notes = request.form.get('notes')
        lesson_type_ids = request.form.getlist('lesson_type_ids')  # Lista de IDs selecionados
        
        # Simple validation
        if not name or not birth_date_str or not phone:
            flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
            return render_template('student_form.html', student=student, lesson_types=lesson_types_list)
        
        try:
            birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Data de nascimento inválida.', 'danger')
            return render_template('student_form.html', student=student, lesson_types=lesson_types_list)
        
        student.name = name
        student.birth_date = birth_date
        student.phone = phone
        student.notes = notes
        
        # Atualizar os tipos de aula
        student.lesson_types.clear()  # Remove todos os tipos atuais
        if lesson_type_ids:
            for lesson_type_id in lesson_type_ids:
                if lesson_type_id.isdigit():
                    lesson_type = LessonType.query.get(int(lesson_type_id))
                    if lesson_type:
                        student.lesson_types.append(lesson_type)
        
        db.session.commit()
        
        flash('Aluno atualizado com sucesso!', 'success')
        return redirect(url_for('main.students'))
    
    return render_template('student_form.html', student=student, lesson_types=lesson_types_list)

@bp.route('/students/<int:id>/delete', methods=['POST'])
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
@bp.route('/lesson-types')
@login_required
def lesson_types():
    # Número de itens por página
    per_page = 10
    
    # Página atual (padrão: 1)
    page = request.args.get('page', 1, type=int)
    
    # Consulta base
    query = LessonType.query
    
    # Ordenar e paginar
    types_pagination = query.order_by(LessonType.name).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('lesson_types.html', 
                         lesson_types=types_pagination.items,
                         pagination=types_pagination)

@bp.route('/lesson-types/new', methods=['GET', 'POST'])
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
        
        lesson_type = LessonType()
        lesson_type.name = name
        lesson_type.description = description
        lesson_type.default_price = default_price
        
        db.session.add(lesson_type)
        db.session.commit()
        
        flash('Tipo de aula cadastrado com sucesso!', 'success')
        return redirect(url_for('main.lesson_types'))
    
    return render_template('lesson_type_form.html')

@bp.route('/lesson-types/<int:id>/edit', methods=['GET', 'POST'])
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
        return redirect(url_for('main.lesson_types'))
    
    return render_template('lesson_type_form.html', lesson_type=lesson_type)

@bp.route('/lesson-types/<int:id>/delete', methods=['POST'])
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
    
    return redirect(url_for('main.lesson_types'))

# ========= Notification Routes =========

@bp.route('/notifications')
@login_required
def notifications():
    """Lista todas as notificações"""
    from sqlalchemy.orm import joinedload
    
    # Número de itens por página
    per_page = 15
    
    # Página atual (padrão: 1)
    page = request.args.get('page', 1, type=int)
    
    # Consulta base
    query = Notification.query.options(
        joinedload(Notification.student),
        joinedload(Notification.lesson_type),
        joinedload(Notification.sent_by)
    )
    
    # Ordenar e paginar
    notifications_pagination = query.order_by(Notification.sent_date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    # Carregar alunos e tipos de aula para o formulário
    students = Student.query.order_by(Student.name).all()
    lesson_types = LessonType.query.order_by(LessonType.name).all()
    
    return render_template(
        'notifications.html',
        notifications=notifications_pagination.items,
        pagination=notifications_pagination,
        students=students,
        lesson_types=lesson_types,
        title='Notificações'
    )

@bp.route('/notifications/new', methods=['GET', 'POST'])
@login_required
def new_notification():
    """Cria uma nova notificação"""
    if request.method == 'POST':
        title = request.form.get('title')
        message = request.form.get('message')
        notification_type = request.form.get('notification_type')
        student_id = request.form.get('student_id')
        lesson_type_id = request.form.get('lesson_type_id')
        group_name = request.form.get('group_name')
        
        if not title or not message or not notification_type:
            flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
            return redirect(url_for('main.new_notification'))
        
        try:
            notification = Notification(
                title=title,
                message=message,
                notification_type=notification_type,
                student_id=student_id if student_id != '0' else None,
                lesson_type_id=lesson_type_id if lesson_type_id != '0' else None,
                group_name=group_name if group_name else None,
                sent_by_id=current_user.id,
                status='Pendente'
            )
            
            db.session.add(notification)
            db.session.commit()
            
            flash('Notificação criada com sucesso!', 'success')
            return redirect(url_for('main.notifications'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar notificação: {str(e)}', 'danger')
            return redirect(url_for('main.new_notification'))
    
    # GET request
    students = Student.query.order_by(Student.name).all()
    lesson_types = LessonType.query.order_by(LessonType.name).all()
    
    return render_template(
        'notification_form.html',
        students=students,
        lesson_types=lesson_types,
        title='Nova Notificação'
    )

@bp.route('/notifications/<int:id>/delete', methods=['POST'])
@login_required
def delete_notification(id):
    """Exclui uma notificação"""
    notification = Notification.query.get_or_404(id)
    
    try:
        db.session.delete(notification)
        db.session.commit()
        flash('Notificação excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir notificação: {str(e)}', 'danger')
    
    return redirect(url_for('main.notifications'))

@bp.route('/notifications/<int:id>/send', methods=['GET'])
@login_required
def send_notification(id):
    """Envia uma notificação via WhatsApp"""
    from sqlalchemy.orm import joinedload
    from urllib.parse import quote

    # Carregar a notificação com os relacionamentos necessários
    notification = Notification.query\
        .options(
            joinedload(Notification.student),
            joinedload(Notification.lesson_type)
        )\
        .get_or_404(id)
    
    try:
        # Determinar os destinatários com base no tipo de notificação
        if notification.notification_type == 'individual' and notification.student_id:
            # Enviar para um aluno específico
            students = [notification.student]
        elif notification.notification_type == 'lesson_type' and notification.lesson_type_id:
            # Enviar para todos os alunos de um tipo de aula
            students = Student.query\
                .filter_by(lesson_type_id=notification.lesson_type_id)\
                .all()
        elif notification.notification_type == 'group' and notification.group_name:
            # Enviar para um grupo personalizado
            flash('Envio para grupos personalizados não implementado.', 'warning')
            return redirect(url_for('main.notifications'))
        else:
            # Enviar para todos os alunos
            students = Student.query.all()
        
        if not students:
            flash('Nenhum destinatário encontrado para enviar a notificação.', 'warning')
            return redirect(url_for('main.notifications'))
        
        # Para cada aluno, criar um link do WhatsApp
        whatsapp_links = []
        
        for student in students:
            if not student.phone:
                continue
                
            # Formatar número de telefone
            phone_number = ''.join(filter(str.isdigit, student.phone))
            
            # Adicionar código do país se não estiver presente
            if not phone_number.startswith('55'):
                phone_number = '55' + phone_number
            
            # Personalizar a mensagem com o nome do aluno se necessário
            personalized_message = notification.message
            if notification.student and '{nome_aluno}' in personalized_message:
                personalized_message = personalized_message.replace('{nome_aluno}', notification.student.name)
            
            # Codificar a mensagem para URL
            message = f"*{notification.title}*\n\n{personalized_message}"
            encoded_message = quote(message)
            
            # Criar o link do WhatsApp
            whatsapp_url = f"https://wa.me/{phone_number}?text={encoded_message}"
            
            # Atualizar o status da notificação
            notification.status = 'Enviada'
            notification.sent_date = datetime.now()
            db.session.commit()
            
            flash('Notificação enviada com sucesso!', 'success')
            return redirect(whatsapp_url)
            
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao enviar notificação: {str(e)}', 'danger')
        return redirect(url_for('main.notifications'))

# ========= Payment Routes =========
@bp.route('/payments')
@login_required
def payments():
    # Número de itens por página
    per_page = 15
    
    # Página atual (padrão: 1)
    page = request.args.get('page', 1, type=int)
    
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
    payments_pagination = query.join(Student).order_by(
        Payment.reference_year.desc(),
        Payment.reference_month.desc(),
        Student.name
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    # Get students for filter dropdown
    students = Student.query.order_by(Student.name).all()
    
    # Get current year for filter
    current_year = datetime.now().year
    years = list(range(current_year - 5, current_year + 1))
    
    return render_template(
        'payments.html',
        payments=payments_pagination.items,
        pagination=payments_pagination,
        students=students,
        months=MONTH_NAMES,
        years=years,
        selected_student_id=student_id,
        selected_month=month,
        selected_year=year,
        selected_status=status
    )

@bp.route('/payments/new', methods=['GET', 'POST'])
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
        
        payment = Payment()
        payment.student_id = student_id
        payment.lesson_type_id = lesson_type_id
        payment.reference_month = reference_month
        payment.reference_year = reference_year
        payment.amount = amount
        payment.status = status
        payment.payment_date = datetime.now() if status == 'Pago' else None
        
        db.session.add(payment)
        db.session.commit()
        
        flash('Mensalidade cadastrada com sucesso!', 'success')
        return redirect(url_for('main.payments'))
    
    students = Student.query.order_by(Student.name).all()
    lesson_types = LessonType.query.order_by(LessonType.name).all()
    
    # Get current month and year for default values
    current_date = datetime.now()
    current_year = current_date.year
    years = list(range(current_year - 5, current_year + 2))
    
    return render_template('payment_form.html', students=students, lesson_types=lesson_types, months=MONTH_NAMES, years=years)

@bp.route('/payments/<int:id>/edit', methods=['GET', 'POST'])
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
            return redirect(url_for('main.payment_receipt', id=payment.id))
        
        return redirect(url_for('main.payments'))
    
    students = Student.query.order_by(Student.name).all()
    lesson_types = LessonType.query.order_by(LessonType.name).all()
    current_year = datetime.now().year
    years = list(range(current_year - 5, current_year + 2))
    
    return render_template('payment_form.html', payment=payment, students=students, lesson_types=lesson_types, months=MONTH_NAMES, years=years)

@bp.route('/payments/<int:id>/delete', methods=['POST'])
@login_required
def delete_payment(id):
    payment = Payment.query.get_or_404(id)
    
    db.session.delete(payment)
    db.session.commit()
    
    flash('Mensalidade excluída com sucesso!', 'success')
    return redirect(url_for('main.payments'))

@bp.route('/payments/<int:id>/toggle-status', methods=['POST'])
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
        return redirect(url_for('main.payment_receipt', id=payment.id))
    
    return redirect(url_for('main.payments'))

@bp.route('/payments/<int:id>/receipt')
@login_required
def payment_receipt(id):
    payment = Payment.query.get_or_404(id)
    
    if payment.status != 'Pago':
        flash('Esta mensalidade ainda não foi paga.', 'warning')
        return redirect(url_for('main.payments'))
    
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

@bp.route('/get-student-lesson-types/<int:student_id>')
@login_required
def get_student_lesson_types(student_id):
    """Retorna os tipos de aula de um aluno específico via AJAX"""
    try:
        student = Student.query.get_or_404(student_id)
        lesson_types = []
        
        for lesson_type in student.lesson_types:
            lesson_types.append({
                'id': lesson_type.id,
                'name': lesson_type.name,
                'default_price': lesson_type.default_price
            })
        
        return jsonify({
            'success': True,
            'lesson_types': lesson_types
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/get-lesson-type-price/<int:id>')
@login_required
def get_lesson_type_price(id):
    lesson_type = LessonType.query.get_or_404(id)
    return jsonify({'default_price': lesson_type.default_price})

# ========= File Management Routes =========

@bp.route('/files')
@login_required
def files():
    """Lista todos os arquivos com filtros"""
    # Número de itens por página
    per_page = 15
    
    # Página atual (padrão: 1)
    page = request.args.get('page', 1, type=int)
    
    query = File.query
    
    # Filtro por aluno
    student_id = request.args.get('student_id', type=int)
    if student_id:
        query = query.filter(File.student_id == student_id)
    
    # Filtro por tipo de aula
    lesson_type_id = request.args.get('lesson_type_id', type=int)
    if lesson_type_id:
        query = query.filter(File.lesson_type_id == lesson_type_id)
    
    # Filtro por tipo de arquivo
    file_type = request.args.get('file_type')
    if file_type:
        if file_type == 'image':
            query = query.filter(File.file_type == 'image')
        elif file_type == 'document':
            query = query.filter(File.file_type.in_(['pdf', 'doc', 'docx', 'xls', 'xlsx']))
        elif file_type == 'pdf':
            query = query.filter(File.file_type == 'pdf')
        elif file_type == 'audio':
            query = query.filter(File.file_type.in_(['mp3', 'wav']))
        elif file_type == 'video':
            query = query.filter(File.file_type.in_(['mp4', 'avi']))
    
    # Ordena por data de upload (mais recentes primeiro) e pagina
    files_pagination = query.order_by(File.upload_date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    # Obtém listas para os filtros
    students = Student.query.order_by(Student.name).all()
    lesson_types = LessonType.query.order_by(LessonType.name).all()
    
    return render_template(
        'files.html',
        files=files_pagination.items,
        pagination=files_pagination,
        students=students,
        lesson_types=lesson_types,
        title='Arquivos',
        active_filters={
            'student_id': student_id,
            'lesson_type_id': lesson_type_id,
            'file_type': file_type
        }
    )

@bp.route('/files/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    """Faz upload de um novo arquivo"""
    if request.method == 'POST':
        # Verifica se o arquivo foi enviado
        if 'file' not in request.files:
            flash('Nenhum arquivo enviado.', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        # Se o usuário não selecionar um arquivo
        if file.filename == '':
            flash('Nenhum arquivo selecionado.', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            try:
                # Salva o arquivo no sistema de arquivos
                file_path = save_file(file)
                
                # Obtém os dados do formulário
                name = request.form.get('name') or file.filename
                description = request.form.get('description', '')
                recipient_type = request.form.get('recipient_type', 'all')
                
                # Inicializa variáveis
                student_id = None
                lesson_type_id = None
                group_name = None
                
                # Processa o destinatário de acordo com o tipo selecionado
                if recipient_type == 'student':
                    student_id = request.form.get('student_id')
                    if student_id and student_id != '0':
                        try:
                            student = Student.query.get_or_404(int(student_id))
                            name = f"{file.filename} - {student.name}"
                            lesson_type_id = None
                            group_name = None
                        except Exception:
                            flash('Erro ao processar o aluno selecionado.', 'danger')
                            return redirect(request.url)
                elif recipient_type == 'lesson_type':
                    lesson_type_id = request.form.get('lesson_type_id')
                    if lesson_type_id and lesson_type_id != '0':
                        try:
                            lesson_type = LessonType.query.get_or_404(int(lesson_type_id))
                            name = f"{file.filename} - {lesson_type.name}"
                            group_name = f"Aula de {lesson_type.name}"
                            student_id = None
                        except Exception:
                            flash('Erro ao processar o tipo de aula selecionado.', 'danger')
                            return redirect(request.url)
                elif recipient_type == 'group':
                    group_name = request.form.get('group_name', 'Geral').strip()
                    if not group_name:
                        flash('Por favor, insira um nome para o grupo.', 'danger')
                        return redirect(request.url)
                    name = f"{file.filename} - {group_name}"
                    student_id = None
                    lesson_type_id = None
                else:  # all
                    student_id = None
                    lesson_type_id = None
                    group_name = None
                
                # Cria o registro do arquivo no banco de dados
                file_type = get_file_type(file.filename)
                
                new_file = File(
                    name=name,
                    description=description,
                    file_path=file_path,
                    file_type=file_type,
                    student_id=student_id,
                    lesson_type_id=lesson_type_id,
                    group_name=group_name,
                    uploaded_by_id=current_user.id
                )
                
                try:
                    db.session.add(new_file)
                    db.session.commit()
                    
                    flash('Arquivo enviado com sucesso!', 'success')
                    return redirect(url_for('main.files'))
                    
                except Exception as db_error:
                    db.session.rollback()
                    raise db_error  # Re-lança a exceção para ser capturada no bloco externo
                    
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao fazer upload do arquivo: {str(e)}', 'danger')
                return redirect(request.url)
        else:
            flash('Tipo de arquivo não permitido.', 'danger')
            return redirect(request.url)
    
    # GET request
    students = Student.query.order_by(Student.name).all()
    lesson_types = LessonType.query.order_by(LessonType.name).all()
    
    return render_template(
        'file_upload.html',
        students=students,
        lesson_types=lesson_types,
        title='Enviar Arquivo'
    )

@bp.route('/files/<int:id>/delete', methods=['POST'])
@login_required
def delete_file(id):
    """Exclui um arquivo"""
    file = File.query.get_or_404(id)
    
    try:
        # Remove o arquivo do sistema de arquivos
        if os.path.exists(file.file_path):
            os.remove(file.file_path)
        
        # Remove o registro do banco de dados
        db.session.delete(file)
        db.session.commit()
        
        flash('Arquivo excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir o arquivo: {str(e)}', 'danger')
    
    return redirect(url_for('main.files'))

@bp.route('/files/<int:id>/download')
@login_required
def download_file(id):
    """Faz o download de um arquivo"""
    file = File.query.get_or_404(id)

    try:
        if not os.path.exists(file.file_path):
            flash('Arquivo não encontrado no servidor.', 'danger')
            return redirect(url_for('main.files'))

        return send_file(
            file.file_path,
            as_attachment=True,
            download_name=file.name + os.path.splitext(file.file_path)[1],
            mimetype='application/octet-stream'
        )
    except Exception as e:
        flash(f'Erro ao fazer download do arquivo: {str(e)}', 'danger')
        return redirect(url_for('main.files'))

@bp.route('/files/<int:id>/send', methods=['GET'])
@login_required
def send_file_whatsapp(id):
    """Envia um arquivo via WhatsApp para os destinatários"""
    from sqlalchemy.orm import joinedload
    from urllib.parse import quote

    # Carregar o arquivo com os relacionamentos necessários
    file = File.query\
        .options(
            joinedload(File.student),
            joinedload(File.lesson_type)
        )\
        .get_or_404(id)
    
    try:
        # Determinar os destinatários com base no tipo de arquivo
        if file.student_id:
            # Enviar para um aluno específico
            students = [file.student]
        elif file.lesson_type_id:
            # Enviar para todos os alunos de um tipo de aula
            students = Student.query\
                .filter_by(lesson_type_id=file.lesson_type_id)\
                .all()
        elif file.group_name:
            flash('Envio para grupos personalizados não implementado.', 'warning')
            return redirect(url_for('main.files'))
        else:
            # Enviar para todos os alunos
            students = Student.query.all()
        
        if not students:
            flash('Nenhum destinatário encontrado para enviar o arquivo.', 'warning')
            return redirect(url_for('main.files'))
        
        # Para cada aluno, criar um link do WhatsApp
        whatsapp_links = []
        base_url = request.host_url.rstrip('/')
        file_url = f"{base_url}/files/{file.id}/download"
        
        for student in students:
            if not student.phone:
                continue
                
            # Formatar número de telefone
            phone_number = ''.join(filter(str.isdigit, student.phone))
            
            # Adicionar código do país se não estiver presente
            if not phone_number.startswith('55'):
                phone_number = '55' + phone_number
            
            # Criar mensagem formatada
            message = f"*{file.name}*\n\n"
            if file.description:
                message += f"{file.description}\n\n"
            
            # Adicionar link em linha separada
            message += f"{file_url}"
            
            # Codificar mensagem para URL
            encoded_message = quote(message)
            
            # Criar link do WhatsApp
            whatsapp_url = f"https://wa.me/{phone_number}?text={encoded_message}"
            whatsapp_links.append((student, whatsapp_url))
        
        if not whatsapp_links:
            flash('Nenhum aluno com número de telefone válido encontrado para enviar o arquivo.', 'warning')
            return redirect(url_for('main.files'))
        
        # Se houver apenas um destinatário, redireciona diretamente
        if len(whatsapp_links) == 1:
            return redirect(whatsapp_links[0][1])
        
        # Se houver múltiplos destinatários, exibe uma página com os links
        return render_template(
            'send_file_whatsapp.html',
            file=file,
            whatsapp_links=whatsapp_links,
            title=f'Enviar {file.name}'
        )
        
    except Exception as e:
        flash(f'Erro ao gerar links do WhatsApp: {str(e)}', 'danger')
        return redirect(url_for('main.files'))
