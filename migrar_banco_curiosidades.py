# migrar_dados.py
import sqlite3
import json
import os
from datetime import datetime


def exportar_sqlite_para_json():
    """Exporta todos os dados do SQLite para um arquivo JSON"""

    print("📦 Exportando dados do SQLite...")

    # Verifica se o arquivo existe
    if not os.path.exists('noticias.db'):
        print("❌ Arquivo noticias.db não encontrado!")
        return False

    # Conecta ao SQLite
    conn = sqlite3.connect('noticias.db')
    conn.row_factory = sqlite3.Row  # Para acessar colunas por nome
    cursor = conn.cursor()

    # Pega todas as tabelas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tabelas = cursor.fetchall()

    dados = {}

    for tabela in tabelas:
        nome_tabela = tabela[0]
        print(f"  📋 Exportando tabela: {nome_tabela}")

        # Pega todos os dados da tabela
        cursor.execute(f"SELECT * FROM {nome_tabela}")
        rows = cursor.fetchall()

        # Converte para lista de dicionários
        dados[nome_tabela] = [dict(row) for row in rows]
        print(f"     ✅ {len(dados[nome_tabela])} registros")

    conn.close()

    # Salva em JSON
    nome_arquivo = f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(nome_arquivo, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n✅ Dados exportados com sucesso para: {nome_arquivo}")
    print(f"📊 Total de tabelas: {len(dados)}")

    return nome_arquivo


if __name__ == "__main__":
    exportar_sqlite_para_json()