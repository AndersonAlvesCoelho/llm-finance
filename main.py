from dotenv import load_dotenv, find_dotenv
from openai import OpenAI
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
import ofxparse
import pandas as pd
import os
from datetime import datetime
# from langchain_core.output_parsers.string import StrOutputParser


df = pd.DataFrame()


for extrato in os.listdir("extratos"):
    with open(f"extratos/{extrato}", encoding='ISO-8859-1') as ofx_file:
        ofx = ofxparse.OfxParser.parse(ofx_file)

    transactions_data = []
    for account in ofx.accounts:
        for transactions in account.statement.transactions:
            transactions_data.append({
                "Data": transactions.date,
                "Valor": transactions.amount,
                "Descrição": transactions.memo,
                "ID": transactions.id,
            })

    df_temp = pd.DataFrame(transactions_data)
    df_temp['Valor'] = df_temp['Valor'].astype(float)
    df_temp['Data'] = df_temp["Data"].apply(lambda x: x.date())

df = pd.concat([df, df_temp])
# ================
# LLM

df["Descrição"].values

_ = load_dotenv(find_dotenv())

template = """
Você é um analista de dados, trabalhando em um projeto de limpeza de dados. Seu trabalho é escolher uma categoria adequada para cada lançamento financeiro que vou te enviar. 
Todos são transações financeiras de uma pessoa física.

Escolha uma dentre as seguintes categorias:
- Alimentação
- Receitas
- Saúde
- Mercado
- Compras
- Transporte
- Investimento
- Transferências para terceiros
- Telefone
- Moradia
- Outros

**Por favor, responda apenas com a categoria correspondente ao seguinte item:**
Você não deve fornecer mais informações, perguntas ou explicações. Apenas forneça a categoria.

Item: {text}
"""


prompt = PromptTemplate.from_template(template=template)
chat = ChatGroq(model="llama-3.1-8b-instant")
chain = prompt | chat


category = []
for transaction in list(df["Descrição"].values):
    category += [chat.invoke(template.format(text=transaction)).content]


df["Categoria"] = category
df.to_csv("finances.csv")