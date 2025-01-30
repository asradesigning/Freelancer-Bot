import flask
from flask import (
    url_for,
    session,
    request,
    jsonify,
    redirect,
    render_template,
    Blueprint,
)
import flask_login
from flask_login import current_user, login_user, logout_user, login_required
from extensions import oauth, db  # Import from extensions
from models import CreateAccountForm, LoginForm, Users, Customize, Pricing, Bidding
from api_config import CONFIG
import requests
from util import verify_pass
from urllib.parse import urlencode
from datetime import datetime, timezone

oauth_bp = Blueprint("oauthBP", __name__, template_folder="templates")

OAUTH_BASE_URL = "{server_base_url}/oauth".format(**CONFIG)
API_BASE_URL = "{server_base_url}/api/v1".format(**CONFIG)

remote = oauth.register(
    name="freelancer",
    client_id=CONFIG["client_id"],
    client_secret=CONFIG["client_secret"],
    api_base_url=CONFIG["server_base_url"],
    access_token_url="{}/token".format(OAUTH_BASE_URL),
    authorize_url="{}/authorise".format(OAUTH_BASE_URL),
)

@oauth_bp.route("/")
def route_default():
    return redirect(url_for('oauthBP.login'))

@oauth_bp.route("/login", methods=["GET", "POST"])
def login():
    login_form = LoginForm(request.form)
    if 'login' in request.form:
        username = request.form['username']
        password = request.form['password']

        # Locate user
        user = Users.query.filter_by(username=username).first()

        # Check the password
        if user and verify_pass(password, user.password):
            if int(user.membership_time.timestamp()) > int(datetime.now(timezone.utc).timestamp()):
                session["user_id"] = user.user_id
                refresh_token()
                login_user(user)
                return redirect(url_for('oauthBP.route_default'))
            return render_template('user/login.html',
                    msg='Membership',
                    form=login_form)

        # Something (user or pass) is not ok
        return render_template('user/login.html',
                               msg='Incorrect',
                               form=login_form)

    if not current_user.is_authenticated:
        return render_template('user/login.html',
                               form=login_form)
    return redirect('/dashboard')

@oauth_bp.route("/register-freelancer", methods=["GET", "POST"])
def register_freelancer():
    if request.method == "GET":
        client_info = {"client_name": CONFIG["client_name"]}
        return render_template(
            "/user/register_freelancer.html", error=request.args.get("error"), **client_info
        )
    prompt = "select_account"
    advanced_scopes = "1 6"
    return remote.authorize_redirect(
        callback=CONFIG["client_redirect"],
        prompt=prompt,
        advanced_scopes=advanced_scopes,
        scope="basic",
    )

@oauth_bp.route("/authorized")
def authorized():
    if request.args.get("error"):
        return f"Error occurred: {request.args.get('error')}"

    resp = remote.authorize_access_token()
    if resp is None:
        return f"Access denied: reason={request.args.get('error_reason')} error={request.args.get('error_description')}"

    session["access_token"] = (resp["access_token"],)
    session["refresh_token"] = (resp["refresh_token"],)
    print(resp["expires_in"])
    print(resp["token_type"])
    freelancer_user_info = get_freelancer_user_info()
    if freelancer_user_info:
        user = Users.query.filter_by(user_id=freelancer_user_info.get('id')).first()
        if user:
            flask_login.login_user(user)
            user.access_token = session["access_token"]
            user.refresh_token = session["refresh_token"]
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('oauthBP.login'))
        session["user_id"] = freelancer_user_info.get('id')
        session["username"] = freelancer_user_info.get('username')
        return redirect(url_for("oauthBP.register"))
    else:
        return redirect(url_for("login"))
    
@oauth_bp.route('/register', methods=["GET", "POST"])
def register():
    
    
    register_form = CreateAccountForm(request.form)
    if 'register' in request.form:
        print('submitting form')
        email = request.form['email']
        passw = request.form['password']
        user = Users.query.filter_by(email=email).first()
        if user:
            return render_template('accounts/register.html',
                                   msg='Email already registered',
                                   success=False,
                                   form=register_form)
        user = Users(
            user_id=session["user_id"],
            username=session["username"],
            access_token=session["access_token"],
            refresh_token=session["refresh_token"],
            email=email,
            password=passw
            )
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('oauthBP.login'))
    
    return render_template("/user/register.html", form=register_form)

