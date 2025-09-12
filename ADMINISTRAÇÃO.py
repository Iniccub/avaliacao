# Substituir importação dinâmica por importação direta
import streamlit as st
import pandas as pd
import os
from openpyxl import load_workbook
from streamlit_js_eval import streamlit_js_eval
import importlib
import sys

# Importar diretamente os módulos
from mongodb_config import get_database
from fornecedores_por_unidade import get_fornecedores
from unidades import get_unidades
#from perguntas_por_fornecedor import get_perguntas

# Função para importação dinâmica
def import_module(module_name, file_path):
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None:
            st.error(f"Erro ao importar {module_name}: Arquivo não encontrado")
            return None
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        st.error(f"Erro ao importar {module_name}: {str(e)}")
        return None

# Importar módulos locais de forma consistente
fornecedores_module = import_module('fornecedores_por_unidade', 'fornecedores_por_unidade.py')
unidades_module = import_module('unidades', 'unidades.py')
perguntas_module = import_module('perguntas_por_fornecedor', 'perguntas_por_fornecedor.py')

# Acessar os atributos dos módulos usando as novas funções MongoDB
try:
    # Tentar obter dados do MongoDB
    unidades = unidades_module.get_unidades()
    fornecedores_por_unidade = fornecedores_module.get_fornecedores()
    perguntas_por_fornecedor = perguntas_module.get_perguntas()
    
    # Verificar se os dados foram obtidos corretamente
    if not unidades or not fornecedores_por_unidade or not perguntas_por_fornecedor:
        raise Exception("Dados vazios retornados do MongoDB")
        
    # Adicionar mensagem de sucesso
    st.success("Dados carregados com sucesso do Banco de Dados")
    
except Exception as e:
    # Fallback para os dados originais apenas se houver erro
    st.error(f"Erro ao conectar com o Banco de Dados: {str(e)}. Usando dados locais como fallback.")
    fornecedores_por_unidade = getattr(fornecedores_module, 'fornecedores_por_unidade', {})
    unidades = getattr(unidades_module, 'unidades', [])
    perguntas_por_fornecedor = getattr(perguntas_module, 'perguntas_por_fornecedor', {})

# Listas fixas
meses_raw = ['31/01/2025', '28/02/2025', '31/03/2025', '30/04/2025', '31/05/2025', '30/06/2025', '31/07/2025', '31/08/2025',
         '30/09/2025', '31/10/2025', '30/11/2025', '31/12/2025']

# Dicionário para converter números de mês em abreviações em português
meses_abrev = {
    '01': 'JAN', '02': 'FEV', '03': 'MAR', '04': 'ABR',
    '05': 'MAI', '06': 'JUN', '07': 'JUL', '08': 'AGO',
    '09': 'SET', '10': 'OUT', '11': 'NOV', '12': 'DEZ'
}

# Formatar os meses para exibição
meses = [f"{meses_abrev[data.split('/')[1]]}/{data.split('/')[2][-2:]}" for data in meses_raw]

# Obter o mês atual e o mês anterior para pré-seleção
import datetime
mes_atual = datetime.datetime.now().month
mes_anterior = mes_atual - 1 if mes_atual > 1 else 12
# Ajustar o índice para a lista de meses (índice começa em 0, meses começam em 1)
indice_mes_anterior = mes_anterior - 1
# Opções de respostas
opcoes = ['Atende Totalmente', 'Atende Parcialmente', 'Não Atende', 'Não se Aplica']


def carregar_fornecedores():
    if os.path.exists(CAMINHO_FORNECEDORES):
        try:
            from fornecedores import fornecedores
            return fornecedores
        except ImportError:
            return []
    return []

CAMINHO_FORNECEDORES = 'fornecedores_por_unidade.py'

# Modificar a função salvar_fornecedores para usar MongoDB
def salvar_fornecedores(fornecedor, unidades_selecionadas):
    try:
        # Usar a função do módulo para adicionar/atualizar fornecedor
        success = fornecedores_module.add_fornecedor(fornecedor, unidades_selecionadas)
        if success:
            # Atualizar a variável local
            global fornecedores_por_unidade
            fornecedores_por_unidade = fornecedores_module.get_fornecedores()
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao salvar fornecedor: {str(e)}")
        return False

