import os
from flask import Flask, render_template, request, flash, redirect, url_for, make_response
from supabase import create_client, Client
from dotenv import load_dotenv
from sanitization import Sanitization
from transactions import Transactions
from emails import EmailSender
import math
import datetime as dt
import secrets
from data import Data
from dateutil import relativedelta
import stripe

# App initialization happens here
# CONSTANTS TOO
load_dotenv()
EVENT_DATE = dt.datetime(2026, 9, 12)
WAIVER_VERSION = 2
GENDERS_MAPPING = {"male": "Male", "female": "Female", "non-binary": "Non-Binary"}

# App setup
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
# Supabase
auth_client: Client = create_client(
        os.environ.get("SUPABASE_URL"),
        os.environ.get("SUPABASE_KEY")
    )
admin_client: Client = create_client(
        os.environ.get("SUPABASE_URL"),
        os.environ.get("SUPABASE_KEY")
)
# App
Data.initialize()

# Stripe
s_key = os.environ.get("STRIPE_K")
s_client = stripe.StripeClient(s_key)
s_price_id = os.getenv("STRIPE_PRICE_ID")
s_endpoint_secret = os.getenv("STRIPE_ENDPOINT_SECRET")


# Helpers Functions
def user_logout_status(access_token=None):
    if access_token is None:
        access_token = request.cookies.get("access_token")

    if access_token is None:
        return None

    try:
        user_response = auth_client.auth.get_user(access_token)
        if user_response is not None:
            #print(user_response.user, type(user_response.user))
            return user_response.user
    except:
        return None

# TODO: CSRF security
def cookie_options():
    return {
        "path": "/",
        "httponly": True,
        "secure": not app.debug,
        "samesite": "Lax",
    }

# Static Cache
@app.after_request
def add_cache_headers(response):
    # Cache static assets for 31 days
    if request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'public, max-age=2678400, immutable'
    return response

# Adding cookies for login
def generate_cookied_response(response, key_value):
    cookied_response = make_response(response)
    cookied_response.set_cookie(
        key_value["key"],
        key_value["value"],
        max_age=3600,
        **cookie_options(),
    )
    return cookied_response

# Deleting cookies after logout
def generate_uncookied_response(response, keys):
    uncookied_response = make_response(response)
    for key in keys:
        uncookied_response.set_cookie(
            key,
            "",
            expires=0,
            max_age=0,
            **cookie_options(),
        )
    return uncookied_response


#
# Routes <Main Page>
@app.route('/')
def index():
    user = user_logout_status()
    user_name = None
    team_id = -1
    is_captain = False
    not_logged_in = True
    is_undecided = True
    user_email = None

    # User exists
    is_admin = False
    if user is not None:
        is_admin = Data.is_user_admin(user.id)
        not_logged_in = False
        captain_status = Data.get_captain_status(user.id)
        print("Captain status;", captain_status)
        if captain_status != 0:
            if captain_status == 1:
                is_captain = False
            else:
                is_captain = True
            is_undecided=False
        
        # Get more team info
        team_id = Data.get_enrolled_team(user.id)
        
        # Also set the email
        user_email = user.email

        # And name
        self_data = Data.get_members_info([user.id])
        if len(self_data) > 0:
            user_info = self_data[0]
            if "first_name" in user_info:
                user_name = user_info["first_name"]

        # Properly populate "is_captain"
        if captain_status == 0:
            if len(Data.get_owned_teams(user.id)) > 0:
                try:
                    Data.upsert_captain_status(user.id, True)
                except:
                    pass
                return redirect(url_for("index"))

            if team_id is not None:
                try:
                    Data.upsert_captain_status(user.id, False)
                except:
                    pass
                return redirect(url_for("index"))
            

    time_left = EVENT_DATE - dt.datetime.now()
    
    if team_id is None:
        team_id = "no_team"

    return render_template("index.html", user_name=user_name, user_email=user_email, team_id=team_id, not_logged_in=not_logged_in, is_admin=is_admin, is_undecided=is_undecided, is_captain=is_captain, days=time_left.days, hours=math.floor(time_left.seconds/3600), minutes=math.ceil(time_left.seconds%3600/60), seconds=time_left.seconds%60)


