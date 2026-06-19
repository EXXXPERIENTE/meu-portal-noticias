# importar_dados.py
import json
from app import app, db


def importar_dados():
    # Pega o backup mais recente
    import os
    arquivos = [f for f in os.listdir('.') if f.startswith('backup_') and f.endswith('.json')]

    if not arquivos:
        print("❌ Nenhum backup encontrado!")
        return

    arquivo = sorted(arquivos)[-1]
    print(f"📂 Lendo: {arquivo}")

    with open(arquivo, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    with app.app_context():
        for nome_tabela, registros in dados.items():
            if not registros:
                continue

            print(f"📥 Importando {nome_tabela}...")

            # Pega o modelo correto
            modelo = None
            if nome_tabela == 'noticia':
                from app import Noticia
                modelo = Noticia
            elif nome_tabela == 'comentario':
                from app import Comentario
                modelo = Comentario
            elif nome_tabela == 'like':
                from app import Like
                modelo = Like
            elif nome_tabela == 'inscrito':
                from app import Inscrito
                modelo = Inscrito
            else:
                print(f"   ⚠️ Tabela {nome_tabela} ignorada")
                continue

            count = 0
            for item in registros:
                item.pop('id', None)
                try:
                    novo = modelo(**item)
                    db.session.add(novo)
                    count += 1
                except Exception as e:
                    print(f"   Erro: {str(e)[:50]}")

            db.session.commit()
            print(f"   ✅ {count} registros importados!")

        print("\n🎉 Importação concluída!")


if __name__ == "__main__":
    importar_dados()