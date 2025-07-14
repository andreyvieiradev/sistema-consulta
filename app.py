from flask import Flask, render_template, jsonify, request
import requests
import json
from datetime import datetime, timedelta
from collections import Counter

app = Flask(__name__)

# --- CONFIGURAÇÕES DA API ---
AUTH_TOKEN = ''
ENDPOINT_URL = 'https://api.maxiprod.com.br/graphql/'
REGISTROS_POR_PAGINA = 50

# --- FUNÇÕES DE BUSCA NA API ---
def executar_query_graphql(query, variaveis):
    headers = {'Content-Type': 'application/json', 'Authorization': f'Basic {AUTH_TOKEN}'}
    payload = {'query': query, 'variables': variaveis}
    print("DEBUG: Enviando payload para a API:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    try:
        response = requests.post(ENDPOINT_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro de Conexão: {e}")
        return {'error': str(e), 'status_code': 500}

# --- ROTAS DA APLICAÇÃO ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/ordens')
def get_ordens():
    pagina = int(request.args.get('page', 1))
    setor_codigo = request.args.get('setor') or None
    estado = request.args.get('estado') or None
    
    query_graphql = """
    query BuscaOrdens($where: OrdemDeProducaoFilterInput, $take: Int, $skip: Int, $order: [OrdemDeProducaoSortInput!]) {
      ordensDeProducao(where: $where, take: $take, skip: $skip, order: $order) {
        totalCount, items { numero, item { codigo, descricao }, quantidade, estado, necessidadeData }
      }
    }
    """
    filtros = []
    
    # Regras de filtro específicas
    if setor_codigo == 'CORTE.PLASMA':
        filtros.extend([{'item': {'codigo': {'nstartsWith': '200'}}}, {'item': {'codigo': {'nstartsWith': '100'}}}])
    
    if estado and estado != 'TODAS':
        filtros.append({'estado': {'eq': estado}})
    elif not estado: 
        filtros.append({'estado': {'eq': 'A_PRODUZIR'}})
    
    # Filtro principal por setor, usando o caminho que foi validado
    if setor_codigo:
        filtros.append({"item": {"roteiros": {"some": {"centroDeTrabalho": {"codigo": {"eq": setor_codigo}}}}}})
    
    variaveis = {
        'take': REGISTROS_POR_PAGINA, 'skip': (pagina - 1) * REGISTROS_POR_PAGINA,
        'order': [{'numero': 'DESC'}], 'where': {'and': filtros} if filtros else {}
    }
    
    dados = executar_query_graphql(query_graphql, variaveis)
    return jsonify(dados)


if __name__ == '__main__':
    app.run(debug=True)