# Registration for the whole website
@app.route("/registration")
def registration():
    user = user_logout_status()
    if user:
        return redirect(url_for("index"))
    return render_template("registration.html")

@app.route("/registration", methods=["POST"])
def registration_post():
    user = user_logout_status()
    if user:
        return redirect(url_for("index"))
    
    email = request.form.get("email")
    password = request.form.get("password")

    success = Sanitization.verify_all_and_create_response(email, "ValidUname", password)

    if not success:
        return redirect(url_for("registration"))
    
    # Do signup
    try:
        response = auth_client.auth.sign_up({
            "email": email,
            "password": password,
        })
        user = response.user
        Data.create_new_basic_runner(user.id, user.email)
    except Exception as e:
        flash(str(e))
        return redirect(url_for("registration"))
    
    return generate_cookied_response(
        redirect(url_for("index")),
        {"key": "access_token", "value": response.session.access_token},
    )


# Captain registration
@app.route("/captain_registration")
def captain_registration():
    user = user_logout_status()
    if not user:
        return redirect(url_for("login",next_page="captain_registration"))
    #user = client.auth.get_user().user
    
    # Make sure we are not in any teams beforehand
    enrolled_team = Data.get_enrolled_team(user.id)
    if enrolled_team is not None:
        flash("Leave your team first before becoming a Captain!")
        return redirect(url_for("index"))

    # And also not a captain
    if Data.get_captain_status(user.id) == 2:
        flash("You are already a Captain!")
        return redirect(url_for("teams"))
    
    user_info = Data.get_members_info([user.id])    
    return render_template("registration_captain.html", user_info=user_info, genders_mapping=GENDERS_MAPPING)

@app.route("/captain_registration", methods=["POST"])
def captain_registration_post():
    user = user_logout_status()
    if not user:
        return redirect(url_for("login"))

    # Make sure we are not in any teams beforehand
    enrolled_team = Data.get_enrolled_team(user.id)
    if enrolled_team is not None:
        flash("Leave your team first before becoming a Captain!")
        return redirect(url_for("captain_registration"))

    # And also not a captain
    if Data.get_captain_status(user.id) == 2:
        flash("You are already a Captain!")
        return redirect(url_for("teams"))

    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    gender = request.form.get("gender")
    birthyear = request.form.get("birthyear")
    birthmonth = request.form.get("birthmonth")
    birthday = request.form.get("birthday")
    phone_number = request.form.get("phone_number")

    success = Sanitization.verify_all_lists_and_create_response([], [], [], [phone_number], [first_name, last_name], [gender])
    if not success:
        return redirect(url_for("captain_registration"))
    
    birthdate = None
    try:
        birthdate = dt.datetime(int(birthyear), int(birthmonth), int(birthday))
    except Exception as e:
        flash("Bad birthdate entered.")
        return redirect(url_for("captain_registration"))
    
    # Calculate age via birthdate
    age = relativedelta.relativedelta(EVENT_DATE, birthdate).years
    #print(age)
    
    # Do captain enrollment
    try:
        upd_resp = Data.update_runner_info(user.id, {"first_name": first_name, "last_name": last_name, "gender": gender, "birthdate": birthdate.strftime("%m/%d/%Y"), "phone_number": phone_number})
        _ = Data.upsert_captain_status(user.id, True)
    except Exception as e:
        flash(str(e))
        print(e, "captain reg failed")
        return redirect(url_for("captain_registration"))
    return redirect(url_for("team_registration"))


# Login for the whole website / Logout
@app.route("/login")
def login():
    logged_in = user_logout_status()
    if logged_in:
        return redirect(url_for("index"))

    # Hidden next page parameter for redirecting after login
    next_page = request.args.get("next_page", "")
    return render_template("login.html", next_page=next_page)

@app.route("/login", methods=["POST"])
def login_post():
    logged_in = user_logout_status()
    if logged_in:
        return redirect(url_for("index"))

    email = request.form.get("email")
    password = request.form.get("password")
    next_page = request.form.get("next_page")

    success = Sanitization.verify_all_and_create_response(email, "ValidUname", password)

    if not success:
        return redirect(url_for("login"))
    
    response = None
    try:
        response = auth_client.auth.sign_in_with_password({
            'email': email,
            'password': password,
        })
    except Exception as e:
        flash(str(e))
        return redirect(url_for("login"))
    
    next_page = Sanitization.verify_next_page(next_page)

    return generate_cookied_response(
        redirect(url_for(next_page)),
        {"key": "access_token", "value": response.session.access_token},
    )

