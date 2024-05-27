#--web true
#--kind python:default
#--param OPENAI_API_KEY $OPENAI_API_KEY
#--param OPENAI_API_HOST $OPENAI_API_HOST
#--param MONGODB_URL $MONGODB_URL
#--timeout 600000

from openai import AzureOpenAI
import chevron
import json
import random
import string
import populate_cv
import time
from pymongo import MongoClient


ASSISTANT_ROLE = """
Sei un assistente che chiede in italiano e con cortesia le informazioni di seguito descritte nel json di seguito riportato, oggetto "data".
COSA FONDAMENTALE IMPORTANTISSIMA: Le informazioni fornite dall'utente inseriscile SEMPRE nel campo data del json.

Chiedi all'utente le seguenti informazioni utili per compilare il suo CV, quali:
- nome e cognome (name)
- posizione lavorativa (position)
- Contatti: Numero di telefono (contact[phone]) + indirizzo email (contact[email]) + indirizzo, basta anche solo la città (contact[address])
- informazioni (about_me) che descrivono quello che ti piace fare, che ti appassiona e sintetizzano il tuo percorso, anche hobby.
- Esperienze professionali (work_experience): esperienze lavorative e relative informazioni, quali posizione, date, 
                            progetto e/o azienda, una descrizione, e una lista di descrizioni sui vari progetti svolti ed eventualmente anche le skill acquisite. 
- Competenze tecniche e/o professionali (hard_skills): Chiedi se puoi ricavarle dall'esperienze lavorative, oppure se l'utente preferisce elencarle
- Abilità, competenze trasversali, attitudini, talenti (soft_skills): Chiedi se puoi ricavarle dall'esperienze lavorative, oppure se l'utente preferisce elencarle
- Formazione, quindi i titoli di studio acquisiti presso istituti superiori o università, quale istituto e eventualmente gli anni, o l'anno di conseguimento (education)
- Lingue ed eventuale livello (languages), quindi Madrelingua o livello QCER (che puoi ricavare in base alle info dell'utente, se non lo specifica) 


- Ad ogni informazione fornita, continua a chiedere le altre info. Puoi anche dire all'utente che il cv è aggiornato e può vederlo a lato.
"""


FORMAT_ROLE = """
Il tuo compito è formattare in json il testo che ricevi, senza inventare nulla.
Anche se è una domanda, non devi rispondere, ma devi riportare la domanda.
Il testo in ingresso contiene una parte testuale, in cui ci sono alcune informazioni relative ad un cv, quali:
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
- Education: Formazione, quindi i titoli di studio acquisiti presso istituti superiori o università, quale istituto e eventualmente gli anni, o l'anno di conseguimento
- Lingue: Lingua ed eventuale livello. Quindi Madrelingua o livello QCER (che puoi ricavare in base alle info dell'utente, se non lo specifica) 


Formatta la risposta e rispondi in json, come di seguito rappresentato, quindi con il campo 'text' corrispondente al messaggio dell'ASSISTANT e il campo 'data' con le varie informazioni che ricevi:
{
    text: "Grazie Nome e Cognome per le informazioni fornite..."
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

IMPORTANTE: popola i valori dell'oggetto 'data' del json solo quando sono presenti i relativi dati. 
Ad esempio, se l'utente non ha ancora fornitora la 'position', allora questo oggetto sarò vuoto.
Il campo text invece ce l'hai sempre, quindi devi sempre popolarlo con quello che ricevi in ingresso.
Non popolare tutto il json, ma solo le informazioni che ricevi nel campo text
"""

#MODEL = "gpt-35-turbo"
ASSISTANT_MODEL = "gpt-35-turbo"
FORMAT_MODEL = "gpt-4"
AI = None
TEMPERATURE = .3
RESPONSE_FORMAT={ "type": "json_object" }
conversation=[{"role": "system", "content": ASSISTANT_ROLE}]
cv_template_path = "index.html"
global user_id
global thread_id
global assistant


#MONGO_DB
clientMongo = MongoClient('mongodb://fcardinale_ferretdb:iBCXJWYdht7X@nuvolaris-mongodb-0.nuvolaris-mongodb-svc.nuvolaris.svc.cluster.local:27017/fcardinale_ferretdb?connectTimeoutMS=60000&authMechanism=PLAIN')  #'MONGODB_URL' is not defined",
db = clientMongo['dbname'] 
collection = db['threads']  


def set_thread_id(user_id, thread_id):
    """
    Salva l'ID del thread in MongoDB associandolo a un user_id.
    """
    collection.update_one(
        {"user_id": user_id},  # Chiave per identificare l'utente
        {"$set": {"thread_id": thread_id}},  # ID del thread da salvare
        upsert=True  # Se non esiste un documento con questo user_id, crealo
    )