@st.dialog("Cadastrar Novo Fornecedor", width="large")
def cadastrar_fornecedor():
    st.subheader("Cadastro de Novo Fornecedor")
    
    with st.form("formulario_cadastro_fornecedor"):
        novo_fornecedor = st.text_input('Nome do fornecedor')
        unidades_selecionadas = st.multiselect("Selecione as unidades", options=unidades)
        
        submitted = st.form_submit_button("Salvar")
        
        if submitted:
            novo_fornecedor = novo_fornecedor.strip()
            # Adicionar validações extras
            if len(novo_fornecedor) < 3:
                st.warning("O nome do fornecedor deve ter pelo menos 3 caracteres")
                return
            if not unidades_selecionadas:
                st.warning("Selecione pelo menos uma unidade")
                return
            
            # Resto do código permanece igual
            if novo_fornecedor and unidades_selecionadas:
                if novo_fornecedor not in fornecedores_por_unidade:
                    # Salvar o novo fornecedor com suas unidades
                    salvar_fornecedores(novo_fornecedor, unidades_selecionadas)
                    st.toast(f'Fornecedor "{novo_fornecedor}" adicionado com sucesso!', icon='✅')
                else:
                    st.warning('Fornecedor já existe na lista')
            else:
                st.warning('Por favor, preencha o nome do fornecedor e selecione pelo menos uma unidade')

with st.sidebar:
    st.image("CSA.png", width=150)

