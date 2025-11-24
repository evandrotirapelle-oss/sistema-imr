import streamlit as st
import utils

# Configuração focada em Layout Limpo
st.set_page_config(page_title="FUNEAS - IMR", layout="wide", page_icon="🏥", initial_sidebar_state="collapsed")
utils.init_db()
utils.aplicar_estilo_funeas()

def login_screen():
    # Colunas para centralizar o cartão (Responsive: no mobile elas empilham, no PC centraliza)
    # A proporção [1, 1.5, 1] deixa o card com uma largura boa
    c_esq, c_centro, c_dir = st.columns([1, 1.5, 1])
    
    with c_centro:
        # Espaço em branco para não colar no topo
        st.write("")
        st.write("")
        
        # --- CARTÃO DE LOGIN (Container com Borda) ---
        # Este container está estilizado pelo CSS no utils.py para ter a borda azul
        with st.container(border=True):
            
            # 1. LOGO
            logo = utils.carregar_logo()
            if logo:
                # Centraliza a imagem usando colunas internas
                l_esq, l_meio, l_dir = st.columns([1, 2, 1])
                with l_meio:
                    st.image(logo, use_container_width=True)
            else:
                st.markdown("<h1 style='text-align: center;'>🏥 FUNEAS</h1>", unsafe_allow_html=True)
            
            # 2. TÍTULO E SUBTÍTULO
            st.markdown("<h3 style='text-align: center;'>Sistema de Gestão IMR</h3>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: gray;'>Informe suas credenciais para acessar</p>", unsafe_allow_html=True)
            
            st.write("") # Espaçamento
            
            # 3. FORMULÁRIO (Para permitir Enter enviar)
            with st.form("login_form"):
                usuario = st.text_input("Usuário", placeholder="Digite seu usuário")
                senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
                
                st.write("")
                submitted = st.form_submit_button("ENTRAR NO SISTEMA", use_container_width=True)
                
            if submitted:
                user_data = utils.verificar_login(usuario, senha)
                if user_data:
                    st.session_state["logado"] = True
                    st.session_state["usuario"] = user_data["usuario"]
                    st.session_state["perfil"] = user_data["perfil"]
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")

        # Rodapé
        st.markdown("<div style='text-align: center; margin-top: 20px; color: #999; font-size: 0.8rem;'>© 2025 Fundação Estatal de Atenção em Saúde do Paraná</div>", unsafe_allow_html=True)

# --- CONTROLE DE FLUXO ---
if "logado" not in st.session_state: st.session_state["logado"] = False

if not st.session_state["logado"]:
    login_screen()
else:
    # Se logado, carrega menu e conteúdo
    utils.menu_lateral()
    
    st.title(f"Olá, {st.session_state['usuario']}!")
    st.markdown(f"Você está conectado como **{st.session_state['perfil']}**.")
    st.divider()
    
    c1, c2, c3 = st.columns(3)
    
    # Cards de Acesso Rápido
    if st.session_state["perfil"] in ["Fiscal", "Admin"]:
        with c1:
            with st.container(border=True):
                st.subheader("📋 Área do Fiscal")
                st.info("Realizar auditorias.")
                if st.button("Acessar Fiscal", use_container_width=True): st.switch_page("pages/1_Fiscal.py")

    if st.session_state["perfil"] in ["Gestor", "Admin"]:
        with c2:
            with st.container(border=True):
                st.subheader("👨‍💼 Área do Gestor")
                st.warning("Validar e Relatórios.")
                if st.button("Acessar Gestor", use_container_width=True): st.switch_page("pages/2_Gestor.py")

    if st.session_state["perfil"] == "Admin":
        with c3:
            with st.container(border=True):
                st.subheader("⚙️ Administração")
                st.success("Configurações.")
                if st.button("Acessar Admin", use_container_width=True): st.switch_page("pages/3_Admin.py")