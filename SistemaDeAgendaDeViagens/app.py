import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask import jsonify
from functools import wraps
from flask import session, redirect, url_for

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_super_secreta'
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, 'database.db')

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


#Criando classe usuário
class Usuario (UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)

#Criando classe viagem
class Viagem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(50), nullable=False)
    local = db.Column(db.String(200), nullable=False)
    motorista = db.Column(db.String(150), nullable=False)
    observacao = db.Column(db.String(300))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('tipo') != 'admin':
            print("Tipo na sessão:", session.get('tipo'))
            return redirect(url_for('calendario'))
        return f(*args, **kwargs)
    return decorated_function
    


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))   

def create_tables():
    with app.app_context():
        db.create_all()

        admin = Usuario.query.filter_by(username='admin').first()
        print("Admin encontrado:", admin)

        if not admin:
            admin = Usuario(
                username='admin',
                password='6@2Yj6mg',
                tipo='admin'
            )
            db.session.add(admin)
            db.session.commit()
        else:
            admin.tipo = 'admin'  # força corrigir
            db.session.commit()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_digitado = request.form.get('username', '').strip()
        senha_digitada = request.form.get('password', '').strip()

        print("Digitado:", username_digitado, senha_digitada)

        user = Usuario.query.filter_by(username=username_digitado).first()

        print("Usuário encontrado:", user)

        if user:
            print("Senha no banco:", user.password)

        if user and user.password == senha_digitada:
            login_user(user)
            session['usuario_id'] = user.id
            session['tipo'] = user.tipo
            print("Login realizado com sucesso!")
            return redirect(url_for('calendario'))

        print("Login falhou")
        return "Usuário ou senha incorretos"

    return render_template('login.html')  

@app.route('/calendario')
@login_required
def calendario():
    return render_template('calendario.html')

@app.route("/criar_banco")
def criar_banco():
    db.create_all()
    return "Banco criado!"

@app.route('/usuarios')
@login_required
@admin_required
def usuarios():
    lista_usuarios = Usuario.query.all()
    return render_template('usuarios.html', usuarios=lista_usuarios)

@app.route('/criar_usuario', methods=['POST'])
@login_required
@admin_required
def criar_usuario():

    username = request.form['username']
    senha = request.form['senha']
    tipo = request.form['tipo']

    novo = Usuario(username=username, password=senha, tipo=tipo)
    db.session.add(novo)
    db.session.commit()

    return redirect(url_for('usuarios'))

@app.route('/excluir_usuario/<int:id>')
@login_required
@admin_required
def excluir_usuario(id):

    usuario = Usuario.query.get(id)

    if usuario and usuario.username != "admin":
        db.session.delete(usuario)
        db.session.commit()

    return redirect(url_for('usuarios'))

@app.route('/salvar_viagem', methods=['POST'])
@login_required
def salvar_viagem():
    data = request.json.get('data')
    local = request.json.get('local')
    motorista = request.json.get('motorista')
    observacao = request.json.get('observacao')

    nova_viagem = Viagem(
        data=data,
        local=local,
        motorista=motorista,
        observacao=observacao
    )

    db.session.add(nova_viagem)
    db.session.commit()

    return jsonify({"status": "sucesso"})

@app.route('/buscar_viagens')
@login_required
def buscar_viagens():
    viagens = Viagem.query.all()

    lista_eventos = []

    for v in viagens:
        lista_eventos.append({
            "id": v.id,
            "title": f"{v.local} - {v.motorista}",
            "start": v.data,
            "extendedProps": {
                "local": v.local,
                "motorista": v.motorista,
                "observacao": v.observacao
            }
        })

    return jsonify(lista_eventos)

@app.route('/excluir_viagem/<int:id>', methods=['DELETE'])
@login_required
def excluir_viagem(id):
    viagem = Viagem.query.get(id)

    if viagem:
        db.session.delete(viagem)
        db.session.commit()
        return jsonify({"status": "excluido"})

    return jsonify({"status": "erro"})

@app.route('/motoristas')
@login_required
def motoristas():
    motoristas = db.session.query(Viagem.motorista).distinct().all()
    lista = [m[0] for m in motoristas]
    return jsonify(lista)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
print(app.url_map)

if __name__ == '__main__':
    create_tables()

    app.run(debug=True)
