from supabase import Client
from werkzeug.security import check_password_hash, generate_password_hash

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
    def create_team(team_name: str, user_id: str, token: str) -> str:
        try:
            response = Data.client.table("teams").insert({"name": team_name, "owner_id": user_id, "encrypted_token": generate_password_hash(token)}).execute()
        except Exception as e:
            print(e)
            return None
        if response is None:
            return None
        if len(response.data) < 1:
            return None
        return str(response.data[0]["id"])
    
    # Gets list of IDS of owned teams
    def get_owned_teams(user_id: str) -> list:
        try:
            response = Data.client.table("teams").select("id").eq("owner_id", user_id).execute()
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
            response = Data.client.table("teams").select("id,name").eq("owner_id", user_id).execute()
        except Exception as e:
            return []
        if response is None:
            return []
        if len(response.data) < 1:
            return []
        return response.data

    def get_team_info(team_id: str):
        try:
            response = Data.client.table("teams").select("id,name,owner_id").eq("id", team_id).execute()
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
            return None
        if response is None:
            return None
        if len(response.data) < 1:
            return None
        return [item["user_id"] for item in response.data]