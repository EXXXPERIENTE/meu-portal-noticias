# migrar_banco_curiosidades.py
import sqlite3
import os


def migrar_banco():
    """Adiciona suporte para categoria 'curiosidades' sem perder dados"""

    # Conectar ao banco existente
    conn = sqlite3.connect('noticias.db')
    cursor = conn.cursor()

    print("🔍 Verificando estrutura do banco de dados...")

    # Verificar se a coluna 'categoria' aceita a nova categoria
    cursor.execute("PRAGMA table_info(noticia)")
    colunas = cursor.fetchall()

    # Verificar as categorias existentes
    cursor.execute("SELECT DISTINCT categoria FROM noticia")
    categorias_existentes = [row[0] for row in cursor.fetchall()]
    print(f"📋 Categorias atuais: {categorias_existentes}")

    # A coluna categoria já existe? (deve existir)
    coluna_categoria = [c for c in colunas if c[1] == 'categoria']
    if coluna_categoria:
        print("✅ Coluna 'categoria' já existe")

        # Verificar o tipo da coluna (deve ser TEXT)
        tipo_atual = coluna_categoria[0][2]
        print(f"📝 Tipo atual da coluna categoria: {tipo_atual}")

        # Verificar se a categoria 'curiosidades' já está sendo usada
        if 'curiosidades' in categorias_existentes:
            print("✅ Categoria 'curiosidades' já existe no banco!")
        else:
            print("📌 Categoria 'curiosidades' não encontrada. O banco está pronto para aceitá-la!")
            print("   Você pode criar novas postagens com a categoria 'curiosidades'")

    # Verificar outras colunas importantes
    colunas_nomes = [c[1] for c in colunas]

    # Adicionar coluna 'imagem' se não existir
    if 'imagem' not in colunas_nomes:
        print("📸 Adicionando coluna 'imagem'...")
        cursor.execute("ALTER TABLE noticia ADD COLUMN imagem TEXT")
        print("✅ Coluna 'imagem' adicionada")

    # Adicionar coluna 'visualizacoes' se não existir
    if 'visualizacoes' not in colunas_nomes:
        print("👁️ Adicionando coluna 'visualizacoes'...")
        cursor.execute("ALTER TABLE noticia ADD COLUMN visualizacoes INTEGER DEFAULT 0")
        print("✅ Coluna 'visualizacoes' adicionada")

    # Verificar se a tabela 'comentario' existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='comentario'")
    if not cursor.fetchone():
        print("💬 Criando tabela 'comentario'...")
        cursor.execute("""
            CREATE TABLE comentario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                noticia_id INTEGER NOT NULL,
                nome TEXT NOT NULL,
                email TEXT,
                conteudo TEXT NOT NULL,
                data TIMESTAMP,
                aprovado BOOLEAN DEFAULT 0,
                FOREIGN KEY (noticia_id) REFERENCES noticia (id)
            )
        """)
        print("✅ Tabela 'comentario' criada")

    # Verificar se a tabela 'like' existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='like'")
    if not cursor.fetchone():
        print("❤️ Criando tabela 'like'...")
        cursor.execute("""
            CREATE TABLE "like" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                noticia_id INTEGER NOT NULL,
                ip_usuario TEXT NOT NULL,
                data TIMESTAMP,
                FOREIGN KEY (noticia_id) REFERENCES noticia (id)
            )
        """)
        print("✅ Tabela 'like' criada")

    # Verificar se a tabela 'inscrito' existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inscrito'")
    if not cursor.fetchone():
        print("📧 Criando tabela 'inscrito'...")
        cursor.execute("""
            CREATE TABLE inscrito (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                data_inscricao TIMESTAMP,
                ativo BOOLEAN DEFAULT 1
            )
        """)
        print("✅ Tabela 'inscrito' criada")

    # Verificar se a tabela 'admin' existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='admin'")
    if not cursor.fetchone():
        print("🔐 Criando tabela 'admin'...")
        cursor.execute("""
            CREATE TABLE admin (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)
        print("✅ Tabela 'admin' criada")

        # Inserir admin padrão
        from werkzeug.security import generate_password_hash
        cursor.execute("INSERT INTO admin (username, password_hash) VALUES (?, ?)",
                       ('admin', generate_password_hash('admin123')))
        print("✅ Usuário admin criado (admin/admin123)")

    # Salvar alterações
    conn.commit()

    # Mostrar estatísticas
    cursor.execute("SELECT COUNT(*) FROM noticia")
    total_noticias = cursor.fetchone()[0]
    print(f"\n📊 Estatísticas do banco:")
    print(f"   - Total de notícias: {total_noticias}")

    cursor.execute("SELECT categoria, COUNT(*) FROM noticia GROUP BY categoria")
    for categoria, count in cursor.fetchall():
        print(f"   - {categoria}: {count} notícia(s)")

    conn.close()

    print("\n🎉 Migração concluída com sucesso!")
    print("✅ Nenhum dado foi perdido!")
    print("🚀 Agora você pode usar a nova categoria 'curiosidades'")


if __name__ == "__main__":
    migrar_banco()