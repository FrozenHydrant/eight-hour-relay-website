import os
from flask import Flask, render_template, request, flash, redirect, url_for
from supabase import create_client, Client
from dotenv import load_dotenv
from sanitization import Sanitization
from transactions import Transactions
import math
import datetime as dt
import secrets
from data import Data
import stripe
import requests

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
# Stripe
s_key = os.environ.get("STRIPE_K")
s_client = stripe.StripeClient(s_key)
s_price_id = os.getenv("STRIPE_PRICE_ID")
s_endpoint_secret = os.getenv("STRIPE_ENDPOINT_SECRET")


def is_user_logged_out():
    user_response = None
    try:
        user_response = client.auth.get_claims()
    except:
        pass
    if user_response is not None:
        print("User claims found! Must have been logged in!")
        return False
    print("No user claims found. Must have been logged out...")
    return True


# Routes <Main Page>
@app.route('/')
def index():
    try:
        user_response = client.auth.get_user()
    except:
        user_response = None
    # Initialize some info we need
    user = None
    team_id = -1
    is_captain = False
    not_logged_in = True
    is_undecided = True

    # User exists
    if user_response is not None:
        user = user_response.user
        not_logged_in = False
        if "is_captain" in user.user_metadata:
            is_captain = user.user_metadata["is_captain"]
            is_undecided=False
        team_id = Data.get_enrolled_team(user.id)

    time_left = EVENT_DATE - dt.datetime.now()
    
    if team_id is None:
        team_id = "no_team"
    return render_template("index.html", team_id=team_id, not_logged_in=not_logged_in, is_undecided=is_undecided, is_captain=is_captain, days=time_left.days, hours=math.floor(time_left.seconds/3600), minutes=math.ceil(time_left.seconds%3600/60), seconds=time_left.seconds%60)


# Registration for the whole website
@app.route("/registration")
def registration():
    logged_out = is_user_logged_out()
    if not logged_out:
        return redirect(url_for("index"))
    return render_template("registration.html")

@app.route("/registration", methods=["POST"])
def registration_post():
    logged_out = is_user_logged_out()
    if not logged_out:
        return redirect(url_for("index"))
    
    email = request.form.get("email")
    password = request.form.get("password")

    success = Sanitization.verify_all_and_create_response(email, "ValidUname", password)

    if not success:
        return redirect(url_for("registration"))
    
    # Do signup
    try:
        response = client.auth.sign_up({
            "email": email,
            "password": password,
        })
        user = response.user
        Data.create_new_basic_runner(user.id, email)
    except Exception as e:
        flash(str(e))
        return redirect(url_for("registration"))
    
    return redirect(url_for("index"))


# Captain registration
@app.route("/captain_registration")
def captain_registration():
    logged_out = is_user_logged_out()
    if logged_out:
        return redirect(url_for("login"))
    user = client.auth.get_user().user
    
    # Make sure we are not in any teams beforehand
    enrolled_team = Data.get_enrolled_team(user.id)
    if enrolled_team is not None:
        flash("Leave your team first before becoming a Captain!")
        return redirect(url_for("index"))

    # And also not a captain
    if "is_captain" in user.user_metadata and user.user_metadata["is_captain"]:
        flash("You are already a Captain!")
        return redirect(url_for("teams"))
    
    return render_template("captain_registration.html")

@app.route("/captain_registration", methods=["POST"])
def captain_registration_post():
    logged_out = is_user_logged_out()
    if logged_out:
        return redirect(url_for("login"))
    user = client.auth.get_user().user

    # Make sure we are not in any teams beforehand
    enrolled_team = Data.get_enrolled_team(user.id)
    if enrolled_team is not None:
        flash("Leave your team first before becoming a Captain!")
        return redirect(url_for("captain_registration"))

    # And also not a captain
    if "is_captain" in user.user_metadata and user.user_metadata["is_captain"]:
        flash("You are already a Captain!")
        return redirect(url_for("teams"))


    # Update
    client.auth.update_user({"data": {"is_captain": True}})
    return redirect(url_for("teams"))


# Login for the whole website
@app.route("/login")
def login():
    logged_out = is_user_logged_out()
    if not logged_out:
        return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login_post():
    logged_out = is_user_logged_out()
    if not logged_out:
        return redirect(url_for("index"))

    email = request.form.get("email")
    password = request.form.get("password")

    success = Sanitization.verify_all_and_create_response(email, "ValidUname", password)

    if not success:
        return redirect(url_for("login"))
    
    try:
        _ = client.auth.sign_in_with_password({
            'email': email,
            'password': password,
        })
    except Exception as e:
        flash(str(e))
        return redirect(url_for("login"))
    return redirect(url_for("index"))