# Aplicar estilo CSS para centralizar imagens na sidebar
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] [data-testid="stImage"] {
            display: block;
            margin-left: 70px;
            margin-right: auto;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.sidebar.write('---')

# Sidebar, Caixas de seleção da unidade, período e fornecedor
unidade = st.sidebar.selectbox('Selecione a unidade', index=None, options=unidades, placeholder='Escolha a unidade')
periodo = st.sidebar.selectbox('Selecione o período avaliado', index=indice_mes_anterior, options=meses, placeholder='Defina o período de avaliação')

# Filtrar fornecedores baseado na unidade selecionada
if unidade:
    fornecedores_filtrados = [
        fornecedor for fornecedor, unidades in fornecedores_por_unidade.items()
        if unidade in unidades
    ]
    # Ordenar fornecedores em ordem alfabética
    fornecedores_filtrados.sort()
    
    fornecedor = st.sidebar.selectbox('Selecione o fornecedor a ser avaliado', 
                                     index=None, 
                                     options=fornecedores_filtrados, 
                                     placeholder='Selecione o prestador/fornecedor')
else:
    fornecedor = st.sidebar.selectbox('Selecione o fornecedor a ser avaliado', 
                                     index=None, 
                                     options=[], 
                                     placeholder='Primeiro selecione uma unidade')

# Tela para cadastrar nova pergunta
@st.dialog("Cadastrar Nova Pergunta", width="large")
def cadastrar_pergunta():
    st.subheader("Cadastro de Nova Pergunta")
    
    # Criar um formulário
    with st.form("formulario_cadastro_pergunta"):
        # Obter lista de fornecedores das unidades
        todos_fornecedores = list(fornecedores_por_unidade.keys())
        fornecedor = st.selectbox("Selecione o fornecedor", options=todos_fornecedores)
        categoria = st.selectbox('Categoria',('Atividades Operacionais', 'Segurança', 'Qualidade'))
        nova_pergunta = st.text_area("Nova pergunta", placeholder="Digite a nova pergunta aqui")
        
        # Botão de submit do formulário
        submitted = st.form_submit_button("Salvar")
        
        if submitted:
            if fornecedor and categoria and nova_pergunta:
                try:
                    # Usar a função do módulo para adicionar pergunta
                    success = perguntas_module.add_pergunta(fornecedor, categoria, nova_pergunta)
                    if success:
                        # Atualizar a variável local
                        global perguntas_por_fornecedor
                        perguntas_por_fornecedor = perguntas_module.get_perguntas()
                        st.success("Pergunta adicionada com sucesso!")
                    else:
                        st.warning("Não foi possível adicionar a pergunta.")
                except Exception as e:
                    st.error(f"Erro ao adicionar pergunta: {str(e)}")
            else:
                st.warning("Por favor, preencha todos os campos.")

#if st.sidebar.button("Cadastrar nova pergunta"):
    #cadastrar_pergunta()

# Título
st.markdown(
    "<h1 style='text-align: left; font-family: Open Sauce; color: #104D73;'>"
    'ADFS - AVALIAÇÃO DE DESEMPENHO DE FORNECEDORES DE SERVIÇOS</h1>',
    unsafe_allow_html=True
)

# Exibir o período selecionado abaixo do título
if periodo:
    st.markdown(f"<h3 style='text-align: left; font-family: Open Sauce; color: #104D73;'>Período selecionado: {periodo}</h3>", unsafe_allow_html=True)

st.write('---')

# Subtitulo
if fornecedor and unidade and periodo:
    st.subheader(f'Contratada/Fornecedor: {fornecedor}')
    st.write(f'Unidade: {unidade}')
    st.write(f'Período avaliado: {periodo}')
    st.write('---')

    # Determinação das abas
    tab1, tab2, tab3 = st.tabs(['Atividades Operacionais', 'Segurança', 'Qualidade'])

    respostas = []
    perguntas = []

    # Obter perguntas específicas do fornecedor
    perguntas_fornecedor = perguntas_por_fornecedor.get(fornecedor, {})

    with tab1:
        perguntas_tab1 = perguntas_fornecedor.get('Atividades Operacionais', [])
        for i, pergunta in enumerate(perguntas_tab1):
            resposta = st.selectbox(pergunta, options=opcoes, index=None, 
                                  placeholder='Selecione uma opção', 
                                  key=f'op_{i}_{pergunta}')
            respostas.append(resposta)
            perguntas.append(pergunta)

    with tab2:
        perguntas_tab2 = perguntas_fornecedor.get('Segurança', [])
        for i, pergunta in enumerate(perguntas_tab2):
            resposta = st.selectbox(pergunta, options=opcoes, index=None, 
                                  placeholder='Selecione uma opção', 
                                  key=f'seg_{i}_{pergunta}')
            respostas.append(resposta)
            perguntas.append(pergunta)

    with tab3:
        perguntas_tab3 = perguntas_fornecedor.get('Qualidade', [])
        for i, pergunta in enumerate(perguntas_tab3):
            resposta = st.selectbox(pergunta, options=opcoes, index=None, 
                                  placeholder='Selecione uma opção', 
                                  key=f'qual_{i}_{pergunta}')
            respostas.append(resposta)
            perguntas.append(pergunta)

    st.sidebar.write('---')

    # Após coletar as perguntas e respostas de cada aba
    categorias = (
            ['Atividades Operacionais'] * len(perguntas_tab1) +
            ['Segurança'] * len(perguntas_tab2) +
            ['Qualidade'] * len(perguntas_tab3)
    )

    # Inicialização de estado da sessão
    if 'pesquisa_salva' not in st.session_state:
        st.session_state.pesquisa_salva = False
    
    # Botão para salvar no MongoDB
    if st.button('Enviar pesquisa'):
        try:
            if None in respostas:
                st.warning('Por favor, responda todas as perguntas antes de salvar.')
            else:
                # Criar barra de progresso
                progress_bar = st.progress(0, text="Iniciando processo de salvamento...")
                
                # Criar DataFrame com as respostas
                df_respostas = pd.DataFrame({
                    'Unidade': unidade,
                    'Período': meses_raw[meses.index(periodo)],
                    'Fornecedor': fornecedor,
                    'categorias': categorias,
                    'Pergunta': perguntas,
                    'Resposta': respostas,
                    'Data_Avaliacao': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                
                # Atualizar progresso - 33%
                progress_bar.progress(33, text="Salvando no Banco de dados...")
                
                # Salvar no MongoDB (coleção avaliacoes_adm)
                try:
                    db = get_database()
                    collection = db["avaliacoes_adm"]
                    
                    # Converter DataFrame para dicionário e inserir no MongoDB
                    avaliacao_dict = df_respostas.to_dict('records')
                    collection.insert_many(avaliacao_dict)
                    
                    # Atualizar progresso - 66%
                    progress_bar.progress(66, text="Gerando arquivo Excel...")
                    
                    # Gerar arquivo Excel
                    def gerar_nome_arquivo_avaliacao(fornecedor, periodo, unidade, origem):
                        # Limpar nome do fornecedor
                        nome_fornecedor = "".join(x for x in fornecedor if x.isalnum() or x in ['_', '-'])
                        
                        # Converter período para formato abreviado
                        periodo_parts = periodo.split('/')
                        if len(periodo_parts) >= 2:
                            mes_num = periodo_parts[1]
                            ano_completo = periodo_parts[2] if len(periodo_parts) > 2 else periodo_parts[0][-4:]
                            ano_abrev = ano_completo[-2:]
                        else:
                            mes_num = '01'
                            ano_abrev = '25'
                        
                        # Dicionário para conversão de mês
                        meses_abrev = {
                            '01': 'JAN', '02': 'FEV', '03': 'MAR', '04': 'ABR',
                            '05': 'MAI', '06': 'JUN', '07': 'JUL', '08': 'AGO',
                            '09': 'SET', '10': 'OUT', '11': 'NOV', '12': 'DEZ'
                        }
                        nome_periodo = f"{meses_abrev[mes_num]}-{ano_abrev}"
                        
                        nome_unidade = "".join(x for x in unidade if x.isalnum() or x in ['_', '-'])
                        
                        if origem == 'SUPRIMENTOS':
                            nome_arquivo = f'{nome_fornecedor}_{nome_periodo}_{nome_unidade}_SUP.xlsx'
                        else:
                            nome_arquivo = f'{nome_fornecedor}_{nome_periodo}_{nome_unidade}.xlsx'
                        
                        return nome_arquivo
                    
                    # Gerar nome do arquivo
                    nome_arquivo = gerar_nome_arquivo_avaliacao(fornecedor, meses_raw[meses.index(periodo)], unidade, 'ADMINISTRAÇÃO')
                    
                    # Criar arquivo Excel em memória
                    from io import BytesIO
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_respostas.to_excel(writer, index=False, sheet_name='Avaliação')
                    
                    # Atualizar progresso - 100%
                    progress_bar.progress(100, text="Processo concluído!")
                    
                    st.success('Avaliação realizada e salva com SUCESSO! Obrigado.')
                    
                    # Botão de download do arquivo Excel
                    st.download_button(
                        label="📥 Baixar Arquivo Excel da Avaliação",
                        data=output.getvalue(),
                        file_name=nome_arquivo,
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        type="primary"
                    )
                    
                    st.info(f"📁 **Arquivo gerado:** {nome_arquivo}")
                    
                    # Aguardar um momento para mostrar a mensagem de sucesso
                    import time
                    time.sleep(3)
                    
                    # Recarregar a página automaticamente
                    streamlit_js_eval(js_expressions='parent.window.location.reload()')
                    
                except Exception as e:
                    st.error(f"Erro ao salvar no MongoDB: {str(e)}")
                    progress_bar.progress(100, text="Erro ao salvar no banco de dados")
                
        except Exception as e:
            st.error(f"Erro ao processar a solicitação: {str(e)}")

# Rodapé com copyright
st.sidebar.markdown("""
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f0f0f0;
        color: #333;
        text-align: center;
        padding: 10px;
        font-size: 14px;
    }
    </style>
    <div class="footer">
        © 2025 FP&A e Orçamento - Rede Lius. Todos os direitos reservados.
    </div>
    """, unsafe_allow_html=True)

# Verificar existência dos arquivos necessários
required_files = ['fornecedores_por_unidade.py', 'unidades.py', 'perguntas_por_fornecedor.py']
for file in required_files:
    if not os.path.exists(file):
        st.error(f"Arquivo {file} não encontrado. Por favor, verifique se todos os arquivos necessários estão presentes.")
        st.stop()