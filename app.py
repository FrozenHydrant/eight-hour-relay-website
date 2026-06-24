import os
from flask import Flask, render_template, request, flash, redirect, url_for
from supabase import create_client, Client
from dotenv import load_dotenv
from util import Util
import math
import datetime as dt
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from data import Data

# App initialization happens here
EVENT_DATE = dt.datetime(2026, 9, 12)
load_dotenv()
app = Flask(__name__)
client: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)
app.secret_key = os.environ.get("SECRET_KEY")
Data.initialize(client)

# Routes
@app.route('/')
def index():
    try:
        user_response = client.auth.get_user()
    except:
        user_response = None
    user = None
    if user_response is not None:
        user = user_response.user

    time_left = EVENT_DATE - dt.datetime.now()
    return render_template("index.html", current_user=user, days=time_left.days, hours=math.floor(time_left.seconds/3600), minutes=math.ceil(time_left.seconds%3600/60), seconds=time_left.seconds%60)


# Registration selection
@app.route("/registration")
def registration():
    try:
        user_response = client.auth.get_user()
    except:
        user_response = None
    if user_response is not None:
        return redirect(url_for("index"))

    return render_template("registration.html")


# Captain registration
@app.route("/captain_registration")
def captain_registration():
    try:
        user_response = client.auth.get_user()
    except:
        user_response = None
    if user_response is not None:
        return redirect(url_for("index"))
    
    return render_template("registration_captain.html")


@app.route("/captain_registration", methods=["POST"])
def captain_registration_post():
    try:
        user_response = client.auth.get_user()
    except:
        user_response = None
    if user_response is not None:
        return redirect(url_for("index"))

    print(request.remote_addr, "registration.")
    email = request.form.get("email")
    username = request.form.get("username")
    password = request.form.get("password")
    
    success = Util.verify_all_and_create_response(email, username, password)

    if not success:
        return redirect(url_for("captain_registration"))
    
    # Do signup
    try:
        response = client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": {"username": username, "is_captain": True}}
        })
    except Exception as e:
        flash(str(e))
        return redirect(url_for("captain_registration"))
    return redirect(url_for("login"))


# Runner registration
@app.route("/runner_registration")
def runner_registration():
    try:
        user_response = client.auth.get_user()
    except:
        user_response = None
    if user_response is not None:
        return redirect(url_for("index"))
    
    return render_template("registration_runner.html")


@app.route("/runner_registration", methods=["POST"])
def runner_registration_post():
    try:
        user_response = client.auth.get_user()
    except:
        user_response = None
    if user_response is not None:
        return redirect(url_for("index"))
    
    email = request.form.get("email")
    username = request.form.get("username")
    password = request.form.get("password")
    team_id = request.form.get("team_id")
    team_token = request.form.get("team_token")

    success = Util.verify_all_and_create_response(email, username, password)

    if not success:
        return redirect(url_for("runner_registration"))
    
    if team_id is None or team_token is None:
        flash("Must enter Team Id and Token.")
        return redirect(url_for("runner_registration"))
    
    # Then check token
    success = Data.check_team_table_credentials(team_id, team_token)
    if not success:
        flash("Team ID or Token is wrong.")
        return redirect(url_for("runner_registration"))
    
    # Do signup
    try:
        response = client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": {"username": username, "is_captain": False}}
        })
        new_response = Data.enroll_user_in_team(response.user.id, team_id)
        #print(new_response)
        if new_response is None:
            flash("Unexpected error in registration.")
            return redirect(url_for("runner_registration"))
    except Exception as e:
        flash(str(e))
        return redirect(url_for("runner_registration"))
    return redirect(url_for("login"))