# Runner registration
@app.route("/runner_registration")
def runner_registration():
    logged_out = is_user_logged_out()
    if logged_out:
        return redirect(url_for("login"))
    user = client.auth.get_user().user
    
    # Make sure we are not in any teams beforehand
    enrolled_team = Data.get_enrolled_team(user.id)
    if enrolled_team is not None:
        flash("You can't register for another team! Ask your captain to remove you from the current one!")
        return redirect(url_for("index"))

    # And also not a captain
    if "is_captain" in user.user_metadata and user.user_metadata["is_captain"]:
        flash("You are already a Runner!")
        return redirect(url_for("index"))
            
    teams = Data.get_all_teams_info()
    return render_template("registration_runner.html", teams=teams)

@app.route("/runner_registration", methods=["POST"])
def runner_registration_post():
    logged_out = is_user_logged_out()
    if logged_out:
        return redirect(url_for("login"))
    user = client.auth.get_user().user

    # Make sure we are not in any teams beforehand
    enrolled_team = Data.get_enrolled_team(user.id)
    if enrolled_team is not None:
        flash("You can't register for another team! Ask your captain to remove you from the current one!")
        return redirect(url_for("index"))

    # And also not a captain
    if "is_captain" in user.user_metadata and user.user_metadata["is_captain"]:
        flash("You are already a Captain!")
        return redirect(url_for("index"))
    
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    gender = request.form.get("gender")
    age = request.form.get("age")
    phone_number = request.form.get("phone_number")
    emergency_phone = request.form.get("emergency_phone")
    team_id = request.form.get("team_id")
    team_token = request.form.get("team_token")

    success = Sanitization.verify_all_lists_and_create_response([], [], [], [phone_number, emergency_phone], [first_name, last_name], [gender])
    if not success:
        return redirect(url_for("runner_registration"))
    
    if team_id is None or team_token is None:
        flash("Must enter Team Id and Token.")
        return redirect(url_for("runner_registration"))
    
    try:
        age = int(age)
    except Exception as e:
        flash("A problem occured: " + str(e))
        return redirect(url_for("profile"))
    
    if age < 1 or age > 100:
        flash("Enter a valid age.")
        return redirect(url_for("profile"))
    
    # Then check token
    success = Data.check_team_table_credentials(team_id, team_token)
    if not success:
        flash("Team ID or Token is wrong.")
        return redirect(url_for("runner_registration"))
    
    # Do team enrollment
    try:
        _ = Data.enroll_user_in_team(user.id, team_id)
        s = Data.update_runner_info(user.id, {"first_name": first_name, "last_name": last_name, "gender": gender, "age": age, "phone_number": phone_number, "emergency_phone": emergency_phone})
    except Exception as e:
        flash(str(e))
        return redirect(url_for("runner_registration"))
    return redirect(url_for("team_information", team_id=team_id))


@app.route("/profile")
def profile():
    logged_out = is_user_logged_out()
    if logged_out:
        return redirect(url_for("login"))
    
    user = client.auth.get_user().user

    list_info = Data.get_members_info([user.id])
    if len(list_info) < 1:
        Data.create_new_basic_runner(user.id, user.email)

    info = Data.get_members_info([user.id])[0]
    # Change None to empty string
    for k in info:
        if info[k] is None:
            info[k] = ""

    return render_template("profile.html", user_info=info, email=info["email"], username=user.email)


@app.route("/logout")
def logout():
    logged_out = is_user_logged_out()
    if logged_out:
        return redirect(url_for("index"))
    client.auth.sign_out(options={"scope": "local"})
    return redirect(url_for("index"))