def get_freelancer_user_info(user_id=None):
    headers = {"Freelancer-OAuth-V1": f"{session['access_token'][0]}"}
    freelancer_api_host = "https://www.freelancer-sandbox.com/api"
    api_url = f"{freelancer_api_host}/users/0.1/self"
    params = {
        "jobs": True,
        "avatar": True
    }
    res = requests.get(api_url, headers=headers, params=params, verify=False)
    if res.status_code == 200:
        return res.json().get("result")
    return None

@oauth_bp.route("/self")
def get_user():
    headers = {"Freelancer-OAuth-V1": "87sdtSoZ9s6foqbQcO5jcE9EiICnCT"}
    freelancer_api_host = "https://www.freelancer.com/api"
    api_url = f"{freelancer_api_host}/users/0.1/self"
    params = {
        "display_info": True,
        "avatar": True,
        "jobs": True
    }
    res = requests.get(api_url, headers=headers, params=params, verify=True)
    if res.status_code == 200:
        print(res.json().get("result"))
        return res.json().get("result")
    return None

@oauth_bp.route("/projects")
def get_projects_with_bids():
    headers = {"Freelancer-OAuth-V1": "87sdtSoZ9s6foqbQcO5jcE9EiICnCT"}  # Replace with session token
    freelancer_api_host = "https://www.freelancer.com/api"
    api_url = f"{freelancer_api_host}/projects/0.1/bids/"  # Correct endpoint for bids
    params = {
        "bidders[]": [79920166],  # Your user ID (replace with your actual ID)
        "project_details": True,  # Get detailed user info (optional)
        "user_details": True,  # Get detailed user info (optional)
        "compact": True,  # Get detailed user info (optional)
        "reputation": True,  # Get detailed user info (optional)
        "user_country_details": True,
        "user_employer_reputation": True,
        "limit": 100
    }
    res = requests.get(api_url, headers=headers, params=params, verify=False)
    if res.status_code == 200:
        return res.json().get('result')
    else:
        return {"error": "Failed to retrieve projects", "status_code": res.status_code, "response": res.text}
    
def get_customize_bid(user_id):
    proposal = Customize.query.filter_by(user_id=user_id).first()
    if proposal and proposal.user_id:
        return proposal
    proposal = Customize(user_id=user_id, client=False, User=False, sealed=False, intro="", links=[])
    db.session.add(proposal)
    db.session.commit()
    return proposal
    
def set_pricing(user_id):
    try:
        pricing = Pricing.query.filter_by(user_id=user_id).first()

        if pricing:
            return pricing

        pricing = Pricing(user_id=user_id, fixed="mid", hourly="mid")
        db.session.add(pricing)
        db.session.commit()

        return pricing

    except Exception as e:
        return None

        
def get_bidding_status(user_id):
    status = Bidding.query.filter_by(user_id=user_id).first()
    if status:
        return status
    
    status = Bidding(user_id=user_id, is_bidding="stopped", task="")
    db.session.add(status)
    db.session.commit()
    return status



@oauth_bp.route('/details')
def details():
    info = get_freelancer_user_info()
    return jsonify(info)


def refresh_token():
    """Uses the current refresh token to get a new OAuth access token."""
    user_id = session["user_id"]
    user = Users.query.filter_by(user_id=user_id).first()
    print(user_id)
    url = 'https://accounts.freelancer-sandbox.com/oauth/token'
    payload = {
    'grant_type': 'refresh_token',
    'refresh_token': user.refresh_token,
    'client_id': CONFIG["client_id"],
    'client_secret': CONFIG["client_secret"],
    'redirect_uri': CONFIG["client_redirect"],
    }
    response = requests.post(url, data=payload)
    result = response.json()
    session['access_token'] = result['access_token']
    session['refresh_token'] = result['refresh_token']
    user.access_token = result['access_token']
    user.refresh_token = result['refresh_token']
    db.session.add(user)
    db.session.commit()
    return result

@oauth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('oauthBP.login'))

