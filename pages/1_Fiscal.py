import streamlit as st
import utils
import uuid
from datetime import datetime
import os
import pandas as pd

st.set_page_config(page_title="Fiscal - FUNEAS", layout="wide", page_icon="📋")
utils.menu_lateral()

if not st.session_state.get("logado"):
    st.warning("Acesso negado. Faça login."); st.stop()

st.title("📋 Área do Fiscal")
st.caption(f"Usuário: {st.session_state['usuario']}")
st.divider()

# --- ABAS ---
tab_novo, tab_pend = st.tabs(["📝 Nova Ocorrência", "🗑️ Gerenciar Pendências"])

# 1. SELEÇÃO DE CONTRATO (GLOBAL)
contratos = utils.listar_contratos_do_usuario(st.session_state["usuario"], st.session_state["perfil"])
if not contratos:
    st.warning("Sem contratos vinculados."); st.stop()

mapa = {f"{c['numero']} - {c['empresa']} ({c['unidade']})": c for c in contratos}

# --- ABA 1: NOVO REGISTRO ---
with tab_novo:
    # Seleção do Contrato
    sel = st.selectbox("Selecione o Contrato", list(mapa.keys()))
    dados_c = mapa[sel]

    # Seleção do Setor
    lista_setores = utils.listar_setores(dados_c['unidade'])
    opcoes_setores = [s['nome_setor'] for s in lista_setores]
    
    if not opcoes_setores:
        st.info(f"A unidade **{dados_c['unidade']}** não possui setores cadastrados. Será 'Geral'.")
        setor_selecionado = "Geral"
    else:
        setor_selecionado = st.selectbox("Onde ocorreu?", opcoes_setores)

    st.markdown("---")

    # Carrega Regras
    regras = utils.listar_regras_do_contrato(dados_c['id'])
    if not regras:
        st.error("Sem IMR configurado."); st.stop()
    df_regras = pd.DataFrame(regras)

    # --- AQUI ESTÁ A CORREÇÃO DO FILTRO ---
    # Tiramos os selectboxes de dentro do form para eles atualizarem em tempo real
    
    col_filtro1, col_filtro2 = st.columns(2)
    
    with col_filtro1:
        # 1. Escolhe Indicador (Isso dispara o refresh da página)
        grupos = df_regras['grupo'].unique()
        grupo_sel = st.selectbox("1. Selecione o Indicador", grupos)
    
    with col_filtro2:
        # 2. Filtra itens baseado na escolha acima
        itens = df_regras[df_regras['grupo'] == grupo_sel]
        
        # Correção visual do número quebrado (0.74999 -> 0.75)
        mapa_i = {f"{row['item']} ({float(row['pontos']):.2f} pts)": row for _, row in itens.iterrows()}
        
        sel_i = st.selectbox("2. Selecione a Infração", list(mapa_i.keys()))
        regra = mapa_i[sel_i]

    # --- FORMULÁRIO DE DADOS (Apenas para Obs e Foto) ---
    # O form agora só envolve o que precisa ser digitado, não o que filtra
    with st.form("ocorrrencia", clear_on_submit=True):
        
        st.info(f"**Resumo:** {dados_c['unidade']} > {setor_selecionado} | Pontuação: **{regra['pontos']}**")
        
        obs = st.text_area("Detalhes / Local Específico", height=130, placeholder="Descreva o fato...")
        foto = st.file_uploader("Foto Evidência", type=['jpg','png'])
            
        if st.form_submit_button("Registrar Ocorrência", use_container_width=True):
            if not obs:
                st.error("Preencha os detalhes da ocorrência.")
            else:
                path = "sem_foto"
                if foto:
                    ext = foto.name.split('.')[-1]
                    path = f"images/{uuid.uuid4()}.{ext}"
                    with open(path, "wb") as f: f.write(foto.getbuffer())
                
                nova = {
                    "id": str(uuid.uuid4()), "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "unidade": dados_c['unidade'], "setor": setor_selecionado,
                    "contrato_id": dados_c['id'], "contrato_nome": f"{dados_c['numero']} - {dados_c['empresa']}",
                    "fiscal": st.session_state["usuario"], "regra_id": regra['id'],
                    "grupo_indicador": regra['grupo'], "descricao_infracao": regra['item'],
                    "pontos": regra['pontos'], "descricao_obs": obs, "status": "Pendente",
                    "foto_path": path, "justificativa_gestor": ""
                }
                utils.salvar_ocorrencia(nova)
                st.toast("Registrado com Sucesso!", icon="✅")

# --- ABA 2: GERENCIAR PENDÊNCIAS ---
with tab_pend:
    st.markdown("### Minhas Ocorrências Pendentes")
    df_all = utils.carregar_ocorrencias()
    
    if not df_all.empty:
        # Filtra apenas as pendentes DO USUÁRIO logado
        meus_pendentes = df_all[
            (df_all['fiscal'] == st.session_state['usuario']) & 
            (df_all['status'] == 'Pendente')
        ]
        
        if meus_pendentes.empty:
            st.info("Você não tem pendências.")
        else:
            for _, row in meus_pendentes.iterrows():
                with st.expander(f"{row['data_hora']} - {row['descricao_infracao']}"):
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"**Local:** {row['unidade']} ({row['setor']})")
                    c1.write(f"**Obs:** {row['descricao_obs']}")
                    
                    if c2.button("🗑️ Excluir", key=f"del_own_{row['id']}", type="primary"):
                        utils.excluir_ocorrencia(row['id'])
                        st.success("Apagado.")
                        st.rerun()
    else:
        st.info("Sem registros.")