def get_thread_id(user_id):
    """
    Recupera l'ID del thread da MongoDB usando un user_id.
    """
    documento = collection.find_one({"user_id": user_id})
    if documento:
        return documento.get("thread_id")
    else:
        return None 
    

def wait_on_run(run, thread_id):
    while run.status == "queued" or run.status == "in_progress":
        run = AI.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id,
        )
        print(f"Run status: {run.status}")
        time.sleep(10)
    return run

def req(msg):
    return [{"role": "system", "content": FORMAT_ROLE}, 
            {"role": "user", "content": msg}]

def ask(input):
    comp = AI.chat.completions.create(model=FORMAT_MODEL, 
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
    global user_id
    global assistant
    global AI
    (key, host) = (args["OPENAI_API_KEY"], args["OPENAI_API_HOST"])
    AI = AzureOpenAI(api_version="2024-02-15-preview", api_key=key, azure_endpoint=host)

    #clean collection in mongodb
    #collection.drop()

    input = args.get("input", "")

    html_out = render(cv_template_path, args)

    if  input == "":

        #create random user_id
        user_id = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        print("user_id", user_id)

        return { 
            "body": {
            "output": "Ciao! Benvenuto su <b>SmartCV AI</b>. Sono qui per aiutarti a compilare il tuo cv che vedi qui a lato.<br> Per questo mi servono alcune informazioni, sei pronto?",
            "title": "SmartCV AI Chat",
            "html": html_out
            } 
        } 
    

    else:
        print("SEARCH ID IN MONGODB")
        thread_id = get_thread_id(user_id)

        if thread_id is None:
            #First interaction with Assistant, so create it
            print("THERE IS NO THREAD, CREATE IT")

            # Create and configure the assistant
            assistant = AI.beta.assistants.create(
                name="CV Assistant",
                instructions=ASSISTANT_ROLE,
                model=ASSISTANT_MODEL,
            )

            # Create a thread where the conversation will happen
            thread = AI.beta.threads.create()
            print("THREAD CREATED:", thread)
            set_thread_id(user_id, thread.id)
            print("THREAD SAVED IN DB")

            message = AI.beta.threads.messages.create(
                thread.id,
                role="user",
                content=input,
            )
            print(message)


            # Create the Run, passing in the thread and the assistant
            run = AI.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant.id
            )
            print("run:",run)

            # Wait for completion of run
            run = wait_on_run(run, thread.id)
                
            # Retrieve messages added by the Assistant to the thread
            all_messages = AI.beta.threads.messages.list(
                thread_id=thread.id
            )

            user_msg = message.content[0].text.value
            ass_msg = all_messages.data[0].content[0].text.value

            print("###################################################### \n")
            print(f"USER: {user_msg}")
            print(f"ASSISTANT: {ass_msg}")

            #Format in json with chat.completion ?
            print("Format in json")
            formatted_output = ask(req("INPUT:"+input+"\n"+"ASSISTANT:"+(ass_msg)))
            print("formatted_output", formatted_output)

            output = extract(formatted_output)

            return {
                "body": {
                    "output":output["text"],
                    "html": html_out
                }
            }

        #subsequent interactions
        else: 
            print("THERE IS THREAD IN DB", thread_id)

            message = AI.beta.threads.messages.create(
                thread_id,
                role="user",
                content=input,
            )
            print(message)

            print("CREATE RUN")
            # Create the Run, passing in the thread and the assistant
            run = AI.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant.id
            )

            start = time.time()
            # Wait for completion of run
            run = wait_on_run(run, thread_id)
            
            end = time.time()
            print("***ASSISTANT RESPONSE TIME:", end - start)

            # Retrieve messages added by the Assistant to the thread
            all_messages = AI.beta.threads.messages.list(
                thread_id=thread_id
            )

            print("RETRIEVED MESSAGE")

            print("###################################################### \n")
            print(f"USER: {message.content[0].text.value}")
            print(f"ASSISTANT: {all_messages.data[0].content[0].text.value}")
            
            start = time.time()
            #Format in json with chat.completion
            #formatted_output = ask(req(all_messages.data[0].content[0].text.value))
            formatted_output = ask(req("INPUT:"+input+"\n"+"ASSISTANT:"+all_messages.data[0].content[0].text.value))
            print("formatted_output", formatted_output)

            end = time.time()
            print("***CHAT COMPLETION RESPONSE TIME:", end - start)

            output = extract(formatted_output)

            if output["data"]:
                #Update CV
                print("***UPDATE CV***")
                populate_cv.update_cv(cv_template_path, output["data"])
                print("***RENDER CV***")
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
                    "html": html_out
                }
            }

