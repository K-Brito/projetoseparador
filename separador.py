import os
import subprocess
import sys
import mysql.connector 


def conectar_banco():
    # Configure aqui os dados de acesso ao seu MySQL local
    return mysql.connector.connect(
        host="localhost",
        user="root",  # Usuário padrão do MySQL
        password="1234",  # Coloque a senha do seu banco aqui (se houver)
        database="separador",
    )


def salvar_status_inicial(arquivo):
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        comando_sql = (
            "INSERT INTO processamentos (nome_musica, caminho, status) VALUES (%s, %s, %s)"
        )
        # Extrai apenas o nome do arquivo para não salvar o caminho gigante
        nome_arquivo = os.path.basename(arquivo)
        cursor.execute(comando_sql, (nome_arquivo, arquivo, "Processando"))
        conexao.commit()

        # Retorna o ID gerado para podermos atualizar o status depois
        id_registro = cursor.lastrowid
        cursor.close()
        conexao.close()
        return id_registro
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível gravar no banco de dados: {e}")
        return None


def atualizar_status_final(id_registro, novo_status):
    if id_registro is None:
        return
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        comando_sql = "UPDATE processamentos SET status = %s WHERE id = %s"
        cursor.execute(comando_sql, (novo_status, id_registro))
        conexao.commit()
        cursor.close()
        conexao.close()
    except Exception as e:
        print(f"⚠️ Erro ao atualizar o banco de dados: {e}")


def separar_audio(caminho_da_musica):
    if not os.path.exists(caminho_da_musica):
        print(f"❌ Erro: O arquivo '{caminho_da_musica}' não foi encontrado.")
        return

    # 1. Registra o início no Banco de Dados
    id_db = salvar_status_inicial(caminho_da_musica)

    print("\n🎵 Iniciando a separação de alta velocidade...")
    print(
        "⚡ Processando com htdemucs e forçando a exportação direta para MP3..."
    )

    comando = [
        sys.executable,
        "-m",
        "demucs",
        "-n",
        "htdemucs",
        "-j",
        "4",
        "--mp3",
        "--two-stems=vocals",
        caminho_da_musica,
    ]

    try:
        subprocess.run(comando, check=True)
        print("\n✅ Concluído com sucesso!")
        print(
            "📂 Procure pela pasta 'separated' dentro da pasta do seu projeto."
        )

        # 2. Atualiza no banco para Concluído
        atualizar_status_final(id_db, "Concluído")

    except subprocess.CalledProcessError:
        print("\n❌ Ocorreu um erro no processamento do Demucs.")

        # 3. Se der erro, atualiza no banco para Erro
        atualizar_status_final(id_db, "Erro")


if __name__ == "__main__":
    print("=== SEPARADOR DE AUDIO IA + BANCO DE DADOS ===")

    caminho = input("Digite ou arraste o caminho do arquivo de música: ")
    caminho = caminho.strip().strip('"').strip("'")

    separar_audio(caminho)