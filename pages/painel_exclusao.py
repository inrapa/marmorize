# Painel de Exclusão Segura - MARMORIZE V2

import streamlit as st
import sqlite3
import pandas as pd
import datetime

st.set_page_config(page_title="🔒 Painel de Exclusão MARMORIZE")

st.title("🔐 Painel Restrito de Exclusão de Dados")

# Autenticação de segurança
senha = st.text_input("Digite a senha de acesso:", type="password")
if senha != "marmorize2025":
    st.warning("Acesso restrito. Digite a senha correta.")
    st.stop()

conn = sqlite3.connect("marmorize.db", check_same_thread=False)
c = conn.cursor()

# Criação de tabela de log, se necessário
c.execute("""
CREATE TABLE IF NOT EXISTS log_exclusoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT,
    tipo TEXT,
    funcionario TEXT,
    mes TEXT
)
""")
conn.commit()

def registrar_log(tipo, funcionario, mes="-"):
    c.execute("INSERT INTO log_exclusoes (data, tipo, funcionario, mes) VALUES (?, ?, ?, ?)",
              (datetime.datetime.now().isoformat(), tipo, funcionario, mes))
    conn.commit()

# Backup automático (exportação CSV)
def fazer_backup():
    df1 = pd.read_sql_query("SELECT * FROM usuarios", conn)
    df2 = pd.read_sql_query("SELECT * FROM metas_individuais", conn)
    df1.to_csv("/mnt/data/backup_funcionarios.csv", index=False)
    df2.to_csv("/mnt/data/backup_vendas.csv", index=False)

# Exclusão completa
st.subheader("❌ Excluir Funcionário por Completo")
c.execute("SELECT nome FROM usuarios")
funcs = [row[0] for row in c.fetchall()]
if funcs:
    func = st.selectbox("Selecionar funcionário", funcs, key="excluir_total")
    if st.button("Excluir Funcionário e Vendas"):
        fazer_backup()
        registrar_log("Exclusão Total", func)
        c.execute("DELETE FROM usuarios WHERE nome = ?", (func,))
        c.execute("DELETE FROM metas_individuais WHERE nome = ?", (func,))
        conn.commit()
        st.success(f"Funcionário '{func}' excluído com sucesso.")
else:
    st.info("Nenhum funcionário disponível.")

# Exclusão por mês
st.subheader("📆 Excluir vendas de um mês específico")
func_mes = st.selectbox("Funcionário", funcs, key="func_mes")
c.execute("SELECT DISTINCT mes FROM metas_individuais WHERE nome = ?", (func_mes,))
meses = [row[0] for row in c.fetchall()]
if meses:
    mes_excluir = st.selectbox("Mês para excluir", meses)
    if st.button("Excluir Vendas do Mês"):
        fazer_backup()
        registrar_log("Exclusão Mês", func_mes, mes_excluir)
        c.execute("DELETE FROM metas_individuais WHERE nome = ? AND mes = ?", (func_mes, mes_excluir))
        conn.commit()
        st.success(f"Vendas de {mes_excluir} excluídas para {func_mes}.")
else:
    st.info("Funcionário sem registros mensais.")

# Redefinir dados (manter funcionário)
st.subheader("🔁 Redefinir Dados de Vendas (sem apagar funcionário)")
func_reset = st.selectbox("Funcionário", funcs, key="func_reset")
if st.button("Zerar Vendas e Metas"):
    fazer_backup()
    registrar_log("Zeramento Dados", func_reset)
    c.execute("DELETE FROM metas_individuais WHERE nome = ?", (func_reset,))
    conn.commit()
    st.success(f"Dados zerados com sucesso para {func_reset}.")

# Log
st.subheader("📜 Histórico de Exclusões")
df_log = pd.read_sql_query("SELECT * FROM log_exclusoes ORDER BY id DESC", conn)
if not df_log.empty:
    df_log["data"] = pd.to_datetime(df_log["data"]).dt.strftime("%d/%m/%Y %H:%M")
    st.dataframe(df_log, use_container_width=True)
else:
    st.info("Nenhuma exclusão registrada ainda.")
