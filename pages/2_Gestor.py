import streamlit as st
import utils
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Gestor - FUNEAS", layout="wide", page_icon="👨‍💼")
utils.menu_lateral()

if not st.session_state.get("logado"): st.warning("Acesso negado."); st.stop()

col_t, col_u = st.columns([3, 1])
col_t.title("👨‍💼 Painel de Gestão")
col_u.markdown(f"👤 **{st.session_state['usuario']}** ({st.session_state['perfil']})")
st.divider()

df_all = utils.carregar_ocorrencias()
contratos = utils.listar_contratos_do_usuario(st.session_state["usuario"], st.session_state["perfil"])
ids = [c['id'] for c in contratos]

if not ids: st.warning("Sem contratos."); st.stop()

df_view = df_all if st.session_state["perfil"] == "Admin" else df_all[df_all['contrato_id'].isin(ids)]
if df_view.empty: st.info("Nenhuma ocorrência."); st.stop()

t1, t2, t3, t4 = st.tabs(["🔍 Validação", "📊 Dashboard", "📑 Relatórios", "🗂️ Histórico"])

# --- ABA 1: VALIDAÇÃO ---
with t1:
    pend = df_view[df_view['status'] == 'Pendente']
    if pend.empty: st.success("Tudo validado!")
    else:
        for _, r in pend.iterrows():
            with st.expander(f"🚨 {r['data_hora']} | {r['contrato_nome']}", expanded=True):
                c1,c2,c3=st.columns([1,2,1.5])
                with c1: 
                    if r['foto_path']!='sem_foto': st.image(r['foto_path']) 
                    else: st.text("Sem foto")
                with c2:
                    st.markdown(f"**{r['grupo_indicador']}**\n\n{r['descricao_infracao']}")
                    # Mostra Setor
                    st.caption(f"📍 {r['unidade']} ({r['setor']}) | Fiscal: {r['fiscal']}")
                    st.info(r['descricao_obs'])
                with c3:
                    st.write("### Decisão")
                    jst=st.text_area("Justificativa", key=f"j{r['id']}")
                    c_ok, c_no = st.columns(2)
                    if c_ok.button("✅ Aceitar", key=f"ok{r['id']}", use_container_width=True): 
                        if jst: utils.atualizar_status(r['id'], "Notificado", jst); st.rerun()
                        else: st.error("Justifique.")
                    if c_no.button("❌ Rejeitar", key=f"no{r['id']}", use_container_width=True):
                        if jst: utils.atualizar_status(r['id'], "Rejeitado", jst); st.rerun()
                        else: st.error("Justifique.")

# --- ABA 2: DASHBOARD ---
with t2:
    st.markdown("### 📊 Visão Estratégica")
    df_d = df_view.copy()
    df_d['dt'] = pd.to_datetime(df_d['data_hora']); df_d['mes'] = df_d['dt'].dt.strftime('%Y-%m')
    
    with st.container(border=True):
        c1, c2 = st.columns(2)
        ct = c1.selectbox("Contrato", ["Todos"]+list(df_d['contrato_nome'].unique()))
        ms = c2.selectbox("Mês", ["Todos"]+sorted(df_d['mes'].unique().tolist(), reverse=True))
        if ct!="Todos": df_d=df_d[df_d['contrato_nome']==ct]
        if ms!="Todos": df_d=df_d[df_d['mes']==ms]
    
    if not df_d.empty:
        tot_pts = df_d['pontos'].sum()
        # Multa dinâmica
        txt_mul = "N/A"
        if ct != "Todos":
            cid = df_d['contrato_id'].iloc[0]
            pct = utils.calcular_multa_dinamica(cid, tot_pts)
            txt_mul = f"{pct}%"
            
        k1,k2,k3 = st.columns(3)
        k1.metric("Ocorrências", len(df_d))
        k2.metric("Pontos", f"{tot_pts:.2f}")
        k3.metric("Multa Estimada", txt_mul)
        
        g1, g2 = st.columns(2)
        g1.plotly_chart(px.bar(df_d['grupo_indicador'].value_counts(), orientation='h'), use_container_width=True)
        g2.plotly_chart(px.pie(df_d, names='status'), use_container_width=True)
    else: st.warning("Sem dados.")

# --- ABA 3: RELATÓRIOS ---
with t3:
    st.subheader("Fechamento")
    mp = {f"{c['numero']} - {c['empresa']}": c for c in contratos}
    sc = st.selectbox("Contrato", list(mp.keys()))
    c_obj = mp[sc]
    
    meses = sorted(df_view[df_view['contrato_id']==c_obj['id']]['data_hora'].str[:7].unique(), reverse=True)
    sm = st.selectbox("Mês", meses) if meses else None
    
    if sm:
        # Filtro manual de string para data (simples e robusto para SQLite)
        dfr = df_view[(df_view['contrato_id']==c_obj['id']) & (df_view['data_hora'].str.startswith(sm)) & (df_view['status'].isin(['Notificado','Glosa Aplicada']))]
        if not dfr.empty:
            tp = dfr['pontos'].sum(); pdsc = utils.calcular_multa_dinamica(c_obj['id'], tp)
            st.success(f"Validado: {len(dfr)} itens | Pontos: {tp} | Multa: {pdsc}%")
            c1, c2 = st.columns(2)
            # Passa o mês formatado MM/YYYY para o relatório
            mes_fmt = f"{sm.split('-')[1]}/{sm.split('-')[0]}"
            c1.download_button("📄 PDF", utils.gerar_relatorio_pdf(dfr, c_obj, mes_fmt), "r.pdf")
            c2.download_button("📊 Excel", utils.gerar_relatorio_excel(dfr, c_obj, mes_fmt), "r.xlsx")
        else: st.warning("Nada validado neste mês.")

# --- ABA 4: HISTÓRICO (SOLUÇÃO 4 - E-MAIL) ---
with t4:
    st.markdown("### 🗂️ Banco de Dados e Notificações")
    
    # Mostra tabela
    st.dataframe(df_view[['data_hora','unidade','setor','contrato_nome','descricao_infracao','status']], use_container_width=True)
    
    st.divider()
    st.markdown("#### 📧 Gerador de Texto para E-mail")
    
    # Seleciona uma ocorrência notificada para gerar o texto
    notificadas = df_view[df_view['status'] == 'Notificado']
    if not notificadas.empty:
        sel_email = st.selectbox("Selecione a ocorrência para gerar o texto:", 
                                 notificadas['id'], 
                                 format_func=lambda x: f"{notificadas[notificadas['id']==x]['data_hora'].values[0]} - {notificadas[notificadas['id']==x]['descricao_infracao'].values[0]}")
        
        if sel_email:
            texto_email = utils.gerar_texto_email(sel_email)
            st.text_area("Copie o texto abaixo:", value=texto_email, height=300)
    else:
        st.info("Nenhuma ocorrência com status 'Notificado' para gerar e-mail.")