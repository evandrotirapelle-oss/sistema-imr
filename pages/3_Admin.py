import streamlit as st
import utils
import pandas as pd

st.set_page_config(page_title="Admin - FUNEAS", layout="wide", page_icon="⚙️")
utils.menu_lateral()

if st.session_state.get("perfil") != "Admin": st.error("Restrito."); st.stop()

c_t, c_u = st.columns([3, 1])
c_t.title("⚙️ Admin"); c_u.markdown(f"👤 **{st.session_state['usuario']}**"); st.divider()

tabs = st.tabs(["🏥 Unidades", "📝 Contratos", "⚖️ Regras IMR", "💰 Multas", "👥 Usuários", "🔗 Vínculos", "🔐 Segurança"])

# --- UNIDADES ---
with tabs[0]:
    c1, c2 = st.columns(2)
    with c1:
        n = st.text_input("Nome da Unidade")
        if st.button("Adicionar Unidade") and n: utils.cadastrar_unidade(n); st.success("Ok!"); st.rerun()
    with c2:
        df_un = utils.carregar_df_sql("SELECT * FROM units")
        if not df_un.empty:
            uni_sel = st.selectbox("Sel. Unidade:", df_un['nome'].unique())
            ns = st.text_input("Novo Setor")
            if st.button("Add Setor") and ns: utils.cadastrar_setor(uni_sel, ns); st.success("Ok"); st.rerun()
            sts = utils.listar_setores(uni_sel)
            for s in sts:
                c_a, c_b = st.columns([4,1]); c_a.text(s['nome_setor'])
                if c_b.button("X", key=f"ds{s['id']}"): utils.excluir_setor(s['id']); st.rerun()
        else: st.warning("Cadastre unidades.")
    st.divider()
    if not df_un.empty:
        with st.expander("Ver Unidades"):
            for _, r in df_un.iterrows():
                k1, k2 = st.columns([4, 1]); k1.text(r['nome'])
                if k2.button("Excluir", key=f"du_{r['nome']}"): utils.excluir_unidade(r['nome']); st.rerun()

# --- CONTRATOS ---
with tabs[1]:
    with st.form("nc"):
        c1,c2,c3=st.columns([1,2,2]); n=c1.text_input("Nº"); u=c2.selectbox("Unid.", utils.carregar_df_sql("SELECT * FROM units")['nome'].tolist() or [])
        e=c3.text_input("Empresa")
        if st.form_submit_button("Salvar") and n and u and e: utils.cadastrar_contrato(n,u,e); st.rerun()
    st.dataframe(utils.carregar_df_sql("SELECT * FROM contracts"))
    df_c = utils.carregar_df_sql("SELECT * FROM contracts")
    if not df_c.empty:
         with st.expander("Excluir Contratos"):
            for _, r in df_c.iterrows():
                c1, c2 = st.columns([4,1]); c1.text(f"{r['numero']} - {r['empresa']}")
                if c2.button("X", key=f"del_c_{r['id']}"): utils.excluir_contrato(r['id']); st.rerun()

# --- REGRAS ---
with tabs[2]:
    cons=utils.listar_todos_contratos(); mp={f"{c['numero']} - {c['empresa']} ({c['unidade']})":c['id'] for c in cons}
    sc=st.selectbox("Contrato", list(mp.keys())); cid=mp[sc] if sc else None
    if cid:
        with st.expander("Add Regra", expanded=True):
            regras=utils.listar_regras_do_contrato(cid); grps=list(pd.DataFrame(regras)['grupo'].unique()) if regras else []
            mod=st.radio("Modo",["Existente","Novo"], horizontal=True) if grps else "Novo"
            g=st.selectbox("Sel", grps) if mod=="Existente" else st.text_input("Novo Grupo")
            i=st.text_input("Item"); p=st.number_input("Pts",0.0,step=0.05,format="%.2f")
            if st.button("Salvar Regra") and g and i: utils.cadastrar_regra(cid,g,i,p); st.rerun()
        if regras:
            dfr=pd.DataFrame(regras)
            for grp in dfr['grupo'].unique():
                with st.expander(f"📂 {grp}"):
                    for _,r in dfr[dfr['grupo']==grp].iterrows():
                        c1,c2,c3=st.columns([6,2,1]); c1.text(r['item']); c2.text(f"{r['pontos']} pts")
                        if c3.button("🗑️", key=f"dr{r['id']}"): utils.excluir_regra(r['id']); st.rerun()

# --- MULTAS ---
with tabs[3]:
    if not cons: st.stop()
    sc_m=st.selectbox("Contrato Multa", list(mp.keys()), key="sm"); cid_m=mp[sc_m]
    c1,c2,c3,c4=st.columns([2,2,2,1])
    with c1: mn=st.number_input("Min",0.0)
    with c2: mx=st.number_input("Max",mn+0.1)
    with c3: pc=st.number_input("%",0.0)
    with c4: 
        st.write(""); 
        if st.button("Add"): utils.cadastrar_faixa_multa(cid_m,mn,mx,pc); st.rerun()
    st.dataframe(pd.DataFrame(utils.listar_faixas_multa(cid_m)))

# --- USUÁRIOS ---
with tabs[4]:
    c1,c2=st.columns(2)
    with c1:
        with st.form("nu"):
            u=st.text_input("Login"); s=st.text_input("Senha",type="password"); p=st.selectbox("Perfil",["Fiscal","Gestor","Admin"])
            if st.form_submit_button("Criar"): utils.cadastrar_usuario(u,s,p); st.rerun()
    with c2:
        dfu=utils.carregar_df_sql("SELECT * FROM users")
        sel=st.selectbox("User", dfu['usuario'].unique())
        if st.button("Excluir Usuário"): utils.excluir_usuario(sel); st.rerun()

# --- VÍNCULOS ---
with tabs[5]:
    c1,c2=st.columns(2)
    with c1:
        dfu=utils.carregar_df_sql("SELECT * FROM users"); 
        if not dfu.empty:
            u=st.selectbox("U", dfu['usuario'].unique()); ct=st.selectbox("C", list(mp.keys()))
            if st.button("Vincular"): utils.vincular_usuario_contrato(u, mp[ct]); st.success("Ok")
    with c2:
        perms=utils.carregar_df_sql("SELECT * FROM permissions")
        for _,r in perms.iterrows():
            st.text(f"{r['usuario']} -> {r['contrato_id']}")
            if st.button("X", key=f"dp{r['usuario']}{r['contrato_id']}"): utils.desvincular_usuario_contrato(r['usuario'],r['contrato_id']); st.rerun()

# --- SEGURANÇA ---
with tabs[6]:
    st.subheader("🔐 Segurança")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Backup Completo")
        st.info("ZIP com Banco de Dados + Fotos.")
        zip_data = utils.gerar_backup_zip()
        st.download_button("📦 Baixar Backup (.zip)", zip_data, f"bkp_{pd.Timestamp.now().strftime('%Y%m%d')}.zip", "application/zip", type="primary")
    with c2:
        st.markdown("#### Logs")
        logs = utils.carregar_df_sql("SELECT * FROM audit_logs ORDER BY data_hora DESC LIMIT 50")
        if not logs.empty: st.dataframe(logs[['data_hora', 'usuario', 'acao', 'detalhes']], hide_index=True)