@app.route("/logout")
def logout():
    logged_in = user_logout_status()
    if not logged_in:
        return redirect(url_for("index"))
    
    access_token = request.cookies.get("access_token")
    try:
        admin_client.auth.admin.sign_out(access_token)
    except Exception:
        pass

    return generate_uncookied_response(redirect(url_for("index")), ["access_token"])


# Runner registration
@app.route("/runner_registration")
def runner_registration():
    user = user_logout_status()
    if not user:
        return redirect(url_for("login", next_page="runner_registration"))
    # Autofill some information
    token = request.args.get("token")
    team_id = request.args.get("team_id")
    team_name = None
    team_division = None

    #
    if team_id is not None:
        team_basic_info = Data.get_team_basic_info(team_id)
        # Bad team id specified -> just don't give
        if team_basic_info is None:
            team_id = None
        else: 
            team_name = team_basic_info["team_name"]
            team_division = team_basic_info["division"]

    # Make sure we are not in any teams beforehand
    enrolled_team = Data.get_enrolled_team(user.id)
    if enrolled_team is not None:
        flash("You can't register for another team! Ask your captain to remove you from the current one!")
        return redirect(url_for("index"))

    # And if we are a captain, only let us join our own team...
    owned_teams = []
    if Data.get_captain_status(user.id) == 2:
        flash("Note: As a captain, you can only register into a team you own.")
        owned_teams = Data.get_owned_teams_info(user.id)
    teams = Data.get_all_teams_info()

    for owned_team in owned_teams:
        if owned_team in teams:
            teams.remove(owned_team)

    # Ensure runner record exists and pass existing info to the form so fields can be prefilled
    users_info = Data.get_members_info([user.id])
    if len(users_info) < 1:
        flash("An unknown problem occured")
        return redirect(url_for("index"))
    
    user_info = users_info[0]
    for k in user_info:
        if user_info[k] is None:
            user_info[k] = ""
    if token is None:
        token = ""

    return render_template("registration_runner.html", teams=teams, owned_teams=owned_teams, user_info=user_info, token=token, team_id=team_id, team_name=team_name, team_division=team_division, genders_mapping=GENDERS_MAPPING)

