from bs4 import BeautifulSoup

def update_cv(cv_file_path, json_data):

    if 'name' in json_data and json_data['name']:
        update_cv_by_id(cv_file_path, json_data['name'], 'name')
        print(f"***INFO: Attributo name nel CV aggiornato con successo")
    
    if 'position' in json_data and json_data['position']:
        update_cv_by_id(cv_file_path, json_data['position'], 'position')
        print(f"***INFO: Attributo position nel CV aggiornato con successo")

    if 'contact' in json_data and json_data['contact']:
        contact_info = json_data['contact']
        for field, value in contact_info.items():
            if value:
                update_cv_by_id(cv_file_path, value, field)
        print(f"***INFO: Attributi contact nel CV aggiornati con successo")

    if 'about_me' in json_data and json_data['about_me']:
        update_cv_by_id(cv_file_path, json_data['about_me'], 'aboutMe')
        print(f"***INFO: Attributo about_me nel CV aggiornato con successo")

    if 'work_experience' in json_data and json_data['work_experience']:
        update_cv_experience(cv_file_path, json_data['work_experience'])
        print(f"***INFO: Aggiunte Esperienze nel CV con successo")

    if 'hard_skills' in json_data:
        update_cv_skills(cv_file_path, json_data['hard_skills'], 'hardSkill')
        print(f"***INFO: Hard Skills nel CV aggiornate con successo")

    if 'soft_skills' in json_data and json_data['soft_skills']:
        update_cv_skills(cv_file_path, json_data['soft_skills'], 'softSkill')
        print(f"***INFO: Soft Skills nel CV aggiornate con successo")

    if 'education' in json_data and json_data['education']:
        update_cv_education(cv_file_path, json_data['education'])
        print(f"Aggiunta Formazione nel CV con successo")
    
    if 'languages' in json_data and json_data['languages']:
        update_cv_languages(cv_file_path, json_data['languages'])
        print(f"***INFO: Aggiunte Lingue nel CV con successo")


def update_cv_by_id(cv_file_path, value, id_attr):
    # Leggi il contenuto del file HTML del CV
    with open(cv_file_path, 'r') as file:
        html_content = file.read()

    # Utilizza BeautifulSoup per analizzare il contenuto HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # Trova l'elemento con id="id_attr"
    name_element = soup.find(id=id_attr)

    # Verifica se l'elemento è stato trovato
    if name_element:
        # Modifica il testo dell'elemento con il nuovo value
        name_element.string = value

        # Sovrascrivi il file HTML con il contenuto aggiornato
        with open(cv_file_path, 'w') as file:
            file.write(str(soup))
    #else:
    #    print(f"ERROR: Attributo {id_attr} non trovato nel CV!")


def update_cv_experience(cv_file_path, experience_data):

    # Leggi il contenuto del file HTML del CV
    with open(cv_file_path, 'r') as file:
        html_content = file.read()

    # Utilizza BeautifulSoup per analizzare il contenuto HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    experience_section = soup.find('ul', id='workExperiences')
    if experience_section:
        # Remove all existing elements in the work experience section
        experience_section.clear()

        for i, job in enumerate(experience_data, start=1):
            # Create a new li element for each job experience
            new_job = soup.new_tag('li', id=f'job-{i}')

            # Create the internal structure of the new li element
            div_job_position = soup.new_tag('div', **{'class': 'jobPosition'})
            span_job_position = soup.new_tag('span', **{'class': 'bolded', 'id': f'jobPosition-{i}'})
            span_job_position.string = job.get('position', '')
            div_job_position.append(span_job_position)
            span_job_dates = soup.new_tag('span', id=f'jobDates-{i}')
            span_job_dates.string = job.get('dates', '')
            div_job_position.append(span_job_dates)
            new_job.append(div_job_position)

            div_project_name = soup.new_tag('div', **{'class': 'projectName bolded'})
            span_project_name = soup.new_tag('span', id=f'jobProjectCompany-{i}')
            span_project_name.string = job.get('project_company', '')
            div_project_name.append(span_project_name)
            new_job.append(div_project_name)

            div_small_text = soup.new_tag('div', **{'class': 'smallText'})
            p_job_description = soup.new_tag('p', id=f'jobDescription-{i}')
            p_job_description.string = job.get('description', '')
            div_small_text.append(p_job_description)

            ul_description_list = soup.new_tag('ul')
            description_list = job.get('description_list', [])
            for j, description in enumerate(description_list, start=1):
                li_description = soup.new_tag('li', id=f'jobDescription-{i}-list{j}')
                li_description.string = description
                ul_description_list.append(li_description)
            div_small_text.append(ul_description_list)

            p_skills = soup.new_tag('p')
            span_bolded_skills = soup.new_tag('span', **{'class': 'bolded'})
            span_bolded_skills.string = 'Skills: '
            p_skills.append(span_bolded_skills)
            span_job_skills = soup.new_tag('span', id=f'jobSkills-{i}')
            skills = ', '.join(job.get('skills', []))
            span_job_skills.string = skills
            p_skills.append(span_job_skills)
            div_small_text.append(p_skills)

            new_job.append(div_small_text)

            # Add the populated new element to the work experience section
            experience_section.append(new_job)
        
        with open(cv_file_path, 'w') as file:
            file.write(str(soup))