@app.route("/login")
def login():
    try:
        user_response = client.auth.get_user()
    except:
        user_response = None
    if user_response is not None:
        return redirect(url_for("index"))

    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login_post():
    try:
        user_response = client.auth.get_user()
    except:
        user_response = None
    if user_response is not None:
        return redirect(url_for("index"))

    print(request.remote_addr, "login.")
    input_email = request.form.get("email")
    input_password = request.form.get("password")

    if not Util.verify_email_characters(input_email):
        flash("Email contains invalid characters.")
        return redirect(url_for("login"))
    if not Util.verify_password_characters(input_password):
        flash("Password contains invalid characters.")
        return redirect(url_for("login"))
    
    # Verify lengths
    if not Util.verify_email_length(input_email):
        flash("Bad email length.")
        return redirect(url_for("login"))
    if not Util.verify_password_length(input_password):
        flash("Bad password length.")
        return redirect(url_for("login"))

    # Verify email
    if not Util.verify_email_correctness(input_email):
        flash("Invalid email.")
        return redirect(url_for("login"))
    
    try:
        data = client.auth.sign_in_with_password({
            'email': input_email,
            'password': input_password,
        })
    except Exception as e:
        flash(str(e))
        return redirect(url_for("login"))
    return redirect(url_for("index"))


@app.route("/profile")
def profile():
    try:
        user_response = client.auth.get_user()
    except:
        user_response = None
    if user_response is None:
        flash("You must log in to view this page.")
        return redirect(url_for("login"))
    user = user_response.user

    return render_template("profile.html", email=user.email, username=user.user_metadata["username"])


@app.route("/logout")
def logout():
    client.auth.sign_out()
    return redirect(url_for("index"))


@app.route("/team_registration")
def team_registration():
    try:
        user_response = client.auth.get_user()
    except:
        user_response = None
    if user_response is None:
        flash("You must log in to view this page.")
        return redirect(url_for("login"))
    user = user_response.user

    return render_template("team_registration.html")


@app.route("/team_registration", methods=["POST"])
def team_registration_post():
    try:
        user_response = client.auth.get_user()
    except:
        user_response = None
    if user_response is None:
        flash("You must log in to view this page.")
        return redirect(url_for("login"))
    user = user_response.user

    team_name = request.form.get("team_name")

    if not Util.verify_username_characters(team_name):
        flash("Team name contains invalid characters.")
        return redirect(url_for("team_registration"))
    if not Util.verify_username_length(team_name):
        flash("Team name must be between 3-16 characters.")
        return redirect(url_for("team_registration"))
    
    # Create token
    token = secrets.token_urlsafe()

    # Add table entry
    team_id: str = Data.create_team(team_name, user.id, token)
    if team_id is None:
        return redirect(url_for("error_page"))
    
    return redirect(url_for("team_created", team_token=token, team_id=team_id))


@app.route("/team_created")
def team_created():
    try:
        user_response = client.auth.get_user()
    except:
        user_response = None
    if user_response is None:
        flash("You must log in to view this page.")
        return redirect(url_for("login"))
    user = user_response.user

    team_id = request.args.get("team_id")
    team_token = request.args.get("team_token")
    
    if team_id is None or team_token is None:
        return redirect(url_for("error_page"))
    
    # Then check if everything is correct (we didn't do anything silly like modify the url)
    success = Data.check_team_table_credentials(team_id, team_token)
    owned_teams = Data.get_owned_teams(user.id)
    #print(owned_teams, success, team_id)

    if not success or team_id not in owned_teams:
        return redirect(url_for("error_page"))
    
    return render_template("team_created.html", team_id=team_id, team_token=team_token)


@app.route("/team_information")
def team_information():
    try:
        user_response = client.auth.get_user()
    except:
        user_response = None
    if user_response is None:
        flash("You must log in to view this page.")
        return redirect(url_for("login"))
    user = user_response.user

    team_id = request.args.get("team_id")

    if team_id is None:
        return redirect(url_for("error_page"))

    team_info = Data.get_team_info(team_id)
    if team_info is None:
        return redirect(url_for("error_page"))
    
    member_ids = Data.get_members_list(team_id)
    members = []
    # TODO: fix
    #for member_id in member_ids:
    #    u = client.auth.admin.get_user_by_id(member_id)
    #    members.append(u)

    return render_template("team_information.html", team=team_info, members=[])


@app.route("/teams")
def teams():
    try:
        user_response = client.auth.get_user()
    except:
        user_response = None
    if user_response is None:
        flash("You must log in to view this page.")
        return redirect(url_for("login"))
    user = user_response.user

    teams = Data.get_owned_teams_info(user.id)
    print(teams)
    return render_template("teams.html", username=user.user_metadata["username"], teams=teams)


@app.route("/error_page")
def error_page():
    return "TODO: error page"


if __name__ == '__main__':
    app.run(debug=True)