@app.route("/runner_registration", methods=["POST"])
def runner_registration_post():
    user = user_logout_status()
    if not user:
        return redirect(url_for("login"))

    # Make sure we are not in any teams beforehand
    enrolled_team = Data.get_enrolled_team(user.id)
    if enrolled_team is not None:
        flash("You can't register for another team! Ask your captain to remove you from the current one!")
        return redirect(url_for("index"))
    
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    gender = request.form.get("gender")
    birthyear = request.form.get("birthyear")
    birthmonth = request.form.get("birthmonth")
    birthday = request.form.get("birthday")
    phone_number = request.form.get("phone_number")
    emergency_name = request.form.get("emergency_name")
    emergency_phone = request.form.get("emergency_phone")
    team_id = request.form.get("team_id")
    team_token = request.form.get("team_token")
    waiver_agreed = request.form.get("waiver_agreed") == "on"
    shirt_size = request.form.get("shirt_size")

    success = Sanitization.verify_all_lists_and_create_response([], [], [], [phone_number, emergency_phone], [first_name, last_name, emergency_name], [gender])

    if not success:
        return redirect(url_for("runner_registration"))
    
    if shirt_size not in ("S", "M", "L", "XL", "XXL"):
        flash("Invalid shirt size!")
        return redirect(url_for("runner_registration"))
    
    if team_id is None or team_token is None:
        flash("Must enter Team Id and Token.")
        return redirect(url_for("runner_registration"))
    
    # And also captain
    if Data.get_captain_status(user.id) == 2 and team_id not in Data.get_owned_teams(user.id):
        flash("You cannot join someone else's team as a captain!")
        return redirect(url_for("runner_registration"))

    if not waiver_agreed:
        flash("You must open the waiver and agree to it before registering.")
        return redirect(url_for("runner_registration"))
    
    birthdate = None
    try:
        birthdate = dt.datetime(int(birthyear), int(birthmonth), int(birthday))
    except Exception as e:
        flash("Bad birthdate entered.")
        return redirect(url_for("runner_registration"))
    
    # Calculate age via birthdate
    age = relativedelta.relativedelta(EVENT_DATE, birthdate).years

    # If younger than 19 on event date must handle parent fields
    # Otherwise we don't store those
    parent_name = None
    parent_relationship = None
    if age < 19:
        # Now get them from the form
        parent_agreed = request.form.get("parent_agreed") == "on"
        parent_name = request.form.get("parent_name")
        parent_relationship = request.form.get("parent_relationship")

        if not Sanitization.verify_all_lists_and_create_response([], [], [], [], [parent_name, parent_relationship], []):
            flash("Check your parent information and try again!")
            return redirect(url_for("runner_registration"))
        
        parent_confirm_name = request.form.get("parent_confirm_name")

        if parent_confirm_name != parent_name:
            flash("Parent Name and Confirm Parent Name do not match")
            return redirect(url_for("runner_registration"))
        
        if not parent_agreed:
            flash("Parent must agree to the parent consent statemet!")
            return redirect(url_for("runner_registration"))

    team_division = None
    team_basic_info = Data.get_team_basic_info(team_id)
    if team_basic_info is not None:
        team_division = team_basic_info.get("division")

    if team_division == "master" and age < 50:
        flash("Master teams require runners to be at least 50 years old.")
        return redirect(url_for("runner_registration"))

    if team_division in ("open", "mixed") and age < 15:
        flash("Open and mixed teams require runners to be at least 15 years old.")
        return redirect(url_for("runner_registration"))
    
    # Then check token
    success = Data.check_team_table_credentials(team_id, team_token)
    if not success:
        flash("Team ID or Token is wrong.")
        return redirect(url_for("runner_registration"))

    # Check team capacity
    members = Data.get_members_list(team_id)
    if len(members) >= 8:
        flash("This team already has the maximum of 8 members.")
        return redirect(url_for("runner_registration"))
    
    # Do team enrollment
    try:
        # If we are undecided and join a team, we are a runner.
        if Data.get_captain_status(user.id) == 0:
            upd_resp = Data.upsert_captain_status(user.id, False)
        #print("Update Captain Status Response: ", upd_resp)

        enr_resp = Data.enroll_user_in_team(user.id, team_id)
        #print("Enrollment response: ", enr_resp)

        upd_resp = Data.update_runner_info(user.id, {"first_name": first_name, "last_name": last_name, "gender": gender, "birthdate": birthdate.strftime("%m/%d/%Y"), "shirt_size": shirt_size, "waiver_agreement": WAIVER_VERSION, "phone_number": phone_number, "emergency_name": emergency_name, "emergency_phone": emergency_phone, "parent_name": parent_name, "parent_relationship": parent_relationship})
        #print("Update Runner Info Response: ", upd_resp)
        
        usr_resp = Data.setup_user_position(user.id, team_id)
        #print("Setup User Pos Resp: ", usr_resp)

        EmailSender.send_team_registration_email(user.email, team_id, team_basic_info.get("team_name", "Unknown"), team_basic_info.get("division", "Unknown"))
        
        team_email = Data.get_team_info(team_id)["email"]
        EmailSender.send_team_registration_email_captain(team_email, team_id, team_basic_info.get("team_name", "Unknown"), user.email)
    except Exception as e:
        flash(str(e))
        return redirect(url_for("runner_registration"))
    return redirect(url_for("team_information", team_id=team_id))


# Profile management
@app.route("/profile")
def profile():
    user = user_logout_status()
    if not user:
        return redirect(url_for("login"))

    list_info = Data.get_members_info([user.id])
    if len(list_info) < 1:
        flash("An unknown problem occured, please try again in a moment")
        return redirect(url_for("index"))

    info = list_info[0]
    # Change None to empty string
    for k in info:
        if info[k] is None:
            info[k] = ""

    return render_template("profile.html", user_info=info, email=info["email"], genders_mapping=GENDERS_MAPPING)


