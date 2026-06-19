from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import re

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'sua_chave_secreta_aqui_mude_para_algo_seguro')

# Configuração para upload de imagens
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Criar pasta para uploads
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ============================================
# CONFIGURAÇÃO DO BANCO DE DADOS - SEM DOTENV!
# ============================================
basedir = os.path.abspath(os.path.dirname(__file__))

# Tenta pegar DATABASE_URL da variável de ambiente (Railway)
# Se não existir, usa SQLite (local)
database_url = os.environ.get('DATABASE_URL')

if database_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    print("✅ Conectado ao PostgreSQL (Railway)")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "noticias.db")}'
    print("📁 Conectado ao SQLite (Local)")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

print(f"🔍 Banco: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")

db = SQLAlchemy(app)


# ============================================
# ROTA PARA SERVIR ARQUIVOS ESTÁTICOS
# ============================================
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)


# ============================================
# MODELOS
# ============================================
class Noticia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    imagem = db.Column(db.String(200), nullable=True)
    video_url = db.Column(db.String(200), nullable=True)
    visualizacoes = db.Column(db.Integer, default=0)
    data_publicacao = db.Column(db.DateTime, default=datetime.utcnow)


class Comentario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    noticia_id = db.Column(db.Integer, db.ForeignKey('noticia.id'), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    conteudo = db.Column(db.Text, nullable=False)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    aprovado = db.Column(db.Boolean, default=False)
    noticia = db.relationship('Noticia', backref=db.backref('comentarios', lazy=True))


class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    noticia_id = db.Column(db.Integer, db.ForeignKey('noticia.id'), nullable=False)
    ip_usuario = db.Column(db.String(50), nullable=False)
    data = db.Column(db.DateTime, default=datetime.utcnow)


class Inscrito(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    data_inscricao = db.Column(db.DateTime, default=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)


# ============================================
# FUNÇÃO PARA MIGRAÇÃO DO BANCO (SQLite)
# ============================================
def verificar_migrar_banco():
    try:
        import sqlite3
        conn = sqlite3.connect('noticias.db')
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(noticia)")
        colunas = [coluna[1] for coluna in cursor.fetchall()]

        if 'imagem' not in colunas:
            cursor.execute("ALTER TABLE noticia ADD COLUMN imagem TEXT")
        if 'visualizacoes' not in colunas:
            cursor.execute("ALTER TABLE noticia ADD COLUMN visualizacoes INTEGER DEFAULT 0")
        if 'video_url' not in colunas:
            cursor.execute("ALTER TABLE noticia ADD COLUMN video_url TEXT")

        conn.commit()
        conn.close()
        print("✅ Migração do SQLite verificada")
    except Exception as e:
        print(f"⚠️ Migração não necessária ou erro: {e}")


# ============================================
# CRIAR BANCO E ADMIN
# ============================================
with app.app_context():
    try:
        db.create_all()
        print("✅ Tabelas criadas/verificadas")

        # Verifica se é SQLite para migrar
        if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
            verificar_migrar_banco()

        # Criar admin se não existir
        if not Admin.query.filter_by(username='admin').first():
            admin = Admin(username='admin', password_hash=generate_password_hash('admin123'))
            db.session.add(admin)
            db.session.commit()
            print("✅ Usuário admin criado: admin / senha: admin123")

    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {str(e)}")


# ============================================
# FUNÇÕES AUXILIARES
# ============================================
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def converter_link_youtube(url):
    if not url:
        return None
    youtube_regex = r'(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&=%\?{\s]+)'
    match = re.match(youtube_regex, url)
    if match:
        video_id = match.group(4)
        return f"https://www.youtube.com/embed/{video_id}"
    return url


@app.context_processor
def utility_processor():
    return dict(converter_link_youtube=converter_link_youtube)


# ============================================
# ROTAS PRINCIPAIS
# ============================================
@app.route('/')
def index():
    tech_noticias = Noticia.query.filter_by(categoria='tecnologia').order_by(Noticia.data_publicacao.desc()).limit(
        10).all()
    saude_noticias = Noticia.query.filter_by(categoria='saude').order_by(Noticia.data_publicacao.desc()).limit(10).all()
    curiosidades_noticias = Noticia.query.filter_by(categoria='curiosidades').order_by(
        Noticia.data_publicacao.desc()).limit(10).all()

    return render_template('index.html',
                           tech_noticias=tech_noticias,
                           saude_noticias=saude_noticias,
                           curiosidades_noticias=curiosidades_noticias)


@app.route('/buscar')
def buscar():
    query = request.args.get('q', '')
    if query:
        noticias = Noticia.query.filter(
            (Noticia.titulo.contains(query)) | (Noticia.conteudo.contains(query))
        ).order_by(Noticia.data_publicacao.desc()).all()
    else:
        noticias = []
    return render_template('buscar.html', noticias=noticias, query=query)


@app.route('/noticia/<int:id>')
def ver_noticia(id):
    noticia = Noticia.query.get_or_404(id)
    noticia.visualizacoes += 1
    db.session.commit()

    comentarios = Comentario.query.filter_by(noticia_id=id, aprovado=True).order_by(Comentario.data.desc()).all()
    ip_usuario = request.remote_addr
    ja_curtiu = Like.query.filter_by(noticia_id=id, ip_usuario=ip_usuario).first() is not None
    total_likes = Like.query.filter_by(noticia_id=id).count()

    return render_template('ver_noticia.html', noticia=noticia, comentarios=comentarios,
                           ja_curtiu=ja_curtiu, total_likes=total_likes)


@app.route('/comentar/<int:noticia_id>', methods=['POST'])
def comentar(noticia_id):
    nome = request.form.get('nome')
    email = request.form.get('email')
    conteudo = request.form.get('conteudo')

    if nome and conteudo:
        comentario = Comentario(noticia_id=noticia_id, nome=nome, email=email,
                                conteudo=conteudo, aprovado=False)
        db.session.add(comentario)
        db.session.commit()
        flash('Comentário enviado! Aguardando aprovação.', 'success')
    else:
        flash('Preencha nome e comentário!', 'danger')
    return redirect(url_for('ver_noticia', id=noticia_id))


@app.route('/like/<int:noticia_id>', methods=['POST'])
def like_noticia(noticia_id):
    ip_usuario = request.remote_addr
    like_existente = Like.query.filter_by(noticia_id=noticia_id, ip_usuario=ip_usuario).first()

    if like_existente:
        db.session.delete(like_existente)
        db.session.commit()
        total_likes = Like.query.filter_by(noticia_id=noticia_id).count()
        return jsonify({'liked': False, 'total': total_likes})
    else:
        like = Like(noticia_id=noticia_id, ip_usuario=ip_usuario)
        db.session.add(like)
        db.session.commit()
        total_likes = Like.query.filter_by(noticia_id=noticia_id).count()
        return jsonify({'liked': True, 'total': total_likes})


@app.route('/newsletter/inscrever', methods=['POST'])
def inscrever_newsletter():
    email = request.form.get('email')
    if not email:
        return jsonify({'success': False, 'message': 'Email é obrigatório'})

    inscrito = Inscrito.query.filter_by(email=email).first()
    if inscrito:
        if not inscrito.ativo:
            inscrito.ativo = True
            db.session.commit()
            return jsonify({'success': True, 'message': 'Inscrição reativada!'})
        return jsonify({'success': False, 'message': 'Email já está inscrito!'})

    inscrito = Inscrito(email=email)
    db.session.add(inscrito)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Inscrição realizada com sucesso!'})


@app.route('/api/noticias')
def api_noticias():
    tech_noticias = Noticia.query.filter_by(categoria='tecnologia').order_by(Noticia.data_publicacao.desc()).limit(
        10).all()
    saude_noticias = Noticia.query.filter_by(categoria='saude').order_by(Noticia.data_publicacao.desc()).limit(10).all()
    curiosidades_noticias = Noticia.query.filter_by(categoria='curiosidades').order_by(
        Noticia.data_publicacao.desc()).limit(10).all()

    def formatar_noticia(n):
        return {
            'id': n.id, 'titulo': n.titulo,
            'data': n.data_publicacao.strftime('%d/%m/%Y às %H:%M'),
            'resumo': re.sub(r'<[^>]+>', '', n.conteudo)[:150] + '...',
            'imagem': n.imagem,
            'video_url': n.video_url,
            'categoria': n.categoria
        }

    return {
        'tecnologia': [formatar_noticia(n) for n in tech_noticias],
        'saude': [formatar_noticia(n) for n in saude_noticias],
        'curiosidades': [formatar_noticia(n) for n in curiosidades_noticias]
    }


# ============================================
# ROTAS ADMIN
# ============================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password_hash, password):
            session['logged_in'] = True
            session['username'] = username
            flash('Login realizado!', 'success')
            return redirect(url_for('admin_panel'))
        flash('Usuário ou senha incorretos!', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))


@app.route('/admin')
def admin_panel():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    noticias = Noticia.query.order_by(Noticia.data_publicacao.desc()).all()
    comentarios_pendentes = Comentario.query.filter_by(aprovado=False).count()
    inscritos_count = Inscrito.query.filter_by(ativo=True).count()
    return render_template('admin.html', noticias=noticias,
                           comentarios_pendentes=comentarios_pendentes,
                           inscritos_count=inscritos_count)


@app.route('/admin/nova', methods=['GET', 'POST'])
def nova_postagem():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        titulo = request.form['titulo']
        conteudo = request.form['conteudo']
        categoria = request.form['categoria']
        video_url = request.form.get('video_url')
        imagem = None

        if 'imagem' in request.files:
            file = request.files['imagem']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                imagem = f'/static/uploads/{filename}'

        if titulo and conteudo:
            noticia = Noticia(titulo=titulo, conteudo=conteudo, categoria=categoria, imagem=imagem, video_url=video_url)
            db.session.add(noticia)
            db.session.commit()
            flash('Notícia publicada!', 'success')
            return redirect(url_for('admin_panel'))
        flash('Preencha todos os campos!', 'danger')
    return render_template('nova_postagem.html')


@app.route('/admin/editar/<int:id>', methods=['GET', 'POST'])
def editar_postagem(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    noticia = Noticia.query.get_or_404(id)

    if request.method == 'POST':
        noticia.titulo = request.form['titulo']
        noticia.conteudo = request.form['conteudo']
        noticia.categoria = request.form['categoria']
        noticia.video_url = request.form.get('video_url')

        if 'imagem' in request.files:
            file = request.files['imagem']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                noticia.imagem = f'/static/uploads/{filename}'

        db.session.commit()
        flash('Notícia atualizada com sucesso!', 'success')
        return redirect(url_for('admin_panel'))

    return render_template('editar_postagem.html', noticia=noticia)


@app.route('/admin/excluir/<int:id>')
def excluir_postagem(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    noticia = Noticia.query.get_or_404(id)

    # Remover comentários
    comentarios = Comentario.query.filter_by(noticia_id=id).all()
    for comentario in comentarios:
        db.session.delete(comentario)

    # Remover likes
    likes = Like.query.filter_by(noticia_id=id).all()
    for like in likes:
        db.session.delete(like)

    # Remover imagem
    if noticia.imagem:
        try:
            nome_arquivo = os.path.basename(noticia.imagem)
            imagem_path = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
            if os.path.exists(imagem_path) and os.path.isfile(imagem_path):
                os.remove(imagem_path)
        except Exception as e:
            print(f"⚠️ Erro ao remover imagem: {e}")

    db.session.delete(noticia)
    db.session.commit()

    flash('Notícia e todos os dados associados foram excluídos com sucesso!', 'success')
    return redirect(url_for('admin_panel'))


@app.route('/admin/comentarios')
def admin_comentarios():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    pendentes = Comentario.query.filter_by(aprovado=False).order_by(Comentario.data.desc()).all()
    aprovados = Comentario.query.filter_by(aprovado=True).order_by(Comentario.data.desc()).limit(50).all()
    return render_template('admin_comentarios.html', pendentes=pendentes, aprovados=aprovados)


@app.route('/admin/comentario/aprovar/<int:id>')
def aprovar_comentario(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    comentario = Comentario.query.get_or_404(id)
    comentario.aprovado = True
    db.session.commit()
    flash('Comentário aprovado!', 'success')
    return redirect(url_for('admin_comentarios'))


@app.route('/admin/comentario/excluir/<int:id>')
def excluir_comentario(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    comentario = Comentario.query.get_or_404(id)
    db.session.delete(comentario)
    db.session.commit()
    flash('Comentário excluído!', 'success')
    return redirect(url_for('admin_comentarios'))


@app.route('/admin/newsletter')
def admin_newsletter():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    inscritos = Inscrito.query.filter_by(ativo=True).order_by(Inscrito.data_inscricao.desc()).all()
    return render_template('admin_newsletter.html', inscritos=inscritos)


@app.route('/admin/newsletter/enviar', methods=['POST'])
def enviar_newsletter():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    assunto = request.form.get('assunto')
    mensagem = request.form.get('mensagem')
    if not assunto or not mensagem:
        flash('Preencha assunto e mensagem!', 'danger')
        return redirect(url_for('admin_newsletter'))
    inscritos = Inscrito.query.filter_by(ativo=True).all()
    flash(f'Newsletter seria enviada para {len(inscritos)} inscritos.', 'info')
    return redirect(url_for('admin_newsletter'))


# ============================================
# SISTEMA DE LOGIN SEGURO
# ============================================
@app.route('/admin/alterar-senha', methods=['GET', 'POST'])
def alterar_senha():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        senha_atual = request.form.get('senha_atual')
        nova_senha = request.form.get('nova_senha')
        confirmar_senha = request.form.get('confirmar_senha')

        admin = Admin.query.filter_by(username=session['username']).first()

        if not check_password_hash(admin.password_hash, senha_atual):
            flash('❌ Senha atual incorreta!', 'danger')
            return redirect(url_for('alterar_senha'))

        if len(nova_senha) < 6:
            flash('❌ A nova senha deve ter pelo menos 6 caracteres!', 'danger')
            return redirect(url_for('alterar_senha'))

        if nova_senha != confirmar_senha:
            flash('❌ As novas senhas não coincidem!', 'danger')
            return redirect(url_for('alterar_senha'))

        admin.password_hash = generate_password_hash(nova_senha)
        db.session.commit()

        flash('✅ Senha alterada com sucesso! Faça login novamente.', 'success')
        session.pop('logged_in', None)
        return redirect(url_for('login'))

    return render_template('alterar_senha.html')


@app.route('/admin/perfil', methods=['GET', 'POST'])
def admin_perfil():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    admin = Admin.query.filter_by(username=session['username']).first()

    if request.method == 'POST':
        novo_usuario = request.form.get('username')

        if novo_usuario and novo_usuario != admin.username:
            existe = Admin.query.filter_by(username=novo_usuario).first()
            if existe:
                flash('❌ Este nome de usuário já existe!', 'danger')
                return redirect(url_for('admin_perfil'))
            admin.username = novo_usuario
            session['username'] = novo_usuario
            flash('✅ Nome de usuário alterado com sucesso!', 'success')

        db.session.commit()
        return redirect(url_for('admin_panel'))

    return render_template('admin_perfil.html', admin=admin)


# ============================================
# INICIAR APLICAÇÃO
# ============================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8888))
    app.run(debug=False, host='0.0.0.0', port=port)