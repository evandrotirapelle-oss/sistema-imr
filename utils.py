import pandas as pd
import os
import uuid
import streamlit as st
from fpdf import FPDF
import io
import base64
import sqlite3
import bcrypt
import zipfile
from datetime import datetime

# --- 1. ARQUIVOS ---
DB_FILE = 'dados/imr.db'

# --- 2. BANCO DE DADOS ---
def get_db_connection():
    if not os.path.exists('dados'): os.makedirs('dados')
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists('images'): os.makedirs('images')
    conn = get_db_connection(); c = conn.cursor()
    
    tables = [
        "CREATE TABLE IF NOT EXISTS users (usuario TEXT PRIMARY KEY, senha TEXT, perfil TEXT)",
        "CREATE TABLE IF NOT EXISTS units (nome TEXT PRIMARY KEY)",
        "CREATE TABLE IF NOT EXISTS sectors (id TEXT PRIMARY KEY, unidade_nome TEXT, nome_setor TEXT)",
        "CREATE TABLE IF NOT EXISTS contracts (id TEXT PRIMARY KEY, numero TEXT, unidade TEXT, empresa TEXT)",
        "CREATE TABLE IF NOT EXISTS permissions (usuario TEXT, contrato_id TEXT)",
        "CREATE TABLE IF NOT EXISTS rules (id TEXT PRIMARY KEY, contrato_id TEXT, grupo TEXT, item TEXT, pontos REAL)",
        "CREATE TABLE IF NOT EXISTS fines (id TEXT PRIMARY KEY, contrato_id TEXT, min_val REAL, max_val REAL, percentual REAL)",
        "CREATE TABLE IF NOT EXISTS occurrences (id TEXT PRIMARY KEY, data_hora TEXT, unidade TEXT, setor TEXT, contrato_id TEXT, contrato_nome TEXT, fiscal TEXT, regra_id TEXT, grupo_indicador TEXT, descricao_infracao TEXT, pontos REAL, descricao_obs TEXT, status TEXT, foto_path TEXT, justificativa_gestor TEXT)",
        "CREATE TABLE IF NOT EXISTS audit_logs (id TEXT PRIMARY KEY, data_hora TEXT, usuario TEXT, acao TEXT, detalhes TEXT)"
    ]
    for t in tables: c.execute(t)
    
    c.execute("SELECT * FROM users WHERE usuario = 'admin'")
    if not c.fetchone():
        s_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        c.execute("INSERT INTO users VALUES (?, ?, ?)", ('admin', s_hash, 'Admin'))
    conn.commit(); conn.close()

# --- 3. LOGS E SEGURANÇA ---
def registrar_log(usuario, acao, detalhes):
    try:
        sql = "INSERT INTO audit_logs VALUES (?, ?, ?, ?, ?)"
        usr = usuario if usuario else "Sistema"
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        executar_sql(sql, (str(uuid.uuid4()), agora, usr, acao, detalhes), log=False)
    except: pass