@app.route("/profile", methods=["POST"])
def profile_post():
    user = user_logout_status()
    if not user:
        return redirect(url_for("login"))

    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    gender = request.form.get("gender")
    birthyear = request.form.get("birthyear")
    birthmonth = request.form.get("birthmonth")
    birthday = request.form.get("birthday")
    phone_number = request.form.get("phone_number")
    emergency_name = request.form.get("emergency_name")
    emergency_phone = request.form.get("emergency_phone")

    success = Sanitization.verify_all_lists_and_create_response([], [], [], [phone_number, emergency_phone], [first_name, last_name, emergency_name], [gender])
    if not success:
        return redirect(url_for("profile"))
    
    birthdate = None
    try:
        birthdate = dt.datetime(int(birthyear), int(birthmonth), int(birthday))
    except Exception as e:
        flash("Bad birthdate entered.")
        return redirect(url_for("profile"))
    
    # Calculate age via birthdate
    age = relativedelta.relativedelta(EVENT_DATE, birthdate).years

    if age < 1 or age > 100:
        flash("Enter a valid age.")
        return redirect(url_for("profile"))
    
    updated_info = {"first_name": first_name, "last_name": last_name, "gender": gender, "birthdate": birthdate.strftime("%m/%d/%Y"), "phone_number": phone_number, "emergency_name": emergency_name, "emergency_phone": emergency_phone}
    success = Data.update_runner_info(user.id, updated_info)
    if not success:
        flash("Error occured while updating information.")
        return redirect(url_for("profile"))
    
    flash("Successfully updated information.")
    return redirect(url_for("profile"))


@app.route("/team_registration")
def team_registration():
    user = user_logout_status()
    if not user:
        return redirect(url_for("login"))

    # Only captains
    if Data.get_captain_status(user.id) != 2:
        return redirect(url_for("index"))

    return render_template("team_registration.html")


@app.route("/team_registration", methods=["POST"])
def team_registration_post():
    user = user_logout_status()
    if not user:
        return redirect(url_for("login"))

    # Only captains
    if Data.get_captain_status(user.id) != 2:
        return redirect(url_for("index"))
    
    team_name = request.form.get("team_name")

    # Generate captain name from existing data
    captain_info = Data.get_members_info([user.id])[0]
    captain_name = captain_info["first_name"] + " " + captain_info["last_name"]
    division = request.form.get("division")

    # Verify names
    if not Sanitization.verify_all_lists_and_create_response([], [team_name], [], [], [captain_name], []):
        return redirect(url_for("team_registration"))
        
    # Verify division correctness
    if division not in set(["open", "mixed", "master"]):
        flash("Something went wrong while setting the division of your team.")
        return redirect(url_for("team_registration"))

    if Data.team_name_exists(team_name):
        flash("A team with that name already exists. Please choose another name.")
        return redirect(url_for("team_registration"))
    
    # Add table entry
    team_id: str = Data.create_team(team_name, user.id, division, user.email, captain_name)
    if team_id is None:
        return redirect(url_for("error_page"))
    
    return redirect(url_for("team_payment_page", team_id=team_id))


@app.route("/team_payment_page")
def team_payment_page():
    user = user_logout_status()
    if not user:
        return redirect(url_for("login"))
    
    # Only captains
    if Data.get_captain_status(user.id) != 2:
        return redirect(url_for("index"))
    
    # Get the team ID
    team_id = request.args.get("team_id")
    team_info = Data.get_team_basic_info(team_id)

    if team_info is None:
        flash("A problem occured when trying to pay for this team!")
        return redirect(url_for("team_information", team_id=team_id))
    
    if team_id not in Data.get_owned_teams(user.id):
        flash("You don't own the team you are trying to pay for!")
        return redirect(url_for("team_information", team_id=team_id))
    
    payment_state = Data.get_team_info(team_id)["paid"]
    if payment_state:
        return redirect(url_for("error_page"))
    
    return render_template("team_payment_page.html", team_info=team_info)


