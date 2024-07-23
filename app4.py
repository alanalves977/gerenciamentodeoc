import streamlit as st
import sqlite3
import hashlib
import pandas as pd
import datetime

# Function to create users table
def create_user_table():
    conn = sqlite3.connect('po_management.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            privilege TEXT,
            ativo INTEGER -- 0 or 1 to represent boolean values
        )
    ''')
    conn.commit()
    conn.close()


def add_first_user():
    conn = sqlite3.connect('po_management.db')
    c = conn.cursor()
    c.execute('''
        SELECT * FROM users
    ''')
    u = c.fetchone()
    conn.close()
    if u is None:
        add_user("Alan Alves", "alan.alves@msdourada.com.br", "123456", "admin")
        add_user("Telma Lima", "telma.lima@msdourada.com.br", "123456", "admin")


# Function to create purchases_orders table
def create_po_table():
    conn = sqlite3.connect('po_management.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS purchases_orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            po INTEGER UNIQUE,
            data_envio_po DATE,
            prazo_despacho_dias INTEGER,
            prazo_transporte_dias INTEGER,
            data_prevista_para_despacho DATE,
            data_despachado DATE,
            data_prevista_recebimento DATE,
            data_recebido DATE,
            descricao TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

# Function to create comments table
def create_comments_table():
    conn = sqlite3.connect('po_management.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY,
            po_id INTEGER,
            user_id INTEGER,
            date_created DATE,
            comment TEXT,
            FOREIGN KEY (po_id) REFERENCES purchases_orders (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to check user credentials
def check_login(email, password):
    conn = sqlite3.connect('po_management.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE email = ? AND password = ? AND ativo = 1', (email, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user

# Function to add a new user
def add_user(name, email, password, privilege):
    try:
        conn = sqlite3.connect('po_management.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO users (name, email, password, privilege, ativo) 
            VALUES (?, ?, ?, ?, 1)
        ''', (name, email, hash_password(password), privilege))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError as e:
        if 'UNIQUE constraint failed' in str(e):
            return False
        else:
            raise e