@app.route("/profile", methods=["POST"])
def profile_post():
    logged_out = is_user_logged_out()
    if logged_out:
        return redirect(url_for("login"))
    
    user = client.auth.get_user().user

    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    gender = request.form.get("gender")
    age = request.form.get("age")
    phone_number = request.form.get("phone_number")
    emergency_phone = request.form.get("emergency_phone")

    success = Sanitization.verify_all_lists_and_create_response([], [], [], [phone_number, emergency_phone], [first_name, last_name], [gender])
    if not success:
        return redirect(url_for("profile"))
    
    try:
        age = int(age)
    except Exception as e:
        flash("A problem occured: " + str(e))
        return redirect(url_for("profile"))
    
    if age < 1 or age > 100:
        flash("Enter a valid age.")
        return redirect(url_for("profile"))
    
    updated_info = {"first_name": first_name, "last_name": last_name, "gender": gender, "age": age, "phone_number": phone_number, "emergency_phone": emergency_phone}
    success = Data.update_runner_info(user.id, updated_info)
    if not success:
        flash("Error occured while updating information.")
        return redirect(url_for("profile"))
    
    flash("Successfully updated information.")
    return redirect(url_for("profile"))


@app.route("/team_registration")
def team_registration():
    logged_out = is_user_logged_out()
    if logged_out:
        return redirect(url_for("login"))
    user = client.auth.get_user().user

    # Only captains
    if "is_captain" not in user.user_metadata or not user.user_metadata["is_captain"]:
        return redirect(url_for("index"))

    return render_template("team_registration.html")


@app.route("/team_registration", methods=["POST"])
def team_registration_post():
    logged_out = is_user_logged_out()
    if logged_out:
        return redirect(url_for("login"))
    user = client.auth.get_user().user

    # Only captains
    if "is_captain" not in user.user_metadata or not user.user_metadata["is_captain"]:
        return redirect(url_for("index"))
    
    team_name = request.form.get("team_name")
    division = request.form.get("division")

    # Verify team name
    if not Sanitization.verify_username_characters(team_name):
        flash("Team name contains invalid characters.")
        return redirect(url_for("team_registration"))
    if not Sanitization.verify_username_length(team_name):
        flash("Team name must be between 3-16 characters.")
        return redirect(url_for("team_registration"))
    
    # Verify division correctness
    if division not in set(["open", "mixed", "master"]):
        flash("Something went wrong while setting the division of your team.")
        return redirect(url_for("team_registration"))
    
    token = secrets.token_urlsafe(3)

    # Add table entry
    team_id: str = Data.create_team(team_name, user.id, token, division, user.email)
    if team_id is None:
        return redirect(url_for("error_page"))
    
    return redirect(url_for("team_created", team_token=token, team_id=team_id))


@app.route("/team_created")
def team_created():
    logged_out = is_user_logged_out()
    if logged_out:
        return redirect(url_for("index"))
    
    user = client.auth.get_user().user

    # Only captains
    if "is_captain" not in user.user_metadata or not user.user_metadata["is_captain"]:
        return redirect(url_for("index"))
    
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
    logged_out = is_user_logged_out()
    if logged_out:
        return redirect(url_for("index"))
    user = client.auth.get_user().user

    # Get the team ID
    team_id = request.args.get("team_id")
    if team_id is None:
        return redirect(url_for("error_page"))

    # Handle no team -> We got kicked ?
    if team_id == "no_team":
        return redirect(url_for("runner_registration"))
    
    # Now get the team info from that
    team_info = Data.get_team_info(team_id)
    #print(team_info, "team_info")
    if team_info is None:
        return redirect(url_for("error_page"))
    
    # Make sure we actually own the team OR are part of it
    owned_teams = Data.get_owned_teams(user.id)
    team_members = Data.get_members_list(team_id)
    #print("owned", owned_teams, team_members)
    if team_id not in owned_teams and user.id not in team_members:
        return redirect(url_for("error_page"))
    
    combined_member_infos = Data.get_members_info(team_members)
    
    # If I'm a runner and I have unfinished info, finish it!
    # (All fields must be filled simultaneously, so just checking one is fine)
    for member_info in combined_member_infos:
        #print(member_info)
        if member_info["user_id"] == user.id and member_info["first_name"] is None:
            flash("You have not filled in your Runner Info yet! Please go to your Profile and finish adding your information. You must do this before the deadline! ")

    #print(combined_member_infos)
    is_captain = False
    if "is_captain" in user.user_metadata:
        is_captain = user.user_metadata["is_captain"]
    return render_template("team_information.html", team=team_info, is_captain=is_captain, members=combined_member_infos)


