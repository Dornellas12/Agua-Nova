"""banco.py — conexão com o banco de dados SQLite e criação das tabelas.

O banco é um único arquivo (dados/agua_nova.db). Para fazer backup, basta copiá-lo.
"""
import sqlite3
from pathlib import Path

DB = Path(__file__).parent / "dados" / "agua_nova.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS config (chave TEXT PRIMARY KEY, valor TEXT);

CREATE TABLE IF NOT EXISTS bairros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    zona TEXT NOT NULL DEFAULT 'Sem zona',
    frete REAL NOT NULL DEFAULT 0,          -- frete embutido por galão
    ativo INTEGER NOT NULL DEFAULT 1);

CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL, marca TEXT DEFAULT '', tamanho TEXT DEFAULT '',
    tipo TEXT NOT NULL,                      -- 'Galão' ou 'Descartável'
    un_fardo INTEGER DEFAULT 1,              -- unidades por fardo
    preco_unit REAL DEFAULT 0,               -- galão: preço da troca
    preco_fardo REAL DEFAULT 0,
    preco_novo REAL DEFAULT 0,               -- galão: preço do galão novo
    custo REAL DEFAULT 0,                    -- custo por unidade (para calcular o lucro)
    est_min INTEGER DEFAULT 0,
    est_cheio INTEGER DEFAULT 0,             -- galão cheio / unidades descartáveis
    est_vazio INTEGER DEFAULT 0,             -- galões vazios no depósito
    ativo INTEGER DEFAULT 1);

CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL, telefone TEXT DEFAULT '', endereco TEXT DEFAULT '',
    bairro_id INTEGER REFERENCES bairros(id),
    frete_especial REAL,                     -- NULL = usa o frete do bairro
    obs TEXT DEFAULT '', ativo INTEGER DEFAULT 1, criado_em TEXT);

CREATE TABLE IF NOT EXISTS emprestimos (     -- galões emprestados a clientes
    cliente_id INTEGER, produto_id INTEGER, qtd INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (cliente_id, produto_id));

CREATE TABLE IF NOT EXISTS vendas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT NOT NULL, cliente_id INTEGER,  -- NULL = cliente avulso
    origem TEXT, tipo_entrega TEXT, pagamento TEXT, total REAL,
    status TEXT DEFAULT 'Ativa', data_entrega TEXT,
    entregador TEXT DEFAULT '', ordem INTEGER DEFAULT 0, entregue INTEGER DEFAULT 0,
    obs TEXT DEFAULT '');

CREATE TABLE IF NOT EXISTS venda_itens (
    id INTEGER PRIMARY KEY AUTOINCREMENT, venda_id INTEGER, produto_id INTEGER,
    modo TEXT, operacao TEXT DEFAULT '', qtd INTEGER, preco REAL);

CREATE TABLE IF NOT EXISTS pagamentos_fiado (
    id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id INTEGER, data TEXT,
    valor REAL, forma TEXT, obs TEXT DEFAULT '');

CREATE TABLE IF NOT EXISTS compras (
    id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, fornecedor TEXT,
    produto_id INTEGER, modo TEXT, qtd INTEGER, custo_unit REAL, total REAL, obs TEXT DEFAULT '');

CREATE TABLE IF NOT EXISTS movimentos (      -- histórico de todo movimento de estoque
    id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, produto_id INTEGER,
    tipo TEXT, d_cheio INTEGER, d_vazio INTEGER, ref TEXT);

CREATE TABLE IF NOT EXISTS despesas (
    id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, categoria TEXT, descricao TEXT DEFAULT '', valor REAL);
"""


def conectar():
    DB.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def iniciar():
    con = conectar()
    try:
        with con:
            con.executescript(SCHEMA)
            # atualização de bancos criados na V1: adiciona a coluna de custo
            if "custo" not in [r["name"] for r in con.execute("PRAGMA table_info(produtos)")]:
                con.execute("ALTER TABLE produtos ADD COLUMN custo REAL DEFAULT 0")
    finally:
        con.close()


def consultar(sql, params=()):
    """Executa um SELECT e devolve uma lista de dicionários."""
    con = conectar()
    try:
        return [dict(r) for r in con.execute(sql, params).fetchall()]
    finally:
        con.close()


def executar(sql, params=()):
    """Executa INSERT/UPDATE/DELETE e devolve o id criado."""
    con = conectar()
    try:
        with con:
            return con.execute(sql, params).lastrowid
    finally:
        con.close()
