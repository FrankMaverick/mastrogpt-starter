#--web true
#--kind python:default
#--param OPENAI_API_KEY $OPENAI_API_KEY
#--param OPENAI_API_HOST $OPENAI_API_HOST
#--timeout 600000

from openai import AzureOpenAI
import chevron
import json
import populate_cv
import time

ROLE = """
Sei un assistente che chiede con gentilezza le informazioni di seguito descritte nel json, campo dati.
Se l'utente da solo il nome o solo il cognome, chiedi per l'altro campo, fin quando non ricevi tutti i campi che servono e che trovi nel json seguente. 
Ecco i campi:
- Name: nome e cognome.
- Position: posizione lavorativa.
- Contact phone, email e address: telefono, indirizzo email e indirizzo, basta anche solo la città.
- Informazioni: informazioni che descrivono quello che ti piace fare, che ti appassiona e sintetizzano il tuo percorso. 
- Esperienze professionali: esperienze lavorative e relative informazioni, quali posizione, date, progetto e/o azienda, una descrizione, e una lista di descrizioni sui vari progetti svolti e infine anche le skill acquisite.
- Hard Skill: Competenze tecniche e/o professionali. Ricavale dall'esperienze lavorative, oppure se chiedi l'utente preferisce elencarle.
- Soft Skill: Abilità, competenze trasversali, attitudini, talenti. Ricavale dall'esperienze lavorative, oppure chiedi se l'utente preferisce elencarle.
- Education: Formazione, titoli di studio acquisiti presso istituti superiori o università, istituto e anno di conseguimento.
- Lingue: Lingua ed eventuale livello QCER.

ESEMPIO:
Rispondi in json, strutturato come l'esempio di seguito:
{
    text: "Grazie Mario Rossi per le informazioni fornite. Puoi vedere la nuova versione del tuo cv aggiornata qui a lato"
    data: {
        "name": "Mario Rossi",
        "position": "Marketing Manager",
        "contact": {
            "phone": "+33 333 3333333",
            "email": "lorem@ipsum.com",
            "address": "New York, USA",
        },
        "about_me": "informazioni... ",
        "work_experience": [
            {
                "position": "Accountant",
                "dates": "Gen 2014 - Ott 2015",
                "project_company": "Progetto | Azienda",
                "description": "descrizione sulla posizione lavorativa",
                "description_list": [
                    "descrizione di un compito",
                    "descrizione di un secondo compito",
                    "..."
                ],
            "skills": ["competenza acquisita 1", "competenza acquisita 2", ...]
            },
            {
            ...
            }
        ],
        "hard_skills": [
            "Programmazione",
            "Word",
            "Powerpoint",
            "Marketing",
            "Photoshop",
            "Management"
        ],
        "soft_skills": [
            "Ascolto",
            "Apprendimento veloce",
            "Lavoro di Squadra",
            "Creatività",
            "Problem Solving"
        ],
        "education": [
            {
                "title": "Laurea in Economia",
                "institute": "Università Bocconi di Milano",
                "dates": "2010 - 2014"
            }
        ],
        "languages": [
            {
                "name": "Italiano",
                "level": "Madrelingua"
            },
            {
                "name": "Inglese",
                "level": "B2"
            }
    }
}

REGOLE:
- Appena ricevi il primo campo della sezione dati (nome cognome), restituiscilo nella sezione dati. Fai lo stesso per ogni info ricevuta.
- Nella sezione dati non aggiungere campi vuoti.
- Restituisci solo gli oggetti inseriti dall'utente nella sezione dati, non tutti i campi forniti precedentemente.
- Riscrivi la sezione informazioni rendendola interessante e usando massimo 120 parole. 
- Riscrivi tutte le esperienze rendendole interessanti e usando massimo 500 parole per tutte.
- Le esperienze lavorative dividele quando possibile, se si tratta di diverse company o diverse posizioni. 
- Non inserire troppe esperienze lavorative, massimo 7.
- Ordina le esperienze lavorative dalla più recente alla meno recente.
- Ricava le skill dalle esperienze lavorative, sia le skills per ogni esperienza, ma anche le hard skills che le soft skills.
- Aggiungi massimo 8-10 hard skills e massimo 5 soft skill
"""

#MODEL = "gpt-35-turbo"
MODEL = "gpt-4"
AI = None
TEMPERATURE = .4
RESPONSE_FORMAT={ "type": "json_object" }
conversation=[{"role": "system", "content": ROLE}]
cv_template_path = "index.html"
role_path = "role.txt"


def ask(input):
    comp = AI.chat.completions.create(model=MODEL, 
                                    response_format=RESPONSE_FORMAT,
                                    messages=input, 
                                    temperature=TEMPERATURE)
    if len(comp.choices) > 0:
        content = comp.choices[0].message.content
        return content
    return "ERROR"


def extract(text):

    print("***RESPONSE:", text)

    json_object = json.loads(text)

    text = json_object.get("text", "")

    if 'data' in json_object:
        data = json_object['data']

        return {
            "text": text,
            "data": data
        }
    
    else:
        
        return {
            "text": text,
            "data": {}
        }


def render(src, args):
    with open(src) as f:
        return chevron.render(f, args)

def main(args):
    global AI
    (key, host) = (args["OPENAI_API_KEY"], args["OPENAI_API_HOST"])
    AI = AzureOpenAI(api_version="2024-02-15-preview", api_key=key, azure_endpoint=host)

    input = args.get("input", "")

    print('input', input)

    html_out = render(cv_template_path, args)

    if  input == "":
        return { 
            "body": {
                "output": "Ciao! Benvenuto su <b>SmartCV AI</b>. Sono qui per aiutarti a compilare il tuo cv che vedi qui a lato.<br> Per questo mi servono alcune informazioni, sei pronto?",
                "title": "SmartCV AI Chat",
                #"message": "You can chat with me to create your CV" #, cover letter or prepare for an interview"
                "html": html_out
            } 
        } 

    else:
        
        conversation.append({"role": "user", "content": input})
        print("***conversation", conversation)
        
        start = time.time()
        
        res = ask(conversation)

        end = time.time()
        print("***RESPONSE TIME:", end - start)

        output = extract(res)

        print("***OUTPUT", output)

        conversation.append({"role": "assistant", "content": res})

        if output["data"]:
            #Update CV
            print("***UPDATE CV***")
            populate_cv.update_cv(cv_template_path, output["data"])
            html_out = render(cv_template_path, args)
            return {
                "body": {
                    "output":output["text"],
                    "html": html_out
                }
            }

        return {
            "body": {
                "output":output["text"],
            }
    }



