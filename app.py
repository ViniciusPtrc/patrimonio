from flask import Flask, render_template, request
import pandas as pd
import os

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Lista de valores a serem ignorados
valores_ignorados = {"37", "210", "208", "57", "147", "235", "238", "242", "260", "347",
                      "367", "447", "497", "597", "395", "443", "430", "478", "577", "645", "100", "442.75", "R$ Unitário"}

def comparar_planilhas(arquivos):
    patrimonio_data = []
    
    for arquivo in arquivos:
        xls = pd.ExcelFile(arquivo)
        for aba in xls.sheet_names:
            aba_limpa = aba.strip().upper()  # Remove espaços extras e coloca tudo em maiúsculas
            if "DEM" in aba_limpa.split():  # Verifica se "DEM" é uma palavra separada
                print(f"Ignorando aba {aba} do arquivo {arquivo} por conter 'DEM'")
                continue
            try:
                df = pd.read_excel(arquivo, sheet_name=aba, dtype=str, skiprows=13)  # Começa a partir da linha 14
                if df.shape[1] < 3:  # Verifica se há pelo menos 3 colunas
                    print(f"Ignorando {arquivo} - Aba {aba}: menos de 3 colunas disponíveis")
                    continue
                df = df.iloc[:, [2]]  # Seleciona apenas a coluna C (índice 2)
                df = df.dropna()
                for valor in df.iloc[:, 0]:
                    valor = valor.strip()
                    if valor in valores_ignorados:
                        continue
                    patrimonio_data.append((valor, os.path.basename(arquivo), aba))
            except Exception as e:
                print(f"Erro ao processar {arquivo} - Aba {aba}: {e}")
    
    df_patrimonios = pd.DataFrame(patrimonio_data, columns=["Número Patrimônio", "Arquivo", "Aba"])
    patrim_repetidos = df_patrimonios[df_patrimonios.duplicated(subset=["Número Patrimônio"], keep=False)]
    resultado = patrim_repetidos.groupby("Número Patrimônio")[["Arquivo", "Aba"]].apply(lambda x: x.values.tolist()).reset_index()
    resultado.columns = ["Número Patrimônio", "Localizações"]
    return resultado.to_dict(orient='records')

@app.route('/', methods=['GET', 'POST'])
def index():
    resultados = []
    if request.method == 'POST':
        files = request.files.getlist("file")
        file_paths = []
        
        for file in files:
            if file.filename.endswith(".xlsx"):
                path = os.path.join(UPLOAD_FOLDER, file.filename)
                file.save(path)
                file_paths.append(path)
        
        if file_paths:
            resultados = comparar_planilhas(file_paths)
        
    return render_template("index.html", resultados=resultados)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)