@app.route("/team_payment_page", methods=["POST"])
def team_payment_page_post():
    user = user_logout_status()
    if not user:
        return redirect(url_for("login"))

    # Only captains are allowed!
    if Data.get_captain_status(user.id) != 2:
        return redirect(url_for("index"))

    team_id = request.form.get("team_id")

    if team_id is None:
        return redirect(url_for("error_page"))
    
    # And we own the team which has not been paid
    owned = Data.get_owned_teams(user.id)
    if team_id not in owned:
        return redirect(url_for("index"))
    
    payment_state = Data.get_team_info(team_id)["paid"]
    if payment_state:
        return redirect(url_for("error_page"))
    
    back_url = request.host_url + url_for("team_creation_completed", team_id=team_id)
    print(back_url)
    payment_link = s_client.v1.payment_links.create({
        "line_items": [{"price": s_price_id, "quantity": 1}],
        "metadata": {"team_id": team_id, "user_id": user.id},
        "after_completion": {"type": "redirect", "redirect": {"url": back_url}}
    })
    
    return redirect(payment_link.url)


@app.route("/team_creation_completed")
def team_creation_completed():
    user = user_logout_status()
    if not user:
        return redirect(url_for("login"))
    
    owned_teams = Data.get_owned_teams(user.id)
    team_id = request.args.get("team_id")
    if team_id not in owned_teams:
        #print("Team nonexistent")
        return redirect(url_for("error_page"))
    
    team_info = Data.get_team_info(team_id)
    team_basic_info = Data.get_team_basic_info(team_id)
    
    if team_info is None or not team_info["paid"]:
        #print("Unpaid")
        return redirect(url_for("error_page"))

    if team_basic_info is None or team_basic_info["token"] is not None:
        #print("Token already set")
        return redirect(url_for("error_page"))
    
    token = secrets.token_hex(3)

    in_team = False
    if Data.get_enrolled_team(user.id) is not None:
        in_team = True

    _ = Data.set_team_token(team_id, token)
    code_s = EmailSender.send_code_email(user.email, team_basic_info, token)
    if not code_s:
        pass
    return render_template("team_creation_completed.html", token=token, team_info=team_basic_info, in_team=in_team)


@app.route("/team_information")
def team_information():
    user = user_logout_status()
    if not user:
        return redirect(url_for("login"))

    # Get the team ID
    team_id = request.args.get("team_id")
    if team_id is None:
        flash("No team was specified in the request!")
        return redirect(url_for("index"))

    # Handle no team -> We got kicked ?
    if team_id == "no_team":
        return redirect(url_for("runner_registration"))
    
    # Now get the team info from that
    team_info = Data.get_team_info(team_id)
    team_basic_info = Data.get_team_basic_info(team_id)

    if team_info is None or team_basic_info is None:
        flash("We couldn't get the information about that team!")
        return redirect(url_for("index"))

    if team_info.get("captain_name") is None:
        team_info["captain_name"] = "Unknown"
    team_info["token"] = team_basic_info.get("token")
    team_info["division"] = team_basic_info.get("division")
    team_info["team_name"] = team_basic_info.get("team_name")
    
    # Make sure we actually own the team OR are part of it OR are an admin
    owned_teams = Data.get_owned_teams(user.id)
    team_members = Data.get_members_list(team_id)
    is_admin = Data.is_user_admin(user.id)

    if team_id not in owned_teams and user.id not in team_members and not is_admin:
        flash("You don't have access to that team!")
        return redirect(url_for("index"))
    
    # If runner, only get own info
    combined_member_infos = []
    member_positions = []
    if team_id in owned_teams or is_admin:
        combined_member_infos = Data.get_members_info(team_members)
        member_positions = Data.get_positions_info(team_members)
    else:
        combined_member_infos = Data.get_members_info([user.id])
        member_positions = Data.get_positions_info([user.id])
    
    for i in combined_member_infos:
        for j in member_positions:
            if i["user_id"] == j["user_id"]:
                i["position"] = j["position"]

    combined_member_infos.sort(key=lambda x: x["position"])
    
    # If I'm a runner and I have unfinished info, finish it!
    # (All fields must be filled simultaneously, so just checking one is fine)
    for member_info in combined_member_infos:
        if member_info["user_id"] == user.id and member_info["first_name"] is None:
            flash("You have not filled in your Runner Info yet! Please go to your Profile and finish adding your information. You must do this before the deadline! ")
    # Get self info
    user_name = None
    users_data = Data.get_members_info([user.id])
    if len(users_data) > 0:
        self_info = users_data[0]
        if "first_name" in self_info:
            user_name = self_info["first_name"]
     
    is_captain = False
    if Data.get_captain_status(user.id) == 2:
        is_captain = True
    return render_template("team_information.html", user_email=user.email, user_name=user_name, team=team_info, is_captain=is_captain, members=combined_member_infos, genders_mapping=GENDERS_MAPPING)


