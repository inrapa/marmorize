
# Sistema completo de monitoramento de performance - MARMORIZE

import streamlit as st
import pandas as pd
import datetime
import sqlite3

st.set_page_config(page_title="Monitoramento MARMORIZE", layout="wide")

st.title("📊 Sistema de Monitoramento de Vendas - MARMORIZE")

# --- Banco de Dados SQLite ---
conn = sqlite3.connect("marmorize.db", check_same_thread=False)
c = conn.cursor()

# Tabelas principais
c.execute("""
CREATE TABLE IF NOT EXISTS funcionarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL,
    data_admissao TEXT NOT NULL,
    participa_pacc TEXT DEFAULT 'Não',
    advertencias TEXT DEFAULT 'Não',
    raths INTEGER DEFAULT 0
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS metas_globais (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mes TEXT,
    valor_alvo REAL,
    percentual_itens_missao REAL,
    atingido REAL
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS metas_individuais (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    mes TEXT,
    meta_individual REAL,
    vendas_totais REAL,
    vendas_itens REAL,
    vendas_decorativos REAL
)
""")

conn.commit()

# --- Cadastro de Funcionário ---
st.sidebar.header("Cadastrar Funcionário")
with st.sidebar.form("cadastro_func"):
    nome = st.text_input("Nome do funcionário")
    data_admissao = st.date_input("Data de admissão", value=datetime.date.today())
    participa_pacc = st.radio("Participa de PACC?", ["Sim", "Não"])
    advertencias = st.radio("Advertência(s)?", ["Sim", "Não"])
    raths = st.number_input("Número de RATHs", min_value=0, step=1)
    cadastrar_func = st.form_submit_button("Cadastrar Funcionário")
    if cadastrar_func and nome:
        try:
            c.execute("INSERT INTO funcionarios (nome, data_admissao, participa_pacc, advertencias, raths) VALUES (?, ?, ?, ?, ?)",
                      (nome, data_admissao.isoformat(), participa_pacc, advertencias, raths))
            conn.commit()
            st.success("Funcionário cadastrado com sucesso!")
        except sqlite3.IntegrityError:
            st.warning("Funcionário já está cadastrado.")

# --- Cadastro de Metas Globais ---
st.sidebar.header("Cadastrar Meta Global")
with st.sidebar.form("cadastro_meta_global"):
    mes_ref = st.text_input("Mês de Referência (Ex: Jun/2025)")
    valor_alvo = st.number_input("Meta (Valor Alvo Global)", min_value=0.0, step=100.0)
    percentual_itens = st.number_input("Meta de Itens de Missão (%)", min_value=0.0, max_value=100.0, step=1.0)
    atingido = st.number_input("Valor Atingido Global", min_value=0.0, step=100.0)
    cadastrar_meta = st.form_submit_button("Cadastrar Meta Global")
    if cadastrar_meta and mes_ref:
        c.execute("INSERT INTO metas_globais (mes, valor_alvo, percentual_itens_missao, atingido) VALUES (?, ?, ?, ?)",
                  (mes_ref, valor_alvo, percentual_itens, atingido))
        conn.commit()
        st.success("Meta Global cadastrada!")

# --- Registro de Metas Individuais e Vendas ---
st.header("📌 Registrar Metas e Vendas por Funcionário")
c.execute("SELECT nome FROM funcionarios")
vendedores = [row[0] for row in c.fetchall()]

if vendedores:
    with st.form("form_metas_vendas"):
        vendedor = st.selectbox("Funcionário", vendedores)
        mes_ind = st.text_input("Mês de Referência (Ex: Jun/2025)")
        meta_func = st.number_input("Meta do Funcionário (R$)", min_value=0.0, step=100.0)
        vendas_total = st.number_input("Vendas Totais (R$)", min_value=0.0, step=100.0)
        vendas_itens = st.number_input("Vendas de Itens de Missão (R$)", min_value=0.0, step=100.0)
        vendas_decor = st.number_input("Vendas de Produtos Decorativos (R$)", min_value=0.0, step=100.0)
        cadastrar_metas = st.form_submit_button("Registrar Metas e Vendas")

        if cadastrar_metas:
            c.execute("INSERT INTO metas_individuais (nome, mes, meta_individual, vendas_totais, vendas_itens, vendas_decorativos) VALUES (?, ?, ?, ?, ?, ?)",
                      (vendedor, mes_ind, meta_func, vendas_total, vendas_itens, vendas_decor))
            conn.commit()
            st.success("Metas e vendas registradas!")

    # --- Relatório Individual ---
    st.subheader("📋 Relatório Individual por Funcionário")
    funcionario_sel = st.selectbox("Selecionar funcionário para análise", vendedores)
    mes_sel = st.selectbox("Selecionar mês", ["Todos"] + [row[0] for row in c.execute("SELECT DISTINCT mes FROM metas_individuais")])

    query = f"SELECT * FROM metas_individuais WHERE nome = ?"
    params = [funcionario_sel]
    if mes_sel != "Todos":
        query += " AND mes = ?"
        params.append(mes_sel)

    df_func = pd.read_sql_query(query, conn, params=params)
    if not df_func.empty:
        df_func["% Meta Atingida"] = (df_func["vendas_totais"] / df_func["meta_individual"] * 100).round(2)
        st.dataframe(df_func)

        c.execute("SELECT data_admissao FROM funcionarios WHERE nome = ?", (funcionario_sel,))
        admissao = datetime.datetime.fromisoformat(c.fetchone()[0]).date()
        anos = (datetime.date.today() - admissao).days // 365
        st.info(f"Fidelidade Premiada: {anos} ano(s) de empresa")

        c.execute("SELECT raths, participa_pacc, advertencias FROM funcionarios WHERE nome = ?", (funcionario_sel,))
        r, pacc, adv = c.fetchone()
        st.write(f"RATHs: {r}")
        st.write(f"Participa de PACC: {pacc}")
        st.write(f"Advertência(s): {adv}")
else:
    st.info("Cadastre ao menos um funcionário.")
