import pandas as pd
import json
import os
import math
import numpy as np

from openpyxl.utils import column_index_from_string

from openai import OpenAI

LOCAL_OUTPUT_BASE_DIR = "output"
os.makedirs(LOCAL_OUTPUT_BASE_DIR, exist_ok=True)

def get_cell_value(df, cell_address):
    col_letter = ''.join(filter(str.isalpha, cell_address))
    row_number = int(''.join(filter(str.isdigit, cell_address))) - 1 # excel krece numeraciju od 1
    col_index = column_index_from_string(col_letter) - 1 # excel krece numeraciju od 1
    return df.iloc[row_number, col_index]

def remove_nan(obj):
    if isinstance(obj, float) and math.isnan(obj):
        return None
    elif isinstance(obj, dict):
        return {k: remove_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [remove_nan(i) for i in obj]
    return obj

def to_JSON(file_path):

    def clean_df(df):
        df = df.copy()
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].astype(str)
            else:
                df[col] = df[col].replace({np.nan: None})
        return df.to_dict(orient='records')

    all_data = {}

    #LIST KUPAC
    sheet_name_kupac = 'Kupac'
    print(f"Obrada lista {sheet_name_kupac}")
    try:
        df1= pd.read_excel(file_path, engine='openpyxl', usecols='E:F', skiprows=4, header=None, nrows=12, sheet_name=0)
        df1.columns= ['Atribut', 'Vrednost']
        all_data["osnovne_informacije"] = clean_df(df1)
    except Exception as e:
        print(f"Nije moguće pročitati list '{sheet_name_kupac}', tabela osnovne informacije: {e}. Preskačem.")
        all_data["osnovne_informacije"] = []

    try:
        df2= pd.read_excel(file_path, engine='openpyxl', usecols='E:F', skiprows=18, header=None, nrows=29, sheet_name=0)
        df2.columns= ['Atribut', 'Vrednost RSD bez PDV']
        df2 = df2.dropna()
        all_data["prometRSD"] = clean_df(df2)
    except Exception as e:
        print(f"Nije moguće pročitati list '{sheet_name_kupac}', tabela promet: {e}. Preskačem.")
        all_data["prometRSD"] = []


    try:
        df3= pd.read_excel(file_path, engine='openpyxl', usecols='I:J', skiprows=9, header=None, nrows=11, sheet_name=0)
        df3.columns= ['Atribut', 'Vrednost']
        all_data["ocena_rizika"] = clean_df(df3)
    except Exception as e:
        print(f"Nije moguće pročitati list '{sheet_name_kupac}', tabela ocena rizika: {e}. Preskačem.")
        all_data["ocena_rizika"] = []


    #EUR
    try:
        df4= pd.read_excel(file_path, engine='openpyxl', usecols='I:N', skiprows=26, header=0, nrows=21, sheet_name=0)
        df4.columns = df4.columns.astype(str)
        df4 = df4.rename(columns={df4.columns[0]: "Atribut"})
        all_data["finansijska_analizaEUR"] = clean_df(df4)
    except Exception as e:
        print(f"Nije moguće pročitati list '{sheet_name_kupac}', tabela finansijska analiza: {e}. Preskačem.")
        all_data["finansijska_analizaEUR"] = []


    try:
        df5= pd.read_excel(file_path, engine='openpyxl', usecols='E:F', skiprows=50, header=None, nrows=6, sheet_name=0)
        df5.columns = ['Atribut', 'Vrednost RSD']
        all_data["predlogRSD"] = clean_df(df5)
    except Exception as e:
        print(f"Nije moguće pročitati list '{sheet_name_kupac}', tabela predlog kreditnog limita: {e}. Preskačem.")
        all_data["predlogRSD"] = []

    
    try:
        df6_1 = pd.read_excel(file_path, sheet_name=0, usecols="L:O", skiprows=7, nrows=1, header=1, engine='openpyxl')
        prefix = df6_1.columns[0]
        df6_1 = df6_1.drop(columns=[prefix])
        df6_1.columns = [f"{prefix} {col}" for col in df6_1.columns]

        df6_2 = pd.read_excel(file_path, sheet_name=0, usecols="L:M", skiprows=10, nrows=1, header=None, engine='openpyxl')
        col_name = df6_2.iloc[0,0]
        value = df6_2.iloc[0,1]
        df6_2= pd.DataFrame({col_name: [value]})

        df6_3 = pd.read_excel(file_path, sheet_name=0, usecols="L:M", skiprows=11, nrows=1, header=None, engine='openpyxl')
        col_name = df6_3.iloc[0,0]
        value = df6_3.iloc[0,1]
        df6_3= pd.DataFrame({col_name: [value]})

        df6 = pd.concat([df6_1, df6_2, df6_3], axis=1)
        all_data["bonitetna_ocena"] = clean_df(df6)
    except Exception as e:
            print(f"Nije moguće pročitati list '{sheet_name_kupac}', tabela bonitetna ocena: {e}. Preskačem.")
            all_data["bonitetna_ocena"] = []


    try:
        df7 = pd.read_excel(
            file_path,
            sheet_name=0,
            usecols="I:K",
            skiprows=52,
            header=0,
            engine='openpyxl'
        )
        if df7.dropna(how='all').empty:
            print("Tabela kreditne istorije je prazna.")
            df7 = df7.dropna(how='all')
        all_data["istorijaKL"] = clean_df(df7)
    except Exception as e:
        print(f"Nije moguće pročitati list '{sheet_name_kupac}', tabela kreditne istorije: {e}. Preskačem.")
        all_data["istorijaKL"] = []

    # LIST SUDSKI SPOROVI
    sheet_name_sporovi = 'Sudski sporovi'
    print(f"Obrada lista {sheet_name_sporovi}")
    try:
        df9 = pd.read_excel(file_path, sheet_name=sheet_name_sporovi, engine='openpyxl')
        all_data["sudski sporovi"] = clean_df(df9)
        if df9.empty:
            print("Tabela sudskih sporova je prazna.")
    except Exception as e:
        print(f"Nije moguće pročitati list '{sheet_name_sporovi}': {e}. Preskačem.")
        all_data["sudski sporovi"] = []

    #LIST REZIME
    sheet_name_rezime = 'Rezime (EUR)'
    print(f"Obrada lista {sheet_name_rezime}")
    try:
        df8 = pd.read_excel(file_path, sheet_name=sheet_name_rezime, skiprows=3, nrows=30, header=0, engine='openpyxl')
        df8 = df8.loc[:, ~df8.columns.astype(str).str.startswith("Unnamed")]
        all_data["rezimeEUR"] = clean_df(df8)
    except Exception as e:
        print(f"Nije moguće pročitati list '{sheet_name_rezime}': {e}. Preskačem.")
        all_data["rezimeEUR"] = []


     # LIST POVEZANA LICA
    sheet_name_povezana = 'Povezana lica'
    print(f"Obrada lista {sheet_name_povezana}")
    try:
        df10 = pd.read_excel(file_path, sheet_name=sheet_name_povezana, usecols="A:D",  header=0, engine='openpyxl')
        all_data["povezana_lica"] = clean_df(df10)
    except Exception as e:
        print(f"Nije moguće pročitati list '{sheet_name_povezana}': {e}. Preskačem.")
        all_data["povezana_lica"] = []

    # LIST BLOKADE
    sheet_name_blokade = 'Blokade'
    print(f"Obrada lista {sheet_name_blokade}")
    try:
        df11 = pd.read_excel(file_path, sheet_name=sheet_name_blokade,  header=0, engine='openpyxl')
        all_data['istorija_blokada'] = clean_df(df11)
    except Exception as e:
        print(f"Nije moguće pročitati list '{sheet_name_blokade}': {e}. Preskačem.")
        all_data["istorija_blokada"] = []


    result = json.loads(json.dumps(all_data, default=str))
    clean_result = json.loads(json.dumps(result, default=str))
    clean_result = remove_nan(all_data)
    return clean_result   

def generate_AIcomment(prompt, key):
  # Inicijalizuj klijenta
  client = OpenAI(api_key=key)

  response = client.responses.create(
      model = "gpt-5-2025-08-07",
      input=prompt,
      reasoning={
          "effort": "high"
      },
      text={
          "verbosity": "high"
      },
      max_output_tokens= 15000
  )
  
  return response.output_text