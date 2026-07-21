import toml
import gspread
from google.oauth2.service_account import Credentials
import os

def setup():
    print("Conectando con Google Sheets...")
    secrets = toml.load('.streamlit/secrets.toml')
    scope = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_info(secrets['gcloud'], scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(secrets['private_gsheets_url'])
    
    # Abrir la pestaña 'Resumen cocina' (con 'c' minúscula)
    ws = sheet.worksheet('Resumen cocina')
    ws.clear()
    
    # Definir filas a insertar
    rows = [
        # Fila 1: Cabeceras
        ["Código", "Plato (Automático)", "Total a Cocinar", "Fecha a consultar:", '=TEXTO(HOY(); "dd/mm/yyyy")'],
        # Fila 2: Separador
        ["--- PRIMEROS ---", "", "", "", ""],
        # Fila 3 y 4: Primeros
        ["1a", "", "", "", ""],
        ["1b", "", "", "", ""],
        # Fila 5: Separador
        ["--- SEGUNDOS ---", "", "", "", ""],
        # Fila 6 y 7: Segundos
        ["2a", "", "", "", ""],
        ["2b", "", "", "", ""],
        # Fila 8: Separador
        ["--- ACOMPAÑAMIENTOS ---", "", "", "", ""],
        # Fila 9, 10, 11: Acompañamientos
        ["4a", "", "", "", ""],
        ["4b", "", "", "", ""],
        ["4c", "", "", "", ""],
        # Fila 12: Separador
        ["--- ENSALADAS ---", "", "", "", ""],
        # Fila 13 y 14: Ensaladas
        ["5a", "", "", "", ""],
        ["5b", "", "", "", ""],
        # Fila 15: Separador
        ["--- POSTRES ---", "", "", "", ""],
        # Fila 16, 17, 18, 19: Postres
        ["3a", "", "", "", ""],
        ["3b", "", "", "", ""],
        ["3c", "", "", "", ""],
        ["3d", "", "", "", ""]
    ]
    
    # Escribir estructura base
    ws.update('A1:E20', rows, raw=False)
    
    # Rellenar fórmulas fila por fila con las celdas correctas
    for row_idx in [3, 4, 6, 7, 9, 10, 11, 13, 14, 16, 17, 18, 19]:
        # Fórmula de buscar plato
        formula_buscar = f'=SI.ERROR(BUSCARV(A{row_idx}; Menu!A:B; 2; FALSO); "")'
        
        # Fórmula de contar reservas (filtra por fecha en E1 y estado distinto a Cancelada)
        formula_contar = (
            f'=SI(B{row_idx}=""; ""; '
            f'CONTAR.SI.CONJUNTO(Reservas!A:A; E$1 & "*"; Reservas!D:D; B{row_idx}; Reservas!K:K; "<>Cancelada") + '
            f'CONTAR.SI.CONJUNTO(Reservas!A:A; E$1 & "*"; Reservas!E:E; B{row_idx}; Reservas!K:K; "<>Cancelada") + '
            f'CONTAR.SI.CONJUNTO(Reservas!A:A; E$1 & "*"; Reservas!F:F; B{row_idx}; Reservas!K:K; "<>Cancelada") + '
            f'CONTAR.SI.CONJUNTO(Reservas!A:A; E$1 & "*"; Reservas!G:G; B{row_idx}; Reservas!K:K; "<>Cancelada") + '
            f'CONTAR.SI.CONJUNTO(Reservas!A:A; E$1 & "*"; Reservas!H:H; B{row_idx}; Reservas!K:K; "<>Cancelada") + '
            f'CONTAR.SI.CONJUNTO(Reservas!A:A; E$1 & "*"; Reservas!I:I; B{row_idx}; Reservas!K:K; "<>Cancelada"))'
        )
        
        ws.update_cell(row_idx, 2, formula_buscar)
        ws.update_cell(row_idx, 3, formula_contar)
        
    print("¡Pestaña 'Resumen cocina' configurada con éxito en Google Sheets!")

if __name__ == '__main__':
    setup()
