from supabase import Client
from werkzeug.security import check_password_hash, generate_password_hash
import secrets

class Data:
    client: Client = None
    
    def initialize(client: Client):
        Data.client = client


    # Verify if token is right for the id
    def check_team_table_credentials(team_id: str, token: str) -> bool:
        response = Data.client.table("teams").select("*").eq("id", team_id).execute()

        if response is None:
            return False
        if len(response.data) < 1:
            return False
        encrypted_token = response.data[0]["encrypted_token"]
        if not check_password_hash(encrypted_token, token):
            return False
        return True
    

    # Creates a team and returns the ID. None if failure.
    def create_team(team_name: str, user_id: str, token: str, division: str, email: str) -> str:
        try:
            response = Data.client.table("teams").insert({"owner_id": user_id, "encrypted_token": generate_password_hash(token), "division": division, "email": email, "paid": False}).execute()
            if response is None:
                return None
            if len(response.data) < 1:
                return None
            team_id = str(response.data[0]["id"])
            _ = Data.client.table("teams_public").insert({"id": team_id, "owner_id": user_id, "team_name": team_name}).execute()
            return team_id
        except Exception as e:
            #print(e)
            return None
        
        
    # Gets list of IDS of owned teams
    def get_owned_teams(user_id: str) -> list:
        try:
            response = Data.client.table("teams_public").select("id").eq("owner_id", user_id).execute()
        except Exception as e:
            return []
        if response is None:
            return []
        if len(response.data) < 1:
            return []
        return [str(item["id"]) for item in response.data]
    

    # Gets list of info from teams
    def get_owned_teams_info(user_id: str) -> list:
        try: 
            response = Data.client.table("teams_public").select("id,team_name").eq("owner_id", user_id).execute()
        except Exception as e:
            return []
        if response is None:
            return []
        if len(response.data) < 1:
            return []
        return response.data


    def get_team_info(team_id: str):
        try:
            response = Data.client.table("teams").select("id,owner_id,division,email").eq("id", team_id).execute()
        except Exception as e:
            return None
        if response is None:
            return None
        if len(response.data) < 1:
            return None
        return response.data[0]
    

    def get_team_basic_info(team_id: str):
        try: 
            response = Data.client.table("teams_public").select("*").eq("id", team_id).execute()
        except Exception as e:
            return None
        if response is None:
            return None
        if len(response.data) < 1:
            return None
        return response.data[0]
    

    def enroll_user_in_team(user_id: str, team_id: str):
        try:
            response = Data.client.table("enrollment").insert({"user_id": user_id, "team_id": team_id}).execute()
        except Exception as e:
            return None
        if response is None:
            return None
        if len(response.data) < 1:
            return None
        return response.data[0]
    

    def get_members_list(team_id: str):
        try:
            response = Data.client.table("enrollment").select("user_id").eq("team_id", team_id).execute()
        except Exception as e:
            return []
        if response is None:
            return []
        if len(response.data) < 1:
            return []
        return [item["user_id"] for item in response.data]
    

    def get_enrolled_team(user_id: str):
        try:
            response = Data.client.table("enrollment").select("team_id").eq("user_id", user_id).execute()
        except Exception as e:
            return None
        if response is None:
            return None
        if len(response.data) < 1:
            return None
        return response.data[0]["team_id"]
        

    # Given a list of member_ids, give their info from the member_info table
    def get_members_info(member_ids: list):

        member_infos = []
        for member_id in member_ids:
            try:
                #print(member_id, "m_id")
                response = Data.client.table("runner_info").select("*").eq("user_id", member_id).execute()
                #print(response)
            except Exception as e:
                continue
            if response is None:
                continue
            if len(response.data) < 1:
                continue
            member_infos.append(response.data[0])
        return member_infos
            

    # Add a user to the member_info table
    def create_new_basic_runner(user_id: str, email: str, username: str, captain_id: str):
        try:
             response = Data.client.table("runner_info").insert({"user_id": user_id, "email": email, "captain_id": captain_id}).execute()
             _ = Data.client.table("runners_public").insert({"user_id": user_id, "username": username}).execute()
        except Exception as e:
            print(e)
            return None
        

    #def create_new_runner(user_id: str, email: str, username: str, first_name: str, last_name: str, gender: str, age: int, phone_number: str, emergency_phone: str):
    #    try:
    #         response = Data.client.table("runner_info").insert({"user_id": user_id, "email": email, "username": username, "first_name": first_name, "last_name": last_name, "gender": gender, "age": age, "phone_number": phone_number, "emergency_phone": emergency_phone}).execute()
    #    except Exception as e:
    #        return None
        

    def generate_new_team_token(team_id: str):
        token = secrets.token_urlsafe()
        try:
            response = Data.client.table("teams").update({"encrypted_token": generate_password_hash(token)}).eq("id", team_id).execute()
        except Exception as e:
            print("Problem during generating new team token,", e)
            return None
        return token