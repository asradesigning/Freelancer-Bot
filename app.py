from flask import Flask, render_template, redirect, request, jsonify, current_app
from __oauth__ import oauth_bp, get_user, get_projects_with_bids, get_customize_bid, set_pricing, get_bidding_status
from admin import admin_bp
from extensions import db, oauth  # Import from extensions
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user
from models import Users, Customize, Skills, Pricing, Bidding
from celery import Celery
from celery.contrib.abortable import AbortableTask
from bidding import *
from datetime import datetime, timezone
from time import sleep
app = Flask(__name__)
app.secret_key = "secret"
import json
login_manager = LoginManager()
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://doadmin:AVNS_sHCfxWNrQhG4sj_jF6Y@db-mysql-bot-do-user-18941393-0.d.db.ondigitalocean.com:25060/defaultdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['CELERY_RESULT_BACKEND'] = "redis://localhost:6379/0"
app.config['CELERY_BROKER_URL'] = "redis://localhost:6379/0"
oauth.init_app(app)
db.init_app(app)
login_manager.init_app(app)


celery = Celery('app', backend=app.config['CELERY_RESULT_BACKEND'], broker=app.config['CELERY_BROKER_URL'])

app.register_blueprint(oauth_bp)
app.register_blueprint(admin_bp)

@celery.task(bind=True, base=AbortableTask)
def bidding(self, user_id):
    print(user_id)
    with app.app_context():
               
        user = Users.query.filter_by(id=user_id).first()
        for i in range(86400):
            print(f"Searching Projects for {user.username}")
            projects = get_projects(user_id)
            sorted_projects = sorted(projects, key=lambda p: p.get('time_diff', float('inf')))
            for project in sorted_projects:
                time = project.get('time_diff')
                proj = project.get('project')
                bid = bid_on_project(user_id, proj) 
                if bid.status_code == 200:
                    break
            sleep(60)
            if self.is_aborted():
                return print(f"Bidding Stopped for {user.username}")
        return f"Bidding Completed for {user.username}"
    return


@app.route("/bidding", methods=["GET", "POST"])
def bidding_start():
    status = request.form["status"]
    bidding_status = Bidding.query.filter_by(user_id=current_user.id).first()
    if status == "bidding":
        bidding_status.is_bidding = "bidding"
        task = bidding.apply_async(args=[current_user.id])
        print(task.id)
        bidding_status.task = task
    elif status == "stopped":
        bidding_status.is_bidding = "stopped"
        task = bidding.AsyncResult(bidding_status.task)
        task.abort()
        bidding_status.task = ""
    db.session.add(bidding_status)
    db.session.commit()
    return redirect("/dashboard")

@app.route("/dashboard")
@login_required
def dashboard(): 
    # Fetch project details and bids from your function
    if(int(current_user.membership_time.timestamp()) < int(datetime.now(timezone.utc).timestamp())):
        bidding_status = Bidding.query.filter_by(user_id=current_user.id).first()
        bidding_status.is_bidding = "stopped"
        task = bidding.AsyncResult(bidding_status.task)
        task.abort()
        bidding_status.task = ""
        db.session.add(bidding_status)
        db.session.commit()
        return redirect('/logout')
    
    bidding_status = get_bidding_status(current_user.id)
    proposal = get_customize_bid(current_user.id)
    pricing = set_pricing(current_user.id)
    data = get_projects_with_bids()
    project_details = data.get('projects', {})  # Projects is a dictionary where keys are project IDs
    user_details = data.get('users', {})  # Projects is a dictionary where keys are project IDs
    Set_Skills(current_user.id)
    bids = data.get('bids', [])  # Bids is a list
    items_per_page = 10  # Maximum number of bids per page
    page = request.args.get('page', 1, type=int)  # Get current page from query parameters (default to 1)
    total_pages = (len(bids) + items_per_page - 1) // items_per_page  # Calculate total number of pages
    skills = Skills.query.filter_by(user_id=current_user.id).first()
    # Slice the bids list for the current page
    start = (page - 1) * items_per_page
    end = start + items_per_page
    paginated_bids = bids[start:end]
    
    # Pass data to the template
    return render_template(
        "/user/dashboard.html",
        user_details=get_user(),
        project_details=project_details.items(),
        bids=paginated_bids,  # Only the sliced bids for the current page
        owner=user_details.items(),
        current_page=page,
        total_pages=total_pages,
        proposal=proposal,
        skills=skills.skills,
        price=pricing,
        bidding=bidding_status
    )
    