@app.route("/reset_team_code")
def reset_team_code():
    user = user_logout_status()
    if not user:
        return redirect(url_for("login"))
    
    team_id = request.args.get("team_id")

    if Data.get_captain_status(user.id) != 2:
        return redirect(url_for("error_page"))
    
    if team_id is None or team_id not in Data.get_owned_teams(user.id):
        return redirect(url_for("error_page"))
    
    team_info = Data.get_team_basic_info(team_id)

    return render_template("reset_team_code.html", team_info=team_info)


@app.route("/reset_team_code", methods=["POST"])
def reset_team_code_post():
    user = user_logout_status()
    if not user:
        return redirect(url_for("login"))
    
    team_id = request.form.get("team_id")

    if Data.get_captain_status(user.id) != 2:
        return redirect(url_for("error_page"))
    
    if team_id is None or team_id not in Data.get_owned_teams(user.id):
        return redirect(url_for("error_page"))
    
    token = secrets.token_hex(3)

    _ = Data.set_team_token(team_id, token)
    return render_template("team_code_resetted.html", token=token, team_id=team_id)


@app.route("/teams")
def teams():
    user = user_logout_status()
    if not user:
        return redirect(url_for("login"))
    # Don't do it if I'm not a captain (we should not see this page)
    if Data.get_captain_status(user.id) != 2:
        return redirect(url_for("index"))

    teams = Data.get_owned_teams_info(user.id)
    return render_template("teams.html", username=user.email, teams=teams)


@app.route("/delete_from_team", methods=["POST"])
def delete_from_team():
    user = user_logout_status()
    if not user:
        return redirect(url_for("login"))

    # Only captains are allowed!
    if Data.get_captain_status(user.id) != 2:
        return redirect(url_for("index"))
    
    member_id = request.form.get("member_id")
    team_id = request.form.get("team_id")
    if not Data.has_authority_over_member(user.id, member_id, team_id):
        flash("We can't delete them (maybe they are already gone?)")
        return redirect(url_for("team_information", team_id=team_id))
    
    s = Data.unenroll_member_from_team(member_id, team_id)

    if s:
        flash("Member deleted successfully.")
    else:
        flash("Problem occured while deleting member.")
    return redirect(url_for("team_information", team_id=team_id))


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


@app.route("/move_team_member_up", methods=["POST"])
def move_team_member_up():
    user = user_logout_status()
    if not user:
        return redirect(url_for("login"))

    # Only captains are allowed!
    if Data.get_captain_status(user.id) != 2:
        return redirect(url_for("index"))
    
    member_id = request.form.get("member_id")
    team_id = request.form.get("team_id")

    if not Data.has_authority_over_member(user.id, member_id, team_id):
        flash("We don't have authority over this member")
        return redirect(url_for("team_information", team_id=team_id))
    
    s = Data.move_member_position_in_team(member_id, team_id, "up")
    if s:
        flash("Successfully changed member ordering.")
    else:
        flash("Unexpected failure while changing runner ordering.")
    return redirect(url_for("team_information", team_id=team_id))


@app.route("/event_registration_choice")
def event_registration_choice():
    user = user_logout_status()
    if not user:
        flash("Login or create an account before registering for this event!")
        return redirect(url_for("login"))
    
    return render_template("event_registration_choice.html")

# TODO: rate limit
# Password reset
@app.route("/forgot_password")
def forgot_password():
    user = user_logout_status()
    if user:
        return redirect(url_for("index"))
    
    return render_template("forgot_password.html")