@app.route("/team_token_reset")
def team_token_reset():
    logged_out = is_user_logged_out()
    if logged_out:
        return redirect(url_for("login"))
    user = client.auth.get_user().user

    # Get team id
    team_id = request.args.get("team_id")
    if team_id is None:
        return redirect(url_for("error_page"))
    
    # Check if we actually have permission to modify this team (i.e we own it)
    owned_teams = Data.get_owned_teams(user.id)
    if team_id not in owned_teams:
        return redirect(url_for("error_page"))
    
    new_token = Data.generate_new_team_token(team_id)
    if new_token is None:
        return redirect(url_for("error_page"))
    
    return render_template("team_token_reset.html", team_token=new_token, team_id=team_id)


@app.route("/teams")
def teams():
    logged_out = is_user_logged_out()
    if logged_out:
        return redirect(url_for("login"))
    user = client.auth.get_user().user
    # Don't do it if I'm not a captain (we should not see this page)
    if "is_captain" not in user.user_metadata or not user.user_metadata["is_captain"]:
        return redirect(url_for("index"))

    teams = Data.get_owned_teams_info(user.id)
    #print(teams, "teams")
    return render_template("teams.html", username=user.email, teams=teams)


@app.route("/manage_team_member")
def manage_team_member():
    logged_out = is_user_logged_out()
    if logged_out:
        return redirect(url_for("login"))
    user = client.auth.get_user().user

    # Only captains are allowed!
    if "is_captain" not in user.user_metadata or not user.user_metadata["is_captain"]:
        return redirect(url_for("index"))
    
    member_id = request.args.get("member_id")
    team_id = request.args.get("team_id")

    if not Data.has_authority_over_member(user.id, member_id, team_id):
        return redirect(url_for("error_page"))
    
    member_info = Data.get_members_info([member_id])[0]

    for k in member_info:
        if member_info[k] is None:
            member_info[k] = "No Data"
    return render_template("manage_team_member.html", team_id=team_id, member=member_info)


#TODO: critical actions should use post requests not get requests
@app.route("/delete_from_team")
def delete_from_team():
    logged_out = is_user_logged_out()
    if logged_out:
        return redirect(url_for("login"))
    
    user = client.auth.get_user().user 

    # Only captains are allowed!
    if "is_captain" not in user.user_metadata or not user.user_metadata["is_captain"]:
        return redirect(url_for("index"))
    
    member_id = request.args.get("member_id")
    team_id = request.args.get("team_id")
    if not Data.has_authority_over_member(user.id, member_id, team_id):
        return redirect(url_for("error_page"))
    
    s = Data.unenroll_member_from_team(member_id, team_id)
    #print(s, "Delete success")
    # TODO: warning on s being false (operation failed) ?
    return redirect(url_for("team_information", team_id=team_id))


@app.route("/team_payment")
def team_payment():
    logged_out = is_user_logged_out()
    if logged_out:
        return redirect(url_for("login"))
    user = client.auth.get_user().user

    # Only captains are allowed!
    if "is_captain" not in user.user_metadata or not user.user_metadata["is_captain"]:
        return redirect(url_for("index"))

    team_id = request.args.get("team_id")

    if team_id is None:
        return redirect(url_for("error_page"))
    
    # And we own the team which has not been paid
    owned = Data.get_owned_teams(user.id)
    if team_id not in owned:
        return redirect(url_for("index"))
    
    payment_state = Data.get_team_info(team_id)["paid"]
    if payment_state:
        return redirect(url_for("error_page"))
    
    completion_url = request.url_root[:-1:] + url_for("team_information", team_id=team_id)
    #print(completion_url)
    payment_link = s_client.v1.payment_links.create({
        "line_items": [{"price": s_price_id, "quantity": 1}],
        "after_completion": {"type": "redirect", "redirect": {"url": completion_url}},
        "metadata": {"team_id": team_id, "user_id": user.id}
    })
    
    return redirect(payment_link.url)


# TODO: rename?
# https://docs.stripe.com/webhooks
@app.route("/team_payment_webhook", methods=["POST"])
def team_payment_webhook():
    if request.content_length > 8192:
        return "Too long", 500

    payload = request.get_data()
    sig_header = request.headers["STRIPE_SIGNATURE"]
    event: stripe.Event = None

    try:
        event = s_client.construct_event(
            payload, sig_header, s_endpoint_secret
        )
    except Exception as e:
        print(e)
        return f"Exception: {e}", 500

    # Handle the event
    if event.type == 'checkout.session.completed':
        checkout_session = event.data.object
        Transactions.complete_payment(checkout_session.id)
        return ""
    return "Event not supported", 500


@app.route("/error_page")
def error_page():
    return "TODO: error page"


if __name__ == '__main__':
    app.run()