@login_required
def Set_Skills(user_id):
    skills = Skills.query.filter_by(user_id=user_id).first()
    user_details = get_user()
    jobs = []

    if skills and skills.skills:
        # Skills exist, compare with jobs from user_details
        current_skills = {skill['id']: skill for skill in skills.skills}
        
        # Append the jobs from current skills
        for skill in skills.skills:
            jobs.append({
                "id": skill['id'],
                "name": skill['name'],
                "status": skill['status']
            })
            
        # Add new jobs from user_details that are not in current_skills
        for job in user_details.get('jobs', []):
            if job.get('id') not in current_skills:
                print(f"Adding skill: {job.get('name')}")
                jobs.append({
                    "id": job.get('id'),
                    "name": job.get('name'),
                    "status": "ON"
                })
                
        # Remove skills from the jobs list that are not in user_details jobs
        for skill in skills.skills:
            if not any(job['id'] == skill['id'] for job in user_details.get('jobs', [])):
                print(f"Removing skill: {skill['name']}")
                jobs = [job for job in jobs if job['id'] != skill['id']]

        
    else:
        # No skills available, so add all jobs from user_details
        for job in user_details.get('jobs', []):
            jobs.append({
                "id": job.get('id'),
                "name": job.get('name'),
                "status": "ON"
            })
        
        # Create new skills record if it doesn't exist
        skills = Skills(user_id=user_id, skills=jobs)

    # Update the skills list in the database
    skills.skills = jobs
    db.session.add(skills)
    db.session.commit()
    return
    
@app.route("/customize", methods=["GET", "POST"])
@login_required
def bid_customize():
    if 'customize' in request.form:
        client = request.form["client"]
        user = request.form["user"]
        sealed = request.form["sealed"]
        intro = request.form["intro"]
        links = request.form["all-links"]
        Client = client == "ON"
        User = user == "ON"
        Sealed = sealed == "ON"
        Links = [item.strip() for item in links.split(",") if item.strip()]
        
        customize = Customize.query.filter_by(user_id=current_user.id).first()
        if customize:
            customize.client = Client
            customize.user = User
            customize.sealed = Sealed
            customize.intro = intro
            customize.links = Links
        else:
            customize = Customize(client=Client, user=User, sealed=Sealed, intro=intro, links=Links, user_id=current_user.id)
            
        db.session.add(customize)
        db.session.commit()
        print(Client)
        print(User)
        print(Sealed)
        
        return redirect('/dashboard')
    else:
        return "No request made"
    
@app.route("/update_skills", methods=["GET", "POST"])
@login_required
def update_skills():
    skill_name = request.form["skill"] # Get the skill name
    status = request.form["status"]    # Get the status (ON/OFF)
    temp_skills = []
    skills_record = Skills.query.filter_by(user_id=current_user.id).first()
    for skill in skills_record.skills:
        print(skill["name"])
        if skill["name"] == skill_name:
            temp_skills.append({
                "id": skill["id"],
                "name": skill["name"],
                "status": status
            })
            print("changing status")
        else:
            temp_skills.append({
                "id": skill["id"],
                "name": skill["name"],
                "status": skill["status"]
            })
    skills_record.skills = temp_skills
    db.session.add(skills_record)
    db.session.commit()
    return redirect("/dashboard")

@app.route("/update-pricing", methods=["GET", "POST"])
@login_required
def update_pricing():
    pricing = Pricing.query.filter_by(user_id=current_user.id).first()
    if 'Fixed' in request.form:
        pricing.fixed = request.form['Fixed']
    elif 'Hourly' in request.form:
        pricing.hourly = request.form['Hourly']
    db.session.add(pricing)
    db.session.commit()
    return redirect("/dashboard")




@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Users, int(user_id)) 

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
    app.app_context().push()