@app.route("/forgot_password", methods=["POST"])
def forgot_password_post():

    user = user_logout_status()
    if user:
        return redirect(url_for("index"))
    
    email = request.form.get("email")

    if not Sanitization.verify_all_and_create_response(email, "ValidUname", "ValidPass01@"):
        return redirect(url_for("forgot_password"))
    # Check email
    email = email.lower()
    email_to = Data.get_member_by_email(email)
    if email_to is None:
        flash("No user exists with this email.")
        return redirect(url_for("forgot_password"))
    
    to_url = request.url_root + url_for("reset_my_password")
    emailed_link = None
    try:
        emailed_link = admin_client.auth.admin.generate_link({"type": "recovery", "email": email, "options": {"redirect_to": to_url}}).model_dump()#reset_password_for_email(email, {"redirect_to": request.url_root + url_for("reset_my_password")})
    except Exception as e:
        print("passforgot problem", e)
        flash("An error occured when sending password reset link. Please try again in a bit!")
        return redirect(url_for("forgot_password"))
    
    hashed_token = emailed_link["properties"]["hashed_token"]

    # Build the link yourself pointing to the verify endpoint
    link = (
        f"{to_url}?token={hashed_token}"
    )

    s = EmailSender.send_password_reset_email(email, link)
    if not s:
        flash("Sorry, something went wrong when sending the password reset request")
        return redirect(url_for("forgot_password"))
    
    return render_template("sent_password_reset.html")


@app.route("/reset_my_password")
def reset_my_password():
    user = user_logout_status()
    if user:
        return redirect(url_for("index"))
    
    token = request.args.get("token")

    if not token:
        flash("Password reset link was bad! Try with a different one?")
        return redirect(url_for("error_page"))

    if not Sanitization.verify_all_lists_and_create_response([], [], [token], [], [], []):
        return redirect(url_for("error_page"))

    # Check the token is valid!
    authresp = None
    try:
        authresp = auth_client.auth.verify_otp({"token_hash": token, "type": "recovery"})
    except Exception as e:
        pass
    if not authresp:
        flash("Invalid password reset link used.")
        return redirect(url_for("index"))
    
    # Get the user again
    user = user_logout_status(access_token=authresp.session.access_token)
    if not user:
        print("no user available")
        return redirect(url_for("error_page"))
    
    # Creaate a new token to validate the post
    emailed_link = None
    try:
        emailed_link = admin_client.auth.admin.generate_link({"type": "recovery", "email": user.email}).model_dump()
    except Exception as e:
        print("Unexpected problem with new token", e)
        return redirect(url_for("error_page"))
    
    hashed_token = emailed_link["properties"]["hashed_token"]

    return render_template("reset_my_password.html", token=hashed_token)

@app.route("/reset_my_password", methods=["POST"])
def reset_my_password_post():
    
    #user_id = user.id
    token = request.form.get("token")
    #auth_token = request.form.get("auth_token")
    password = request.form.get("password")

    if not token:
        return redirect(url_for("error_page"))

    #print(token, auth_token, password)
    if not Sanitization.verify_all_lists_and_create_response([], [], [token, password], [], [], []):
        #print("can't validate")
        return redirect(url_for("error_page"))
        
    authresp = None
    try:
        authresp = auth_client.auth.verify_otp({"token_hash": token, "type": "recovery"})
    except Exception as e:
        flash(str(e))
        return redirect(url_for("error_page"))
    
    if not authresp:
        flash("Invalid password reset link used!")
        return redirect(url_for("error_page"))
    
    auth_token = authresp.session.access_token
    user = user_logout_status(access_token=auth_token)
    if not user:
        flash("Invalid password reset link used!")
        return redirect(url_for("error_page"))
    
    success = False
    problem = None
    try:
        auth_client.auth.update_user({"password": password})
        success = True
    except Exception as e:
        problem = str(e)
    # Then logout
    admin_client.auth.admin.sign_out(auth_token)

    if success:
        flash("Successfully changed password")
    else:
        flash("There was a problem resetting your password: " + problem)
    return redirect(url_for("login"))
    

@app.route("/error_page")
def error_page():
    return render_template("error_page.html")

@app.route("/admin_panel")
def admin_panel():
    user = user_logout_status()
    if not user:
        return redirect(url_for("login"))

    is_admin = Data.is_user_admin(user.id)
    if not is_admin:
        return redirect(url_for("index"))

    teams = Data.get_all_teams_info()
    return render_template("teams.html", username="Awesome Eighthourrelay Admin", teams=teams)


@app.route("/rules")
def rules():
    return render_template("rules.html")


if __name__ == '__main__':
    app.run()