def hash_senha(s): return bcrypt.hashpw(s.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
def check_senha(s, h): 
    try: return bcrypt.checkpw(s.encode('utf-8'), h.encode('utf-8'))
    except: return False

# --- 4. VISUAL ---
def carregar_logo():
    return "images/logo_funeas.png" if os.path.exists("images/logo_funeas.png") else None

def get_image_base64(path):
    if not os.path.exists(path): return ""
    with open(path, "rb") as img: return f"data:image/png;base64,{base64.b64encode(img.read()).decode()}"

def aplicar_estilo_funeas():
    cor_inst = "#005483" # Azul FUNEAS
    cor_hover = "#E6F0F5" # Azul bem clarinho para hover
    
    st.markdown(f"""
        <style>
        /* 1. Ajustes Gerais */
        .block-container {{padding-top: 1.5rem; padding-bottom: 1rem;}}
        [data-testid="stSidebarNav"] {{display: none;}}
        
        /* 2. Estilização da Sidebar */
        [data-testid="stSidebar"] {{
            background-color: #FFFFFF;
            border-right: 1px solid #E0E0E0;
        }}
        
        /* 3. Transformando Botões da Sidebar em "Links de Menu" */
        /* Seleciona todos os botões DENTRO da sidebar */
        [data-testid="stSidebar"] div.stButton > button {{
            background-color: transparent; /* Fundo transparente */
            color: #444444; /* Texto cinza escuro */
            border: 1px solid transparent; /* Sem borda visível */
            border-radius: 5px;
            text-align: left; /* Texto alinhado à esquerda */
            width: 100%; /* Ocupa largura total */
            padding: 10px 15px; /* Espaçamento interno */
            font-size: 16px;
            font-weight: 500;
            margin-bottom: 2px; /* Espaço menor entre botões */
            transition: all 0.2s ease;
        }}
        
        /* Efeito ao passar o mouse (Hover) na Sidebar */
        [data-testid="stSidebar"] div.stButton > button:hover {{
            background-color: {cor_hover};
            color: {cor_inst};
            border-left: 4px solid {cor_inst}; /* Detalhe azul na esquerda */
            border-radius: 0px 5px 5px 0px; /* Borda quadrada na esquerda */
        }}
        
        /* Efeito ao clicar (Active) */
        [data-testid="stSidebar"] div.stButton > button:active {{
            background-color: #D0E0EB;
            transform: scale(0.99);
        }}

        /* 4. Tratamento Especial para o Botão SAIR (Identificamos pelo tipo 'primary' se usado, ou pelo contexto) */
        /* Vamos usar um truque no Python para identificar o botão Sair, mas aqui definimos um estilo de alerta */
        
        /* 5. Estilo do Card de Login (Mantido do anterior) */
        .login-card {{
            background: white; padding: 3rem; border-radius: 12px; 
            box-shadow: 0 4px 20px rgba(0,0,0,0.1); border-top: 6px solid {cor_inst}; 
            text-align: center; margin-top: 50px;
        }}
        
        /* 6. Botões da Área Principal (Mantém o estilo forte azul) */
        /* O seletor abaixo garante que NÃO afete a sidebar */
        .main div.stButton > button {{
            background-color: {cor_inst}; 
            color: white; 
            border-radius: 6px; 
            font-weight: 600;
        }}
        .main div.stButton > button:hover {{
            background-color: #004060;
        }}
        
        h1, h2, h3 {{color: {cor_inst};}}
        </style>
    """, unsafe_allow_html=True)

def menu_lateral():
    aplicar_estilo_funeas()
    logo = carregar_logo()
    
    with st.sidebar:
        # Espaço para o Logo
        st.write("")
        if logo: 
            # Colunas para centralizar melhor o logo se ele for pequeno
            c1, c2, c3 = st.columns([0.5, 2, 0.5])
            with c2:
                st.image(logo, use_container_width=True)
        else: 
            st.title("🏥 FUNEAS")
            
        st.markdown("---")
        
        if st.session_state.get("logado"):
            p = st.session_state.get("perfil")
            
            st.caption("MENU PRINCIPAL")
            
            # Botões com ícones integrados no texto para alinhamento perfeito
            # A lógica if/else permanece idêntica, mudamos apenas a "cara" via CSS acima
            
            if st.button("  🏠   Início"): 
                st.switch_page("app.py")
            
            if p in ["Fiscal", "Admin"]: 
                if st.button("  📋   Área do Fiscal"): 
                    st.switch_page("pages/1_Fiscal.py")
            
            if p in ["Gestor", "Admin"]: 
                if st.button("  👨‍💼   Área do Gestor"): 
                    st.switch_page("pages/2_Gestor.py")
            
            if p == "Admin": 
                if st.button("  ⚙️   Administração"): 
                    st.switch_page("pages/3_Admin.py")
            
            # Empurrador para o fundo (Espaço em branco)
            st.write("")
            st.write("")
            st.markdown("---")
            
            # Botão de Sair com estilo visual diferente (usando markdown HTML se necessário ou CSS específico)
            # Aqui usamos o botão nativo, mas o CSS vai tentar deixá-lo limpo. 
            # Para destacar o SAIR como vermelho/alerta, podemos usar o type="primary" e mudar o CSS específico dele
            if st.button("🚪  Sair do Sistema"):
                registrar_log(st.session_state['usuario'], "Logout", "Saiu")
                st.session_state.clear()
                st.rerun()
            
            # Rodapézinho
            st.markdown("<div style='text-align: center; color: grey; font-size: 12px; margin-top: 20px;'>v1.0.0</div>", unsafe_allow_html=True)

# --- 5. DADOS SQL ---
def get_conn(): return get_db_connection()
def carregar_df_sql(q, p=()):
    conn = get_conn()
    try: return pd.read_sql_query(q, conn, params=p)
    except: return pd.DataFrame()
    finally: conn.close()
def executar_sql(sql, p=(), log=True):
    conn = get_conn()
    try: c=conn.cursor(); c.execute(sql, p); conn.commit(); return True
    except: return False
    finally: conn.close()

# --- 6. LÓGICA E RELATÓRIOS ---
def gerar_texto_email(oid):
    r = carregar_df_sql("SELECT * FROM occurrences WHERE id=?", (oid,))
    if r.empty: return ""
    r = r.iloc[0]
    return f"Prezados,\nNotificação ref. Contrato {r['contrato_nome']}.\nLocal: {r['unidade']} ({r['setor']})\nInfração: {r['descricao_infracao']}\nData: {r['data_hora']}\n\nAtenciosamente,\nFUNEAS"

def calcular_multa_dinamica(cid, pts):
    df = carregar_df_sql("SELECT * FROM fines WHERE contrato_id=?",(cid,))
    if df.empty: return 0.0
    for _,r in df.iterrows():
        if float(r['min_val']) <= float(pts) <= float(r['max_val']): return float(r['percentual'])
    return 0.0

def calcular_sla(data_hora_str):
    try:
        dt_ocorr = datetime.strptime(str(data_hora_str), "%Y-%m-%d %H:%M")
        diff = datetime.now() - dt_ocorr
        horas = diff.total_seconds() / 3600
        if horas < 24: return "🟢 No Prazo"
        elif horas < 48: return "🟡 Atenção"
        else: return "🔴 Expirado"
    except: return "⚪ N/A"

def gerar_relatorio_pdf(df, info, mes):
    class PDF(FPDF):
        def header(self):
            if os.path.exists("images/logo_funeas.png"): self.image("images/logo_funeas.png", 10, 8, 33)
            self.set_font('Arial', 'B', 14); self.cell(40); self.cell(0, 10, 'Relatório de Medição (IMR)', 0, 1, 'C'); self.ln(10)
    pdf = PDF(); pdf.add_page(); pdf.set_auto_page_break(True, 15)
    pdf.set_font("Arial", size=10); pdf.cell(0, 5, f"Ref: {mes}", 0, 1, 'R'); pdf.ln(5)
    pdf.set_font('Arial', 'B', 11); pdf.cell(0,6,f"Unid: {info['unidade']}",0,1); pdf.cell(0,6,f"Contrato: {info['numero']} - {info['empresa']}",0,1); pdf.ln(5)
    w=[25,95,45,25]; pdf.set_fill_color(240); pdf.set_font('Arial','B',9)
    h=['Data','Ocorrência','Indicador','Pts']; [pdf.cell(w[i],8,h[i],1,0,'C',1) for i in range(4)]; pdf.ln()
    pdf.set_font('Arial','',8); tot=0
    for _, r in df.iterrows():
        d=str(r['data_hora']).split()[0]; 
        def c(t): return str(t).encode('latin-1','replace').decode('latin-1')
        o=c(f"[{r['setor']}] {r['descricao_infracao']}"); i=c(str(r['grupo_indicador']).split('-')[0]); p=f"{r['pontos']:.2f}"
        h_ln=max(int(pdf.get_string_width(o)/(w[1]-2))+1, int(pdf.get_string_width(i)/(w[2]-2))+1)*5+2
        if pdf.get_y()+h_ln>275: pdf.add_page()
        x=pdf.get_x(); y=pdf.get_y()
        pdf.cell(w[0],h_ln,d,0,0,'C'); pdf.set_xy(x+w[0],y); pdf.multi_cell(w[1],5,o,0,'L')
        pdf.set_xy(x+w[0]+w[1],y); pdf.multi_cell(w[2],5,i,0,'L'); pdf.set_xy(x+sum(w[:3]),y); pdf.cell(w[3],h_ln,p,0,0,'C')
        pdf.set_xy(x,y); [pdf.rect(x+sum(w[:j]),y,w[j],h_ln) for j in range(4)]; pdf.set_xy(x,y+h_ln); tot+=r['pontos']
    pdf.ln(10); per=calcular_multa_dinamica(info['id'],tot)
    pdf.set_font('Arial','B',12); pdf.cell(0,8,f"Total: {tot:.2f} | Desconto: {per}%",0,1); return pdf.output(dest='S').encode('latin-1')

def gerar_relatorio_excel(df, info, mes):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as w:
        df.to_excel(w, sheet_name='Dados', index=False)
        wb=w.book; ws=wb.add_worksheet('Resumo'); bold=wb.add_format({'bold':True})
        ws.write('A1', f"IMR - {mes}", bold); ws.write('A3', f"Contrato: {info['numero']}")
        tot=df['pontos'].sum(); per=calcular_multa_dinamica(info['id'], tot)
        ws.write('A6', "Total:", bold); ws.write('B6', tot); ws.write('A7', "Desc %:", bold); ws.write('B7', f"{per}%")
    return out.getvalue()

def gerar_backup_zip():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        if os.path.exists(DB_FILE): z.write(DB_FILE, arcname="imr.db")
        if os.path.exists("images"):
            for root, _, files in os.walk("images"):
                for file in files: z.write(os.path.join(root, file), arcname=os.path.join("images", file))
    buffer.seek(0); return buffer.read()

# --- 7. CRUD ---
def cadastrar_usuario(u,s,p):
    if not carregar_df_sql("SELECT 1 FROM users WHERE usuario=?",(u,)).empty: return False
    res=executar_sql("INSERT INTO users VALUES (?,?,?)",(u,hash_senha(s),p))
    if res: registrar_log(st.session_state.get('usuario'),"Cadastro",f"User {u}"); return res
def editar_usuario(u,s,p):
    res=executar_sql("UPDATE users SET senha=?, perfil=? WHERE usuario=?",(hash_senha(s),p,u))
    if res: registrar_log(st.session_state.get('usuario'),"Edit",f"User {u}"); return res
def excluir_usuario(u):
    if u=='admin': return False
    executar_sql("DELETE FROM permissions WHERE usuario=?",(u,)); res=executar_sql("DELETE FROM users WHERE usuario=?",(u,))
    if res: registrar_log(st.session_state.get('usuario'),"Delete",f"User {u}"); return res
def verificar_login(u,s):
    r=get_conn().execute("SELECT * FROM users WHERE usuario=?",(u,)).fetchone()
    if r and check_senha(s, r['senha']): registrar_log(u,"Login","Ok"); return dict(r)
    return None
def listar_contratos_do_usuario(u,p):
    if p=='Admin': return carregar_df_sql("SELECT * FROM contracts").to_dict('records')
    return carregar_df_sql("SELECT c.* FROM contracts c JOIN permissions p ON c.id=p.contrato_id WHERE p.usuario=?",(u,)).to_dict('records')
def listar_todos_contratos(): return carregar_df_sql("SELECT * FROM contracts").to_dict('records')
def cadastrar_contrato(n,u,e): return executar_sql("INSERT INTO contracts VALUES (?,?,?,?)",(str(uuid.uuid4()),n,u,e))
def excluir_contrato(i): 
    for t in ['rules','fines','permissions']: executar_sql(f"DELETE FROM {t} WHERE contrato_id=?",(i,))
    return executar_sql("DELETE FROM contracts WHERE id=?",(i,))
def cadastrar_unidade(n): return executar_sql("INSERT INTO units VALUES (?)",(n,))
def excluir_unidade(n): executar_sql("DELETE FROM sectors WHERE unidade_nome=?",(n,)); return executar_sql("DELETE FROM units WHERE nome=?",(n,))
def cadastrar_setor(u,n): return executar_sql("INSERT INTO sectors VALUES (?,?,?)",(str(uuid.uuid4()),u,n))
def excluir_setor(i): return executar_sql("DELETE FROM sectors WHERE id=?",(i,))
def listar_setores(u): return carregar_df_sql("SELECT * FROM sectors WHERE unidade_nome=?",(u,)).to_dict('records')
def cadastrar_regra(c,g,i,p): return executar_sql("INSERT INTO rules VALUES (?,?,?,?,?)",(str(uuid.uuid4()),c,g,i,p))
def excluir_regra(i): return executar_sql("DELETE FROM rules WHERE id=?",(i,))
def listar_regras_do_contrato(c): return carregar_df_sql("SELECT * FROM rules WHERE contrato_id=?",(c,)).to_dict('records')
def cadastrar_faixa_multa(c,mi,mx,p): return executar_sql("INSERT INTO fines VALUES (?,?,?,?,?)",(str(uuid.uuid4()),c,mi,mx,p))
def excluir_faixa_multa(i): return executar_sql("DELETE FROM fines WHERE id=?",(i,))
def listar_faixas_multa(c): return carregar_df_sql("SELECT * FROM fines WHERE contrato_id=? ORDER BY min_val",(c,)).to_dict('records')
def vincular_usuario_contrato(u,c): 
    if not carregar_df_sql("SELECT 1 FROM permissions WHERE usuario=? AND contrato_id=?",(u,c)).empty: return True
    return executar_sql("INSERT INTO permissions VALUES (?,?)",(u,c))
def desvincular_usuario_contrato(u,c): return executar_sql("DELETE FROM permissions WHERE usuario=? AND contrato_id=?",(u,c))
def salvar_ocorrencia(n): res=executar_sql("INSERT INTO occurrences VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",tuple(n.values())); return res
def excluir_ocorrencia(i): return executar_sql("DELETE FROM occurrences WHERE id=?",(i,))
def carregar_ocorrencias(): return carregar_df_sql("SELECT * FROM occurrences")
def atualizar_status(oid,s,j=""): return executar_sql("UPDATE occurrences SET status=?, justificativa_gestor=? WHERE id=?",(s,j,oid))