from flask import Flask
import requests
from models import Skills, Pricing, Customize, Users
from datetime import datetime, timezone
from __oauth__ import get_user
from openai import OpenAI

deepSkeek = OpenAI(api_key="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")

def get_projects(user_id):
    headers = {"Freelancer-OAuth-V1": "87sdtSoZ9s6foqbQcO5jcE9EiICnCT"}
    freelancer_api_host = "https://www.freelancer.com/api"
    api_url = f"{freelancer_api_host}/projects/0.1/projects/active/"
    skills = Skills.query.filter_by(user_id=user_id).first()
    jobs = []
    query = ""
    for skill in skills.skills:
        if skill['status'] == "ON":
            jobs.append({
                skill['id']
            })
            query = query + skill['name'] + ", "

    
    params = {
        "jobs[]": jobs,
        "full_description": True,
        "query": query,
        'job_details': True,
        "limit": 100
    }
    res = requests.get(api_url, headers=headers, params=params, verify=False)
    if res.status_code == 200:
        current_projects = []
        projects = res.json().get("result").get('projects')
        for project in projects:
            project_time = project.get('time_submitted')
            time_diff = get_current_time() - project_time
            if time_diff < 600:
                current_projects.append({
                    "time_diff": time_diff,
                    "project": project
                })
        return current_projects
    return None

def bid_on_project(user_id, project):
    headers = {"Freelancer-OAuth-V1": "87sdtSoZ9s6foqbQcO5jcE9EiICnCT"}
    freelancer_api_host = "https://www.freelancer.com/api"
    api_url = f"{freelancer_api_host}/projects/0.1/bids/"
    project_id = project.get('id')
    bidder_id = get_user().get('id')
    bid_amout = get_bid_amount(user_id, project.get('type'), project.get('budget').get('minium'), project.get('budget').get('maximum'))
    period = 3
    milestone = 100
    description = get_proposal(user_id, project)
    
    bid_data = {
    "project_id": project_id,  # Replace with the actual project ID
    "bidder_id": bidder_id,   # Replace with the actual bidder ID
    "amount": bid_amout,    # Your bid amount
    "period": period,      # Delivery period (in days)
    "milestone_percentage": milestone,  # Milestone percentage
    "description": description,  # Your bid proposal
}
    
    response = requests.post(api_url, headers=headers, json=bid_data)

    return response
    
def get_bid_amount(user_id, type, min, max):
    pricing = Pricing.query.filter_by(user_id=user_id).first()
    price = min
    if type == 'fixed':
        if pricing.fixed == 'lowest':
            price = min
        elif pricing.fixed == 'highest':
            price = max
        elif pricing.fixed == 'mid':
            price = (max - min) / 2 + min
    elif type == 'hourly':
        if pricing.hourly == 'lowest':
            price = min
        elif pricing.hourly == 'highest':
            price = max
        elif pricing.hourly == 'mid':
            price = (max - min) / 2 + min
    return price

def get_proposal(user_id, project):
    proposal = Customize.query.filter_by(user_id=user_id).first()
    use_client_name = proposal.client
    use_user_name = proposal.user
    intro = proposal.intro
    links = proposal.links
    project_title = project.get('title')
    client_name = ""
    user_name = ""
    user = get_user()
    if use_client_name == True:
        client_name = get_client(project.get('owner_id'))
    if use_user_name == True:
        user_name = f"{user.get('first_name')} {user.get('last_name')}"
        
    Jobs = ""
    for job in project.get('jobs'):
        Jobs = f"{Jobs} + {job.get('name')}, "
    
    portfolio_links = ""
    for link in links:
        portfolio_links = f"{portfolio_links} + {link}, "
        
    generate_proposal = proposal_request(project.get('description'), Jobs, intro, portfolio_links, client_name, user_name)
    return generate_proposal
        
    
def get_client(client_id):
    headers = {"Freelancer-OAuth-V1": "87sdtSoZ9s6foqbQcO5jcE9EiICnCT"}
    freelancer_api_host = "https://www.freelancer.com/api"
    api_url = f"{freelancer_api_host}/users/0.1/users/{client_id}/"
    res = requests.get(api_url, headers=headers, verify=False)
    if res.status_code == 200:
        client_name = res.json().get("result").get('public_name')
        return client_name
    else:
        return False

def get_current_time():
    current_time = datetime.now(timezone.utc)
    current_time = int(current_time.timestamp())
    return current_time


def proposal_request(project_description, skills, intro="", links="", client_name="", user_name=""):
    # # Base prompt
    # prompt = f"""
    # Write a professional proposal for a project with the following details:
    # - **Project Description:** {project_description}
    # - **Required Skills:** {skills}
    # """
    
    # # Add intro to the prompt if it is provided
    # if intro:
    #     prompt += f"""
    # - **Example Introduction About Me:** {intro}
    # """
    
    # # Add client name if provided
    # if client_name:
    #     prompt += f"""
    # - **Client Name:** {client_name}
    # """
    
    # # Add user name if provided
    # if user_name:
    #     prompt += f"""
    # - **My Name:** {user_name}
    # """
    
    # # Add portfolio links if provided
    # if links:
    #     # Split links into a list (assuming links are separated by commas)
    #     links_list = links.split(", ")
    #     # Format links as one per line
    #     formatted_links = "\n".join(links_list)
    #     prompt += f"""
    # - **My Portfolio:**
    # {formatted_links}
    # Use the portfolio links if necessary, depending on the project requirements.
    # """
    
    # # Final instructions
    # prompt += """
    # Make the proposal concise, professional, and convincing. Ensure the proposal is no longer than 1200 characters.
    # """
    
    # # Call the DeepSeek API to generate the proposal
    # response = deepSkeek.chat.completions.create(
    #     model="gpt-4o-mini",
    #     messages=[
    #         {"role": "system", "content": "You are a professional freelancer."},
    #         {"role": "user", "content": prompt},
    #     ],
    #     stream=False
    # )
    
    # # Extract the generated proposal
    # proposal = response.choices[0].message.content
    
    # # Print the proposal (optional, for debugging or logging)
    # print(proposal)
    links_list = links.split(", ")
    formatted_links = "\n".join(links_list)
    
    proposal = f"""Hi {client_name}

    My name is {user_name}. {intro}
    
    With over 3 years of professional experience in web development,
    I possess a well-rounded skill set in both front-end and back-end technologies.
    On the front end, I specialize in crafting responsive, intuitive, and visually appealing user interfaces using HTML, CSS, and JavaScript,
    along with frameworks like React, Vue.js, Next Js and Bootstrap. My back-end expertise includes working with Node.js, PHP, and Python to develop
    robust and scalable server-side applications, complemented by hands-on experience in managing databases such as MySQL, MongoDB, and PostgreSQL.
    
    My Portfolio:
    {formatted_links}
    
    I am confident in delivering a project that not only meets but exceeds your expectations. I look forward to the opportunity to collaborate with you on this project.
    
    Best regards,
    {user_name}
    """
    
    # Return the generated proposal
    return proposal