def update_cv_skills(cv_file_path, skill_data, skill_id):
    # Leggi il contenuto del file HTML del CV
    with open(cv_file_path, 'r') as file:
        html_content = file.read()

    # Utilizza BeautifulSoup per analizzare il contenuto HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the skills section in the HTML template
    skill_section = soup.find(id=skill_id)
    
    # Clear the current content of the skills section
    skill_section.clear()
    
    # Populate the skills section with the provided data
    for i, skill in enumerate(skill_data, start=1):
        # Create a new div for each skill
        skill_div = soup.new_tag('div', attrs={'class': 'skill', 'id': f'{skill_id}-{i}'})
        
        # Create the span for the skill
        skill_span = soup.new_tag('span')
        skill_span.string = skill
        skill_div.append(skill_span)
        
        # Add the populated skill div to the skills section
        skill_section.append(skill_div)
    
    with open(cv_file_path, 'w') as file:
        file.write(str(soup))

def update_cv_languages(cv_file_path, language_data):
    # Leggi il contenuto del file HTML del CV
    with open(cv_file_path, 'r') as file:
        html_content = file.read()

    # Utilizza BeautifulSoup per analizzare il contenuto HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the language section in the HTML template
    language_section = soup.find(id='languagesList')
    
    # Clear the current content of the language section
    language_section.clear()
    
    # Populate the language section with the provided data
    for i, language in enumerate(language_data, start=1):
        # Create a new div for each language
        language_div = soup.new_tag('div', attrs={'class': 'skill', 'id': f'language-{i}'})
        
        # Create the div for the language name
        name_div = soup.new_tag('div')
        name_span = soup.new_tag('span', id=f'lang-{i}')
        name_span.string = language['name']
        name_div.append(name_span)
        language_div.append(name_div)
        
        # Create the div for the language level
        level_div = soup.new_tag('div', attrs={'class': 'yearsOfExperience'})
        level_span = soup.new_tag('span', id=f'langLevel-{i}', attrs={'class': 'alignright'})
        level_span.string = language['level']
        level_div.append(level_span)
        language_div.append(level_div)
        
        # Add the populated language div to the language section
        language_section.append(language_div)
    
    with open(cv_file_path, 'w') as file:
        file.write(str(soup))

def update_cv_education(cv_file_path, education_data):
    # Leggi il contenuto del file HTML del CV
    with open(cv_file_path, 'r') as file:
        html_content = file.read()

    # Utilizza BeautifulSoup per analizzare il contenuto HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the div with id "educationSection"
    education_section = soup.find('div', id='educationSection')
    if education_section:
        # Remove all existing elements in the education section
        education_section.clear()

        # For each education entry in the education_data list
        for i, education_entry in enumerate(education_data, start=1):
            # Create a new div element for the education entry
            new_education = soup.new_tag('div', **{'class': 'smallText', 'id': f'education-{i}'})

            # Create and populate HTML tags with education details
            p_title = soup.new_tag('p', **{'class': 'bolded white', 'id': 'eduTitle'})
            p_title.string = education_entry.get('title', '')
            new_education.append(p_title)

            p_institute = soup.new_tag('p', id='eduInstitute')
            p_institute.string = education_entry.get('institute', '')
            new_education.append(p_institute)

            p_dates = soup.new_tag('p', id='eduYears')
            p_dates.string = education_entry.get('dates', '')
            new_education.append(p_dates)

            # Add the new education element to the "educationSection" in the HTML template
            education_section.append(new_education)
    
    with open(cv_file_path, 'w') as file:
        file.write(str(soup))