# Function to add a new purchase order
def add_purchase_order(user_id, po, data_envio_po, prazo_despacho_dias, prazo_transporte_dias, descricao):
    data_prevista_para_despacho = datetime.datetime.strptime(data_envio_po, '%Y-%m-%d') + datetime.timedelta(days=prazo_despacho_dias)
    
    try:
        conn = sqlite3.connect('po_management.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO purchases_orders (user_id, po, data_envio_po, prazo_despacho_dias, prazo_transporte_dias, data_prevista_para_despacho, descricao) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, po, data_envio_po, prazo_despacho_dias, prazo_transporte_dias, data_prevista_para_despacho, descricao))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError as e:
        if 'UNIQUE constraint failed' in str(e):
            return False
        else:
            raise e

# Function to add a new comment
def add_comment(po_id, user_id, comment):
    date_created = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect('po_management.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO comments (po_id, user_id, date_created, comment) 
        VALUES (?, ?, ?, ?)
    ''', (po_id, user_id, date_created, comment))
    conn.commit()
    conn.close()

# Function to get all purchase orders
def get_all_purchase_orders():
    conn = sqlite3.connect('po_management.db')
    c = conn.cursor()
    c.execute('SELECT purchases_orders.*, users.name FROM purchases_orders LEFT JOIN users ON purchases_orders.user_id = users.id ORDER BY po')
    pos = c.fetchall()
    conn.close()
    return pos

# Function to get comments for a specific PO
def get_comments(po_id):
    conn = sqlite3.connect('po_management.db')
    c = conn.cursor()
    c.execute('SELECT users.name, comments.date_created, comments.comment FROM comments JOIN users ON comments.user_id = users.id WHERE comments.po_id = ? ORDER BY comments.date_created', (po_id,))
    comments = c.fetchall()
    conn.close()
    return comments

# Update data despachado and data_prevista_recebimento
def update_data_despachado(po_number, new_despachado_date, new_data_prevista_recebimento):
    try:
        conn = sqlite3.connect('po_management.db')
        c = conn.cursor()
        c.execute('''
            UPDATE purchases_orders
            SET data_despachado = ?,
                data_prevista_recebimento = ?
            WHERE po = ?
        ''', (new_despachado_date, new_data_prevista_recebimento, po_number))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        st.warning(f"Um erro ocorreu. Não foi possível atualizar: {e}")
        return False
     
#Update data recebido
def update_data_recebido(po_number, new_date):
    try:
        conn = sqlite3.connect('po_management.db')
        c = conn.cursor()
        c.execute('''
            UPDATE purchases_orders
            SET data_recebido = ?
            WHERE po = ?
        ''', (new_date, po_number))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        st.warning("Um erro ocorreu. Não foi possível atualizar: {e}")

#Update usuário
def update_user(user_id, name, email, password, privilege, ativo):
    try:
        conn = sqlite3.connect('po_management.db')
        c = conn.cursor()
        c.execute('''
            UPDATE users
            SET name = ?, email = ?, password = ?, privilege = ?, ativo = ?
            WHERE id = ?
        ''', (name, email, password, privilege, int(ativo), user_id))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        st.warning(f"Um erro ocorreu: {e}")
        return False
    
#Check orders statuses
def check_statuses(df):
    #Convert dates to pandas datetime type
    df[['data_envio_po','data_prevista_para_despacho','data_despachado', 'data_prevista_recebimento','data_recebido']] = df[['data_envio_po','data_prevista_para_despacho','data_despachado', 'data_prevista_recebimento','data_recebido']].apply(pd.to_datetime)

    #STATUS OF SENT DATE
    
    #Order sent on expected time
    status_despacho_temp = df['data_despachado'] <= df['data_prevista_para_despacho']
    df.loc[status_despacho_temp, 'status_despachado'] = 'Despachado no prazo'
    df.loc[status_despacho_temp, 'overall_status'] = 'no prazo - em trânsito'

    #Orders sent after expected time
    status_despacho_temp = df['data_despachado'] > df['data_prevista_para_despacho']
    df.loc[status_despacho_temp, 'status_despachado'] = 'Despachado com atraso'
    df.loc[status_despacho_temp, 'overall_status'] = 'no prazo - em trânsito'

    #Order not yet sent but on time
    status_despacho_temp = pd.isna(df['data_despachado']) & (df['data_prevista_para_despacho'] >= pd.to_datetime(datetime.date.today()))
    df.loc[status_despacho_temp, 'status_despachado'] = 'No prazo'
    df.loc[status_despacho_temp, 'overall_status'] = 'no prazo - remessa não enviada'
    
    #Find which orders is delayed
    status_despacho_temp = pd.isna(df['data_despachado']) & (df['data_prevista_para_despacho'] < pd.to_datetime(datetime.date.today()))
    df.loc[status_despacho_temp, 'status_despachado'] = 'Atrasada'
    df.loc[status_despacho_temp, 'overall_status'] = 'atrasada - remessa não enviada'

    #STATUS OF ARRIAVEL DATE

    #Orders arrived on expected time
    status_recebido_temp = df['data_recebido'] <= df['data_prevista_recebimento']
    df.loc[status_recebido_temp, 'status_recebido'] = 'Recebido no prazo'
    df.loc[status_recebido_temp, 'overall_status'] = 'Finalizada'

    #Orders arrived after expected time
    status_recebido_temp = df['data_recebido'] > df['data_prevista_recebimento']
    df.loc[status_recebido_temp, 'status_recebido'] = 'Recebido com atraso'
    df.loc[status_recebido_temp, 'overall_status'] = 'Finalizada'
    
    #Orders not yet received but on time
    status_recebido_temp = pd.isna(df['data_recebido']) & (df['data_prevista_recebimento'] >= pd.to_datetime(datetime.date.today()))
    df.loc[status_recebido_temp, 'status_recebido'] = 'No prazo'
    df.loc[status_recebido_temp, 'overall_status'] = 'no prazo - em trânsito'
    
    #Orders not yet received and delayed
    status_recebido_temp = pd.isna(df['data_recebido']) & (df['data_prevista_recebimento'] < pd.to_datetime(datetime.date.today()))
    df.loc[status_recebido_temp, 'status_recebido'] = 'Atrasada'
    df.loc[status_recebido_temp, 'overall_status'] = 'atrasada - em trânsito'
    
    #Expected days to arrivel
    df['dias_para_chegada'] = (df['data_prevista_recebimento'] - pd.to_datetime(datetime.date.today())).dt.days
    
    #Overall status: próximo de encerrar
    status_overall_temp = (df['overall_status'] == 'no prazo - em trânsito') & (df['dias_para_chegada'] <= 3)
    df.loc[status_overall_temp, 'overall_status'] = 'prazo próximo do encerramento'

    return df

# Main login function
def login():

    # Logo
    st.image("mineração serra dourada.png", use_column_width=False)
    st.write("")
    st.write("### Gestão de compras enviadas ao fornecedor")
    st.write("#### Login")

    email = st.text_input("Email")
    password = st.text_input("Senha", type="password")

    if st.button("Login"):
        user = check_login(email, password)
        if user:
            st.success(f"Welcome {user[1]}!")
            st.session_state.user = user
            st.session_state.logged_in = True
            st.session_state.page = "Todas Ordens de Compras"  # Set initial page after login
            st.rerun()  # Rerun to immediately reflect session state changes
        else:
            st.error("O seu e-mail ou a sua senha está incorreta.")

# Page to add new purchase orders
def add_new_order_page():
    st.title("Adicionar Nova OC")

    user = st.session_state.user

    po = st.number_input("Número da OC", min_value=1, step=1)
    descricao = st.text_input("Descrição", placeholder = "Fornecedor / itens / outras informações relevantes")
    data_envio_po = st.date_input("Data Envio da OC", format="DD/MM/YYYY", max_value=datetime.datetime.today())
    prazo_despacho_dias = st.number_input("Prazo Despacho (dias)", min_value=1, step=1)
    prazo_transporte_dias = st.number_input("Prazo Transporte (dias)", min_value=1, step=1)

    if st.button("Adicionar OC"):
        success = add_purchase_order(user[0], po, data_envio_po.strftime('%Y-%m-%d'), prazo_despacho_dias, prazo_transporte_dias, descricao)
        st.session_state['po'] = ""
        st.session_state['data_envio_po'] = ""
        st.session_state['prazo_despacho_dias'] = ""
        st.session_state['prazo_transporte_dias'] = ""
        if success:
            st.success("Ordem de compra adicionada com sucesso.")
        else:
            st.warning("OC já cadastrada. Por favor entre com um número de OC diferente.")
        

# Settings page for admin to add users
def settings_page():
    st.title("Usuários")
    
    tabs = st.tabs(["Adicionar novo usuário", "Editar Usuário"])
    
    # Adicionar novo usuário
    with tabs[0]:
        st.header("Adicionar Novo Usuário")
        
        name = st.text_input("Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        privilege = st.selectbox("Privilégio", ["admin", "comprador"])

        if st.button("Adicionar usuário"):
            if not name or not email or not password:
                st.warning("Todos os campos são obrigatórios!")
            else:
                success = add_user(name, email, password, privilege)
                if success:
                    st.success("Usuário adicionado com sucesso!")
                else:
                    st.warning("E-mail de usuário já cadastrado.")
    
    # Editar Usuário
    with tabs[1]:
        st.header("Editar Usuário")
        
        conn = sqlite3.connect('po_management.db')
        c = conn.cursor()
        c.execute('SELECT email FROM users')
        emails = [row[0] for row in c.fetchall()]
        conn.close()

        selected_email = st.selectbox("Selecione o Email", emails)

        if selected_email:
            conn = sqlite3.connect('po_management.db')
            c = conn.cursor()
            c.execute('SELECT * FROM users WHERE email = ?', (selected_email,))
            user_data = c.fetchone()
            conn.close()

            if user_data:
                user_id, name, email, password, privilege, ativo = user_data

                new_name = st.text_input("Name", value=name, key = "new_name_input")
                new_password = st.text_input("Password", type="password", key ="new_password_input")
                new_privilege = st.selectbox(
                    "Privilégio", 
                    ["admin", "comprador"], 
                    index=["admin", "comprador"].index(privilege) if privilege in ["admin", "comprador"] else 0,
                    key = "new_privilege_input"
                )
                new_ativo = st.checkbox("Usuário Ativo", value=ativo == 1)

            #Salva alterações
            if st.button("Salvar Alterações"):
                # Check if any input is empty
                if not new_name or not selected_email or not new_password or new_privilege is None:
                    st.warning("Todos os campos são obrigatórios!")
                else:
                    success = update_user(user_id, new_name, selected_email, hash_password(new_password), new_privilege, new_ativo)
                    if success:
                        st.success("Usuário atualizado com sucesso!")
                    else:
                        st.warning("Erro ao atualizar o usuário.")
        
# All pos page   
def all_pos_page():
    #Colour codes
    success_colour = "#4caf50"
    warning_colour = "#ff9800"
    danger_colour = "#ef5350"
    
    # Make use of full width page
    st.markdown('''
        <style>
            section.main > div {max-width:98rem}
        </style>
        ''', unsafe_allow_html=True)
    # Page title 
    st.markdown("<h1 style='text-align: center; color: black;'>Ordens de Compra</h1>", unsafe_allow_html=True)
    st.write("#")
    
    # Get orders
    pos = get_all_purchase_orders() 
    
    # Convert order to pandas dataframe
    colnames = ['id', 'user_id', 'po', 'data_envio_po', 'prazo_despacho_dias', 'prazo_transporte_dias', 'data_prevista_para_despacho', 'data_despachado', 'data_prevista_recebimento', 'data_recebido', 'descricao', 'comprador']
    pos_df = check_statuses(pd.DataFrame(pos, columns = colnames))
    pos_df.columns = ['ID', 'User ID', 'OC', 'Data de Envio OC', 'Prazo de Despacho', 'Prazo de Transporte', 'Data Prevista Para Despacho', 'Data Despachado', 'Data Prevista de Recebimento', 'Data Recebido', 'Descrição', 'Comprador','Status Despachado', 'Status Geral', 'Status Recebido', 'Dias para Chegar']
    pos_df['Data de Envio OC'] = pos_df['Data de Envio OC'].dt.strftime("%d/%m/%Y")
    
    #Create two columns and show delayed purchases on left side
    colx, coly = st.columns(2, gap = "large")
    
    #Get delayed OCs
    delayed_ocs = pos_df[pos_df['Status Geral'].astype(str).str.contains('atrasada', case=False, na=False)]['OC'].astype(str).str.cat(sep=', ')
    near_deadline = pos_df[pos_df['Status Geral'].astype(str).str.contains('próximo', case=False, na=False)]['OC'].astype(str).str.cat(sep=', ')
    
    #Show delayed OCs
    if delayed_ocs or near_deadline:
        with colx:
            with st.expander("##### Ordens de compras atrasadas ou com prazo próximo", expanded = True):
                #Filtrar pelo usuário ativo
                minhas_oc = st.checkbox("Ver apenas as minhas", value = False)
                if minhas_oc:
                    comprador_temp = st.session_state.user[1]
                    delayed_ocs = pos_df[pos_df['Status Geral'].astype(str).str.contains('atrasada', case=False, na=False) & (pos_df['Comprador'] == comprador_temp)]['OC'].astype(str).str.cat(sep=', ')
                    near_deadline = pos_df[pos_df['Status Geral'].astype(str).str.contains('próximo', case=False, na=False) & (pos_df['Comprador'] == comprador_temp)]['OC'].astype(str).str.cat(sep=', ')
                    
                    if not delayed_ocs and not near_deadline:
                        st.write("**Você não tem nenhuma OC atrasada ou com prazo próximo**")
                        st.balloons()
                    
                if delayed_ocs:
                    # Display the text with colored status
                    st.markdown(f"""
                        **Atrasadas:** <span style="color:{danger_colour};">{delayed_ocs}</span>
                        """, unsafe_allow_html=True)
                if near_deadline:
                    st.markdown(f"""
                        **Com prazo próximo:** <span style="color:{warning_colour};">{near_deadline}</span>
                        """, unsafe_allow_html=True)
                        
    # Create two columns
    col1, col2 = st.columns(2, gap ="medium")

    # Display POs in a DataFrame table
    if pos:
        with col1:
            st.write("#### Todas OC")
            #Create two columns to build filter options
            col3, col4 = st.columns(2, gap = "small")
            #Filter options
            st.write("##### Filtros")
            with col3:
                comprador_filter = st.selectbox("Filtrar por Comprador", ["Todos"] + pos_df['Comprador'].unique().tolist())
                if comprador_filter != "Todos":
                    pos_df = pos_df[pos_df['Comprador'] == comprador_filter]
            
            with col4:
                status_filter = st.selectbox("Filtrar por Status Geral", ["Todos"] + pos_df['Status Geral'].unique().tolist())
                if status_filter != "Todos":
                    pos_df = pos_df[pos_df['Status Geral'] == status_filter]
            
            # Create a dataframe for display and add a clickable column
            st.dataframe(pos_df[['OC', 'Descrição', 'Data de Envio OC', 'Status Geral', 'Comprador']],
            hide_index=True,
            use_container_width=True,
            column_config={
                "OC":st.column_config.NumberColumn(
                    width = "small",
                    format = "%f"
                    )
                })
        
        #PO details
        with col2:
            # Retrieve OC
            st.write("#### Detalhes")
            selected_po_number = st.selectbox("Selecione uma Ordem de Compra", pos_df['OC'], index = None, placeholder = 'Selecione uma OC')
            pos_df_details = pos_df.loc[pos_df['OC']==selected_po_number]
            
            #Show details when selected PO number
            if selected_po_number:
                #Detalhes da OC
                prazo_envio = pos_df_details['Prazo de Despacho'].values[0]
                data_enviado = pos_df_details['Data Despachado'].iloc[0].strftime('%d/%m/%Y') if not pd.isna(pos_df_details['Data Despachado'].values[0]) else "remessa ainda não enviada"
                prazo_transporte = int(pos_df_details['Prazo de Transporte'].iloc[0])
                data_prevista_recebimento = pos_df_details['Data Prevista de Recebimento'].iloc[0] if not pd.isna(pos_df_details['Data Prevista de Recebimento'].values[0]) else None
                data_recebido = pos_df_details['Data Recebido'].iloc[0].strftime('%d/%m/%Y') if not pd.isna(pos_df_details['Data Recebido'].values[0]) else False
                status = pos_df_details['Status Geral'].values[0]
                
                # Determine the color of status based on the status
                if "atrasada" in status:
                    status_color = danger_colour
                elif status == "prazo próximo do encerramento":
                    status_color = warning_colour
                elif "no prazo" in status or status == "Finalizada":
                    status_color = success_colour
                else:
                    status_color = "#333333"

                # Display the text with colored status
                st.markdown(f"""
                    ##### OC {selected_po_number}: <span style="color:{status_color};">{status}</span>
                    """, unsafe_allow_html=True)
                
                #Detalhes da OC e campo para atualizar informações da OC
                col5, col6 = st.columns(2, gap = "small")
                
                #Detalhes da OC
                with col5:
                    #OC info
                    st.write(f"**Comprador**: {pos_df_details['Comprador'].values[0]}")
                    st.write(f"**Data de envio da OC**: {pos_df_details['Data de Envio OC'].values[0]}")
                    st.write(f"**Prazo para envio**: {prazo_envio} {'dias' if prazo_envio > 1 else 'dia'}")
                    st.write(f"**Data prevista para envio**: {pos_df_details['Data Prevista Para Despacho'].iloc[0].strftime('%d/%m/%Y')}")
                    st.write(f"**Data despachado**: {data_enviado}")
                    st.write(f"**Prazo em transporte**: {prazo_transporte} {'dias' if prazo_transporte > 1 else 'dia'}")
                    if data_prevista_recebimento:
                        st.write(f"**Data prevista para recebimento**: {data_prevista_recebimento.strftime('%d/%m/%Y')}")
                    if data_recebido:
                        st.write(f"**Data de recebimento**: {data_recebido}")
                    st.write(f"**Descrição**: {pos_df_details['Descrição'].iloc[0]}")
                
                #Atualizar OC
                if pd.isna(pos_df_details['Data Despachado'].values[0]) or pd.isna(pos_df_details['Data Recebido'].values[0]):
                    with col6:
                        st.write("##### Atualizar")

                        # Initialize variables
                        data_despachado_input = None
                        data_recebido_input = None
                        
                        # Data de envio da remessa
                        if pd.isna(pos_df_details['Data Despachado'].values[0]):
                            data_despachado_input = st.date_input(
                                "Data em que a remessa foi **ENVIADA**", 
                                format="DD/MM/YYYY", 
                                min_value=pd.to_datetime(pos_df_details['Data de Envio OC'].iloc[0], format="%d/%m/%Y"), 
                                max_value=datetime.datetime.today()
                            )
                        
                        # Data recebido
                        if not pd.isna(pos_df_details['Data Despachado'].values[0]):
                            data_recebido_input = st.date_input(
                                "Data em que a remessa foi **RECEBIDA**", 
                                format="DD/MM/YYYY", 
                                min_value=pos_df_details['Data Despachado'].iloc[0], 
                                max_value=datetime.datetime.today()
                            )
                        
                        # Salva alterações
                        update_po = st.button("Salvar Alteração")    
                        if update_po:
                            if data_despachado_input:
                                new_data_prevista_recebimento = data_despachado_input + datetime.timedelta(days=prazo_transporte)
                                success = update_data_despachado(selected_po_number, data_despachado_input.strftime("%Y-%m-%d"), new_data_prevista_recebimento )
                                if success:
                                    st.success("Alteração salva com sucesso!")
                            else:
                                success = update_data_recebido(selected_po_number, data_recebido_input.strftime("%Y-%m-%d"))
                                if success:
                                    st.success("Alteração salva com sucesso!")
                                    st.balloons()                                                             

                #Comentários
                st.write("")
                st.write("##### Comentários") 

                # Container for comments
                comments_container = st.container()

                def display_comments():
                    comments = get_comments(selected_po_number)
                    if comments:
                        for comment in comments:
                            # Ensure comment[1] is a datetime object
                            comment_date = datetime.datetime.strptime(comment[1], '%Y-%m-%d %H:%M:%S')  # Adjust the format to match your date format
                            formatted_date = comment_date.strftime('%d-%m-%Y %H:%M')
                            
                            # Define coloured elements
                            colour1 = "#251C6E"
                            colour2 = "#F3C449"
                            if comment[0] == st.session_state.user[1]:
                                backgroundcolor = colour1
                            else:
                                backgroundcolor = colour2

                            st.markdown(f"""
                                <div style="display: flex; align-items: center;">
                                    <div style="flex: 0 0 auto; width: 10px; height: 10px; border-radius: 50%; background-color: {backgroundcolor}; margin-right: 10px;"></div>
                                    <div>
                                        <strong>{comment[0]} ({formatted_date})</strong><br>
                                        {comment[2]}
                                    </div>
                                </div>
                                <hr style="border-top: 1px solid {colour1}; margin: 10px 0;">
                            """, unsafe_allow_html=True)
                    else:
                        st.write("Nenhum comentário para esta ordem de compra.")

                # Initial display of comments
                with comments_container:
                    display_comments()

                # Add new comment
                new_comment = st.text_area("Novo comentário", key=f"comment_{selected_po_number}")
                if st.button("Comentar", key=f"button_{selected_po_number}"):
                    add_comment(selected_po_number, st.session_state.user[0], new_comment)
                    st.success("Comentário adicionado!")
                    with comments_container:
                        st.empty()
                        display_comments()
                 
            else:
                st.write("Selecione uma Ordem de Compra para ver detalhes e adicionar um comentário.")
    else:
        st.write("Nenhuma ordem de compra encontrada.")
    
# Main function to handle navigation
def main():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        
        #Logo e boas vindas
        st.sidebar.image("logo.png", width =70 )  # Display logo
        st.sidebar.write(f"**Bem vindo, {st.session_state.user[1]}!**")  # Display user's name
        st.sidebar.markdown("---") 

        #Título
        st.sidebar.title("Navegação")
        
        # Menu options
        menu_options = ["Todas Ordens de Compras","Adicionar Nova OC"]
        if st.session_state.user[4] == "admin":
            menu_options.append("Usuários")

        # Navigation menu
        selected_page = st.sidebar.radio("Menu", menu_options, label_visibility = "hidden")

        st.sidebar.markdown("---") 

        # Set the selected page
        st.session_state.page = selected_page

        if 'page' not in st.session_state:
            st.session_state.page = "Todas Ordens de Compras"

        # Render the selected page
        if st.session_state.page == "Adicionar Nova OC":
            add_new_order_page()
        elif st.session_state.page == "Usuários" and st.session_state.user[4] == "admin":
            settings_page()
        elif st.session_state.page == "Todas Ordens de Compras":
            all_pos_page()
    else:
        login()

if __name__ == "__main__":
    create_user_table()
    add_first_user()
    create_po_table()
    create_comments_table()
    main()
