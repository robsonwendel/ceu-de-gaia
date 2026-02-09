from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from datetime import datetime, timedelta, timezone
from sqlalchemy.sql.expression import extract
from apscheduler.schedulers.background import BackgroundScheduler
import os
from sqlalchemy import func, distinct, case
from sqlalchemy.orm import aliased





# Configuração do Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'senha1989'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'mysql+mysqlconnector://mysql:geh*1989@site-gaia_banco-gaia:3306/yoga_school'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicialização de Extensões
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Configurar Flask-Migrate
migrate = Migrate(app, db)

# Tabela intermediária
aluno_turma = db.Table('aluno_turma',
    db.Column('aluno_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('turma_id', db.Integer, db.ForeignKey('turma.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)

    # Informações pessoais
    data_nascimento = db.Column(db.Date, nullable=True)
    sexo = db.Column(db.String(20), nullable=True)
    profissao = db.Column(db.String(150), nullable=True)

    # Endereço
    endereco = db.Column(db.String(255), nullable=True)
    numero_endereco = db.Column(db.String(10), nullable=True)
    bairro = db.Column(db.String(100), nullable=True)
    cidade = db.Column(db.String(100), nullable=True)
    estado = db.Column(db.String(50), nullable=True)
    cep = db.Column(db.String(20), nullable=True)

    # Contato
    contato_1 = db.Column(db.String(20), nullable=True)
    contato_2 = db.Column(db.String(20), nullable=True)
    contato_emergencia = db.Column(db.String(20), nullable=True)
    nome_contato_emergencia = db.Column(db.String(150), nullable=True)

    # Histórico de saúde
    antecedentes_cirurgicos = db.Column(db.Text, nullable=True)
    tratamentos_medicamentosos = db.Column(db.Text, nullable=True)
    antecedentes_alergicos = db.Column(db.Text, nullable=True)
    funcionamento_intestino = db.Column(db.Boolean, nullable=True)
    pratica_atividade_fisica = db.Column(db.Boolean, nullable=True)
    indicacoes_observacoes = db.Column(db.Text, nullable=True)

    turmas = db.relationship('Turma', secondary=aluno_turma, backref=db.backref('alunos', lazy='dynamic'))

class Turma(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    professor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    professor = db.relationship('User', backref='turmas_professor', lazy=True)
    ativa = db.Column(db.Boolean, default=True)

class ContasPagar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    vencimento = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='Pendente')

class Mensalidade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    turma_id = db.Column(db.Integer, db.ForeignKey('turma.id'), nullable=False)
    professor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    mes = db.Column(db.String(20), nullable=False)
    valor = db.Column(db.Float, nullable=False, default=100.0)
    status = db.Column(db.String(20), default='Pendente')
    data_matricula = db.Column(db.Date, nullable=False)

    aluno = db.relationship('User', foreign_keys=[aluno_id])
    turma = db.relationship('Turma', foreign_keys=[turma_id])
    professor = db.relationship('User', foreign_keys=[professor_id])

class HistoricoMatricula(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    turma_id = db.Column(db.Integer, db.ForeignKey('turma.id'), nullable=False)
    data_acao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    acao = db.Column(db.String(50), nullable=False)
    aluno = db.relationship('User', backref='historico_matriculas')
    turma = db.relationship('Turma', backref='historico_matriculas')

from datetime import datetime

class Presenca(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_aula = db.Column(db.Date, nullable=False)
    presente = db.Column(db.Boolean, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    turma_id = db.Column(db.Integer, db.ForeignKey('turma.id'), nullable=False)

    # 🔥 RELACIONAMENTOS
    aluno = db.relationship('User', backref='presencas')
    turma = db.relationship('Turma', backref='presencas')




class Matricula(db.Model):
    __tablename__ = 'matricula'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    turma_id = db.Column(db.Integer, db.ForeignKey('turma.id'), nullable=False)
    data_matricula = db.Column(db.DateTime, default=datetime.utcnow)
    data_vencimento = db.Column(db.Integer)  # Guardamos apenas o dia (ex: 10, 15, 20)

    # Relacionamentos para facilitar o acesso
    aluno = db.relationship('User', backref='suas_matriculas')
    turma = db.relationship('Turma', backref='matriculas_alunos')    

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# --- ROTAS NOVAS ADICIONADAS PARA FUNCIONAR COM O DASHBOARD MELHORADO ---

@app.route('/get_alunos_turma/<int:turma_id>')
@login_required
def get_alunos_turma(turma_id):
    # Buscamos através da tabela de associação Matricula
    matriculas = Matricula.query.filter_by(turma_id=turma_id).all()
    
    lista = []
    for m in matriculas:
        lista.append({
            'id': m.aluno.id,
            'username': m.aluno.username,
            'email': m.aluno.email,
            'data_matricula': m.data_matricula.strftime('%d/%m/%Y'),
            'vencimento': m.data_vencimento
        })
    
    return jsonify({'alunos': lista})

# --- FIM DAS ROTAS NOVAS ---

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/horarios')
def horarios():
    return render_template('horarios.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # 1. Coleta de dados básicos do formulário
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # 2. Verificação de Duplicidade (Evita o IntegrityError)
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Este nome de usuário já está em uso. Escolha outro.', 'danger')
            return redirect(url_for('register'))

        if email:
            email_exists = User.query.filter_by(email=email).first()
            if email_exists:
                flash('Este e-mail já está cadastrado em outra conta.', 'danger')
                return redirect(url_for('register'))

        # 3. Tratamento de campos específicos (Data e Checkbox)
        data_nasc_raw = request.form.get('data_nascimento')
        data_nascimento = None
        if data_nasc_raw:
            try:
                data_nascimento = datetime.strptime(data_nasc_raw, '%Y-%m-%d').date()
            except ValueError:
                data_nascimento = None

        # Checkbox retorna 'True' ou None
        pratica_atividade = True if request.form.get('pratica_atividade_fisica') else False
        intestino_regular = True if request.form.get('funcionamento_intestino') else False

        # 4. Criptografia da senha
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # 5. Criação do objeto User com todos os campos do seu banco
        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            role='aluno', # Definido como padrão
            is_approved=True, # Sua nova regra: aprovado automaticamente
            is_admin=False,
            
            # Informações Pessoais
            data_nascimento=data_nascimento,
            sexo=request.form.get('sexo'),
            profissao=request.form.get('profissao'),
            
            # Endereço
            endereco=request.form.get('endereco'),
            numero_endereco=request.form.get('numero_endereco'),
            bairro=request.form.get('bairro'),
            cidade=request.form.get('cidade'),
            estado=request.form.get('estado'),
            cep=request.form.get('cep'),
            
            # Contato
            contato_1=request.form.get('contato_1'),
            contato_2=request.form.get('contato_2'),
            contato_emergencia=request.form.get('contato_emergencia'),
            nome_contato_emergencia=request.form.get('nome_contato_emergencia'),
            
            # Histórico de Saúde
            antecedentes_cirurgicos=request.form.get('antecedentes_cirurgicos'),
            tratamentos_medicamentosos=request.form.get('tratamentos_medicamentosos'),
            antecedentes_alergicos=request.form.get('antecedentes_alergicos'),
            funcionamento_intestino=intestino_regular,
            pratica_atividade_fisica=pratica_atividade,
            indicacoes_observacoes=request.form.get('indicacoes_observacoes')
        )

        # 6. Salvar no Banco de Dados
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Cadastro realizado com sucesso! Bem-vindo(a) à Céu de Gaia.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback() # Cancela a operação se der erro
            print(f"Erro ao cadastrar: {e}")
            flash('Ocorreu um erro interno ao salvar seus dados. Tente novamente.', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Agora pegamos o email do formulário
        email_login = request.form.get('email')
        password = request.form.get('password')
        
        # Buscamos no banco pelo email
        user = User.query.filter_by(email=email_login).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Login realizado com sucesso!', 'success')
            
            # Redirecionamento baseado na role
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'professor':
                return redirect(url_for('professor_dashboard'))
            else:
                return redirect(url_for('aluno_dashboard', aluno_id=user.id))
        else:
            flash('E-mail ou senha incorretos!', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu com sucesso.', 'success')
    return redirect(url_for('home'))

@app.route('/admin_dashboard', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('home'))

    # Lógica de exclusão/rejeição (caso ainda precise remover alguém)
    if request.method == 'POST' and 'user_id' in request.form:
        user_id = request.form.get('user_id')
        acao = request.form.get('acao')
        usuario = User.query.get(user_id)
        if usuario and acao == 'rejeitar':
            db.session.delete(usuario)
            db.session.commit()
            flash(f'Usuário {usuario.username} removido.', 'warning')
        return redirect(url_for('admin_dashboard'))

    # --- AQUI ESTÁ A MUDANÇA PRINCIPAL ---
    # Buscamos TODOS os alunos cadastrados, sem filtrar por is_approved
    alunos = User.query.filter_by(role='aluno').all() 
    
    # Busca professores e turmas
    professores = User.query.filter_by(role='professor').all()
    turmas = db.session.query(
    Turma,
    func.count(distinct(Mensalidade.aluno_id)).label('total_alunos'),

    func.count(
        distinct(
            case(
                (Mensalidade.status != 'Pago', Mensalidade.aluno_id)
            )
        )
    ).label('inadimplentes')

).outerjoin(
    Mensalidade, Mensalidade.turma_id == Turma.id
).group_by(
    Turma.id
).all()


    
    # Dados financeiros
    contas_pagar = ContasPagar.query.all()
    mensalidades = Mensalidade.query.all()

    total_pagar = sum([c.valor for c in contas_pagar if c.status == 'Pendente'])
    total_receber = sum([m.valor for m in mensalidades if m.status == 'Pendente'])
    saldo_estimado = total_receber - total_pagar

    return render_template('admin_dashboard.html',
                           alunos=alunos, # Esta lista agora contém todos
                           professores=professores,
                           turmas=turmas,
                           contas_pagar=contas_pagar,
                           mensalidades=mensalidades,
                           total_pagar=total_pagar,
                           total_receber=total_receber,
                           saldo_estimado=saldo_estimado)


@app.route('/gerar_mensalidades_lote', methods=['POST'])
@login_required
def gerar_mensalidades_lote():
    if not current_user.is_admin:
        return redirect(url_for('home'))

    alunos_ids = request.form.getlist('alunos_ids')
    mes_referencia = request.form.get('mes_referencia')  # YYYY-MM
    valor = float(request.form.get('valor'))

    if not alunos_ids:
        flash('Selecione pelo menos um aluno!', 'danger')
        return redirect(url_for('admin_dashboard'))

    try:
        count = 0

        for aluno_id in alunos_ids:
            # 🔹 busca todas as matrículas ativas do aluno
            matriculas = Matricula.query.filter_by(user_id=aluno_id).all()

            for m in matriculas:
                # 🔹 evita mensalidade duplicada por aluno/turma/mês
                existente = Mensalidade.query.filter_by(
                    aluno_id=aluno_id,
                    turma_id=m.turma_id,
                    mes=mes_referencia
                ).first()

                if existente:
                    continue

                nova_mensalidade = Mensalidade(
                    aluno_id=aluno_id,
                    turma_id=m.turma_id,
                    professor_id=m.turma.professor_id,
                    mes=mes_referencia,
                    valor=valor,
                    status='Pendente',
                    data_matricula=m.data_matricula.date()
                )

                db.session.add(nova_mensalidade)
                count += 1

        db.session.commit()
        flash(f'{count} mensalidades geradas com sucesso!', 'success')

    except Exception as e:
        db.session.rollback()
        print(f"ERRO AO GERAR MENSALIDADES: {e}")
        flash('Erro ao gerar mensalidades.', 'danger')

    return redirect(url_for('admin_dashboard'))



COMISSAO_PERCENTUAL = 40  # 40%


from sqlalchemy import func

COMISSAO_PERCENTUAL = 40

from sqlalchemy.orm import aliased

COMISSAO_PERCENTUAL = 40

@app.route('/relatorio_financeiro_professor')
@login_required
def relatorio_financeiro_professor():

    mes = request.args.get('mes')  # formato YYYY-MM

    Professor = aliased(User)
    Aluno = aliased(User)

    query = db.session.query(
        Professor.username.label('professor'),
        Aluno.username.label('aluno'),
        Turma.nome.label('turma'),
        Mensalidade.mes,
        Mensalidade.valor,
        Mensalidade.status
    ).join(
        Professor, Professor.id == Mensalidade.professor_id
    ).join(
        Aluno, Aluno.id == Mensalidade.aluno_id
    ).join(
        Turma, Turma.id == Mensalidade.turma_id
    )

    if mes:
        query = query.filter(Mensalidade.mes == mes)

    resultados = query.order_by(
        Professor.username,
        Aluno.username
    ).all()

    relatorio = {}

    for r in resultados:
        professor = r.professor

        if professor not in relatorio:
            relatorio[professor] = {
                'alunos': [],
                'total_recebido': 0,
                'comissao': 0
            }

        relatorio[professor]['alunos'].append({
            'aluno': r.aluno,
            'turma': r.turma,
            'mes': r.mes,
            'valor': r.valor,
            'status': r.status
        })

        if r.status == 'Pago':
            relatorio[professor]['total_recebido'] += r.valor

    # calcula comissão
    for professor in relatorio:
        total = relatorio[professor]['total_recebido']
        relatorio[professor]['comissao'] = total * COMISSAO_PERCENTUAL / 100

    return render_template(
        'relatorio_financeiro_professor.html',
        relatorio=relatorio,
        mes=mes,
        percentual=COMISSAO_PERCENTUAL
    )



@app.route('/professor_dashboard')
@login_required
def professor_dashboard():
    if current_user.role != 'professor':
        flash('Acesso negado!')
        return redirect(url_for('home'))
    
    # Busca as turmas do professor
    turmas = Turma.query.filter_by(professor_id=current_user.id).all()
    
    # Busca TODOS os alunos cadastrados para o dropdown de matrícula
    todos_alunos = User.query.filter_by(role='aluno').all()
    
    return render_template('professor_dashboard.html', 
                           turmas=turmas, 
                           todos_alunos=todos_alunos) # Enviando a lista para o HTML

@app.route('/aluno_dashboard')
@login_required
def aluno_dashboard():
    # Garante que apenas alunos acessem esta rota
    if current_user.role != 'aluno':
        return redirect(url_for('home'))

    # CORREÇÃO AQUI: Mudamos de user_id para aluno_id para bater com seu modelo Mensalidade
    mensalidades = Mensalidade.query.filter_by(aluno_id=current_user.id).order_by(Mensalidade.mes.desc()).all()
    
    # Busca o histórico para o cálculo de frequência
    # Aqui continua user_id porque na sua classe Presenca a coluna chama-se user_id
    historico = Presenca.query.filter_by(user_id=current_user.id).all()
    
    total_aulas = len(historico)
    presencas = len([p for p in historico if p.presente])
    frequencia = (presencas / total_aulas * 100) if total_aulas > 0 else 0

    return render_template('aluno_dashboard.html', 
                           mensalidades=mensalidades, 
                           frequencia=frequencia,
                           historico=historico)

@app.route('/marcar_pago_conta/<int:conta_id>', methods=['POST'])
@login_required
def marcar_pago_conta(conta_id):
    conta = ContasPagar.query.get_or_404(conta_id)
    conta.status = 'Pago'
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/marcar_pago_mensalidade/<int:mensalidade_id>', methods=['POST'])
@login_required
def marcar_pago_mensalidade(mensalidade_id):
    mensalidade = Mensalidade.query.get_or_404(mensalidade_id)
    mensalidade.status = 'Pago'
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

def gerar_mensalidades():
    with app.app_context():
        hoje = datetime.now()
        proximo_mes = (hoje.replace(day=1) + timedelta(days=32)).replace(day=1)
        # Lógica de geração automática aqui...
        db.session.commit()

# Configurar o agendador
scheduler = BackgroundScheduler()
scheduler.add_job(gerar_mensalidades, 'cron', day=1, hour=0)
scheduler.start()

@app.route('/criar_turma', methods=['POST'])
@login_required
def criar_turma():
    if not current_user.is_admin:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('home'))
    
    nome = request.form.get('nome')
    professor_id = request.form.get('professor_id')
    
    if nome and professor_id:
        nova_turma = Turma(nome=nome, professor_id=professor_id)
        db.session.add(nova_turma)
        db.session.commit()
        flash(f'Turma "{nome}" criada com sucesso!', 'success')
    else:
        flash('Preencha todos os campos!', 'warning')
        
    return redirect(url_for('admin_dashboard'))

@app.route('/alterar_status_turma/<int:id>', methods=['POST'])
@login_required
def alterar_status_turma(id):
    if not current_user.is_admin:
        return redirect(url_for('home'))
    
    turma = Turma.query.get_or_404(id)
    # Inverte o status: se está ativa, inativa. Se está inativa, reativa.
    turma.ativa = not turma.ativa 
    db.session.commit()
    
    status_texto = "ativada" if turma.ativa else "inativada/arquivada"
    flash(f'Turma "{turma.nome}" foi {status_texto} com sucesso!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/remove_aluno/<int:turma_id>', methods=['POST'])
@login_required
def remove_aluno(turma_id):
    if current_user.role != 'professor' and not current_user.is_admin:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('home'))

    aluno_id = request.form.get('aluno_id')
    
    # Se você estiver usando a classe 'Matricula' (Associação Direta):
    matricula = Matricula.query.filter_by(user_id=aluno_id, turma_id=turma_id).first()
    
    if matricula:
        try:
            db.session.delete(matricula)
            
            # Opcional: Registrar a desmatrícula no histórico
            historico = HistoricoMatricula(aluno_id=aluno_id, turma_id=turma_id, acao='Desmatrícula')
            db.session.add(historico)
            
            db.session.commit()
            flash('Aluno desmatriculado com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao remover: {e}', 'danger')
    else:
        flash('Matrícula não encontrada.', 'warning')

    return redirect(url_for('professor_dashboard'))

@app.route('/salvar_chamada/<int:turma_id>', methods=['POST'])
@login_required
def salvar_chamada(turma_id):
    alunos_presentes = request.form.getlist('alunos_presenca')
    data_hj = datetime.now().date()

    try:
        # 1. Remove presenças anteriores da mesma turma e data
        Presenca.query.filter_by(
            turma_id=turma_id,
            data_aula=data_hj
        ).delete()

        # 2. Busca os alunos matriculados corretamente
        matriculas = Matricula.query.filter_by(turma_id=turma_id).all()

        for m in matriculas:
            presente = str(m.user_id) in alunos_presentes

            nova_presenca = Presenca(
                user_id=m.user_id,
                turma_id=turma_id,
                data_aula=data_hj,
                presente=presente
            )
            db.session.add(nova_presenca)

        db.session.commit()
        flash('Chamada realizada com sucesso!', 'success')

    except Exception as e:
        db.session.rollback()
        print(f"ERRO AO SALVAR PRESENÇA: {e}")
        flash('Erro ao salvar presença.', 'danger')

    return redirect(url_for('professor_dashboard'))

@app.route('/historico_presenca/<int:aluno_id>')
@login_required
def historico_presenca(aluno_id):
    # Garante que professores ou admin vejam o histórico
    if current_user.role == 'aluno' and current_user.id != aluno_id:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('home'))

    aluno = User.query.get_or_404(aluno_id)
    # Busca as presenças ordenadas pela data mais recente
    historico = Presenca.query.filter_by(user_id=aluno_id).all()
    
    # Cálculo simples de frequência
    total_aulas = len(historico)
    total_presencas = len([p for p in historico if p.presente])
    frequencia = (total_presencas / total_aulas * 100) if total_aulas > 0 else 0

    return render_template('historico_presenca.html', 
                           aluno=aluno, 
                           historico=historico, 
                           frequencia=frequencia)

@app.route('/adicionar_conta', methods=['POST'])
@login_required
def adicionar_conta():
    if not current_user.is_admin:
        return redirect(url_for('home'))

    descricao = request.form.get('descricao')
    valor = request.form.get('valor')
    vencimento_raw = request.form.get('vencimento')

    if descricao and valor and vencimento_raw:
        try:
            vencimento = datetime.strptime(vencimento_raw, '%Y-%m-%d').date()
            nova_conta = ContasPagar(
                descricao=descricao,
                valor=float(valor),
                vencimento=vencimento,
                status='Pendente'
            )
            db.session.add(nova_conta)
            db.session.commit()
            flash('Conta adicionada com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar conta: {e}', 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/setup_admin')
def setup_admin():
    # Dados do novo administrador
    nome_adm = "Administrador Céu de Gaia"
    email_adm = "admin@admin.com" # <--- Seu e-mail de login
    senha_adm = "5253545590"               # <--- Sua senha
    
    # Verifica se este e-mail já existe para evitar erro de duplicidade
    user_exists = User.query.filter_by(email=email_adm).first()
    if user_exists:
        return f"O administrador com o e-mail {email_adm} já está cadastrado!"

    # Gera o hash da senha
    hashed_password = bcrypt.generate_password_hash(senha_adm).decode('utf-8')
    
    # Cria o objeto com a nova lógica (Email como login, Nome no username)
    novo_admin = User(
        username=nome_adm,       # Aqui fica o Nome Completo
        email=email_adm,          # Aqui fica o E-mail de login
        password=hashed_password,
        role='professor',
        is_approved=True,
        is_admin=True,
        nome_contato_emergencia='ADMINISTRADOR SISTEMA'
    )
    
    try:
        db.session.add(novo_admin)
        db.session.commit()
        return f"Administrador {nome_adm} criado com sucesso! Use o e-mail {email_adm} para logar."
    except Exception as e:
        db.session.rollback()
        return f"Erro ao criar administrador: {e}"
    

@app.route('/cadastrar_professor', methods=['POST'])
@login_required
def cadastrar_professor():
    if not current_user.is_admin:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('home'))

    nome = request.form.get('nome')
    email = request.form.get('email')
    senha = request.form.get('senha')

    if User.query.filter_by(email=email).first():
        flash('Este e-mail já está cadastrado!', 'warning')
        return redirect(url_for('admin_dashboard'))

    hashed_password = bcrypt.generate_password_hash(senha).decode('utf-8')
    novo_prof = User(
        username=nome,
        email=email,
        password=hashed_password,
        role='professor',
        is_approved=True,
        is_admin=False
    )

    try:
        db.session.add(novo_prof)
        db.session.commit()
        flash(f'Professor(a) {nome} cadastrado(a) com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao cadastrar: {e}', 'danger')

    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)