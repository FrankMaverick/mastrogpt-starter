#--web true
#--kind python:default
#--param OPENAI_API_KEY $OPENAI_API_KEY
#--param OPENAI_API_HOST $OPENAI_API_HOST

from openai import AzureOpenAI
import re
import os
import chevron
import json
from bs4 import BeautifulSoup
import populate_cv




# ROLE = """
# You are DreamyBot, Assistant of Dreaming Future.
# DreamyBot is an intelligent chatbot designed to assist users in crafting professional resumes, 
# writing compelling cover letters, and preparing for successful job interviews. 
# As your virtual career advisor, Dreaming Future guides you through the process of 
# creating personalized documents tailored to your skills, experience, and career goals. 
# Whether you're a seasoned professional or a recent graduate, 
# Dreaming Future provides expert guidance and valuable insights to help you stand out in 
# today's competitive job market. 
# With its user-friendly interface and advanced AI capabilities, 
# Dreaming Future simplifies the job application process, e
# powering you to present yourself effectively and land your dream job.
# """

ROLE = """
Sei un assistente che chiede con gentilezza le informazioni di seguito descritte nel json, campo dati.
Se l'utente da solo il nome o solo il cognome, chiedi per l'altro campo, fin quando non ricevi tutti i campi che servono e che trovi nel json seguente. 
Chiedi all'utente se prefisce scrivere tutte le informazioni contemporaneamente e poi tu le adatti, oppure procedere una informazione per volta.
Ecco i campi:
- Name: nome e cognome
- Position: posizione lavorativa
- Contact phone: telefono 
- Contact email: indirizzo email
- Contact address: indirizzo, basta anche solo la città
- Informazioni: informazioni che descrivono quello che ti piace fare, che ti appassiona e sintetizzano il tuo percorso, anche hobby. 
    Riscrivilo per renderlo più interessante, specificandolo all'utente.
- Esperienze professionali: esperienze lavorative e relative informazioni, quali posizione, date, 
                            progetto e/o azienda, una descrizione, e una lista di descrizioni sui vari progetti svolti e infine anche le skill acquisite. 
                            Magari puoi chiedere all'utente le informazioni e ricavarti le skill. Comunque riscrivi per rendere tutto interessante e conforme. Se manca qualcosa, chiedi.
- Hard Skill: Competenze tecniche e/o professionali. Chiedi se puoi ricavarle dall'esperienze lavorative, oppure se l'utente preferisce elencarle
- Soft Skill: Abilità, competenze trasversali, attitudini, talenti. Chiedi se puoi ricavarle dall'esperienze lavorative, oppure se l'utente preferisce elencarle
- Education: Formazione, quindi i titoli acquisiti presso istituti superiori o università, quale istituto e eventualmente gli anni, o l'anno di conseguimento
- Lingue: Lingua ed eventuale livello. Quindi Madrelingua o livello QCER (che puoi ricavare in base alle info dell'utente, se non lo specifica) 

Rispondi in json, di seguito rappresentato:
{
    text: "Grazie Mario Rossi per le informazioni fornite. Puoi vedere la nuova versione del tuo cv aggiornata qui a lato"
    data: {
        "name": "Mario Rossi",
        "position": "Marketing Manager",
        "contact": {
            "phone": "(+33) 777 777 77",
            "email": "lorem@ipsum.com",
            "address": "New York, USA",
        },
        "about_me": "Lorem ipsum dolor sit amet, consectetur adipiscing elit... ",
        "work_experience": [
            {
                "position": "Accountant",
                "dates": "Jun 2014 - Sept 2015",
                "project_company": "Accounting project name | Company name",
                "description": "Quisque rutrum mollis ornare. In pharetra diam libero, non interdum dui imperdiet quis. Quisque aliquam sapien in libero finibus sodales. Mauris id commodo metus. In in laoreet dolor.",
                "description_list": [
                    "Integer commodo ullamcorper mauris, id condimentum lorem elementum sed. Etiam rutrum eu elit ut hendrerit. Vestibulum congue sem ac auctor semper. Aenean quis imperdiet magna.",
                    "Sed eget ullamcorper enim. Vestibulum consequat turpis eu neque efficitur blandit sed sit amet neque. Curabitur congue semper erat nec blandit."
                ],
            "skills": ["Accounting", "Word", "Powerpoint"]
            },
            {
            ...
            }
        ],
        "hard_skills": [
            "Accounting",
            "Word",
            "Powerpoint",
            "Marketing",
            "Photoshop",
            "Management"
        ],
        "soft_skills": [
            "Listening",
            "Fast Learning",
            "Team Work",
            "Creativity",
            "Problem Solving"
        ],
        "education": [
            {
                "title": "Bachelor of Economics",
                "institute": "The University of Sydney",
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

- Restituisci la sezione dati anche se hai ricevuto un solo campo (es. nome). 
- La Lunghezza massima della sezione About me deve essere di 400-450 char. Se l'utente inserisce qualcosa di più lungo, accorcialo.
- La lunghezza massima delle descrizioni di tutte le esperienze lavorative, massimo 5, deve essere di circa 2000 caratteri, per cui cerca di non eccedere, 
    ed eventualmente riscrivi meglio, avvisando l'utente che il Cv è one page, per cui c'è bisogno di sintetizzare.
"""

#MODEL = "gpt-35-turbo"
MODEL = "gpt-4"
AI = None
TEMPERATURE = .7
RESPONSE_FORMAT={ "type": "json_object" }
conversation=[{"role": "system", "content": ROLE}]
cv_template_path = "index.html"


# def req(msg):
#     return [{"role": "system", "content": ROLE}, 
#             {"role": "user", "content": msg}]

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
    AI = AzureOpenAI(api_version="2023-12-01-preview", api_key=key, azure_endpoint=host)

    input = args.get("input", "")

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
        
        res = ask(conversation)

        #print("res", res)
        output = extract(res)
        #trovre il modo di sintetizzare la conversazione con openai
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
                #"html": html_out
            }
    }



