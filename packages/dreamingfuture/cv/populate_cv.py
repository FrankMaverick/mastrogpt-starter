import json
from bs4 import BeautifulSoup

def update_cv(cv_file_path, json_data):

    if 'name' in json_data:
        update_cv_by_id(cv_file_path, json_data['name'], 'name')
    
    if 'position' in json_data:
        update_cv_by_id(cv_file_path, json_data['position'], 'position')

    if 'contact' in json_data:
        contact_info = json_data['contact']
        for field, value in contact_info.items():
            update_cv_by_id(cv_file_path, value, field)


def update_cv_by_id(cv_file_path, value, id_attr):
    # Leggi il contenuto del file HTML del CV
    with open(cv_file_path, 'r') as file:
        html_content = file.read()

    # Utilizza BeautifulSoup per analizzare il contenuto HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # Trova l'elemento <h1> con id="name"
    name_element = soup.find(id=id_attr)

    # Verifica se l'elemento è stato trovato
    if name_element:
        # Modifica il testo dell'elemento con il nuovo nome
        name_element.string = value

        # Sovrascrivi il file HTML con il contenuto aggiornato
        with open(cv_file_path, 'w') as file:
            file.write(str(soup))
        print(f"{id_attr} nel CV aggiornato con successo a: {value}")
    else:
        print(f"ERROR: Attributo {id_attr} non trovato nel CV!")