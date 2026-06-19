# importar_para_railway.py
import json
import os
import importlib
import sys


def encontrar_modelos():
    """Tenta encontrar automaticamente os modelos"""

    # Lista de possíveis nomes de arquivos de modelos
    possiveis_nomes = ['models', 'modelos', 'database', 'db', 'schema']

    for nome in possiveis_nomes:
        try:
            modulo = importlib.import_module(nome)
            print(f"✅ Modelos encontrados em: {nome}.py")
            return modulo
        except ModuleNotFoundError:
            continue

    # Se não encontrar, tenta importar do app
    try:
        from app import db, Noticia, Comentario, Like
        return {'db': db, 'Noticia': Noticia, 'Comentario': Comentario, 'Like': Like}
    except ImportError:
        pass

    print("❌ Não foi possível encontrar os modelos!")
    print("   Arquivos disponíveis:")
    for arquivo in os.listdir('.'):
        if arquivo.endswith('.py'):
            print(f"   - {arquivo}")

    return None


def importar_dados():
    """Importa dados do JSON para o PostgreSQL"""

    # Pega o JSON mais recente
    arquivos = [f for f in os.listdir('.') if f.startswith('backup_') and f.endswith('.json')]
    if not arquivos:
        print("❌ Nenhum arquivo de backup encontrado!")
        print("   Execute primeiro: python migrar_dados.py")
        return

    # Pega o mais recente
    arquivo = sorted(arquivos)[-1]
    print(f"📂 Lendo arquivo: {arquivo}")

    with open(arquivo, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    # Tenta importar o app
    try:
        from app import app, db
    except ImportError:
        try:
            from main import app, db
        except ImportError:
            print("❌ Arquivo app.py ou main.py não encontrado!")
            return

    with app.app_context():
        # Verifica qual banco está usando
        url_banco = app.config['SQLALCHEMY_DATABASE_URI']
        print(f"🔍 Banco atual: {url_banco}")

        if 'sqlite' in url_banco:
            print("⚠️ Você está no SQLite local, não no Railway!")
            print("   Para importar no Railway, faça deploy primeiro.")
            print("   Ou configure DATABASE_URL para o PostgreSQL do Railway.")
            return

        print("✅ Conectado ao PostgreSQL - Importando dados...")

        # Tenta importar os modelos
        modelos = encontrar_modelos()
        if not modelos:
            return

        # Verifica quais tabelas existem
        print(f"📊 Dados disponíveis: {list(dados.keys())}")

        # Tenta importar cada tabela
        for nome_tabela, registros in dados.items():
            print(f"\n📋 Processando tabela: {nome_tabela}")
            print(f"   {len(registros)} registros encontrados")

            if not registros:
                print("   ⏭️  Sem dados para importar")
                continue

            try:
                # Tenta encontrar a classe do modelo
                modelo_classe = None

                # Tenta vários nomes possíveis
                possiveis_nomes = [
                    nome_tabela,  # ex: 'noticia'
                    nome_tabela.capitalize(),  # ex: 'Noticia'
                    nome_tabela.title(),  # ex: 'Noticia'
                    nome_tabela.replace('_', ''),  # ex: 'noticias' -> 'noticias'
                    nome_tabela[:-1] if nome_tabela.endswith('s') else nome_tabela  # 'noticias' -> 'noticia'
                ]

                # Procura nos modelos
                for attr in dir(modelos):
                    if attr in possiveis_nomes or attr.lower() in possiveis_nomes:
                        modelo_classe = getattr(modelos, attr)
                        if hasattr(modelo_classe, '__tablename__'):
                            break

                if not modelo_classe:
                    print(f"   ⚠️  Modelo não encontrado para: {nome_tabela}")
                    continue

                # Importa os dados
                count = 0
                for item in registros:
                    # Remove campos que não devem ser inseridos
                    item.pop('id', None)  # Deixa o banco gerar
                    item.pop('_sa_instance_state', None)

                    try:
                        novo_registro = modelo_classe(**item)
                        db.session.add(novo_registro)
                        count += 1
                    except Exception as e:
                        print(f"   ⚠️  Erro ao importar item: {str(e)[:100]}")

                db.session.commit()
                print(f"   ✅ {count} registros importados com sucesso!")

            except Exception as e:
                print(f"   ❌ Erro ao importar {nome_tabela}: {str(e)}")
                db.session.rollback()

        print("\n🎉 Importação concluída!")


if __name__ == "__main__":
    importar_dados()