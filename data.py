from supabase import Client
from werkzeug.security import check_password_hash, generate_password_hash
import secrets
import uuid

class Data:
    client: Client = None
    
    def initialize(client: Client):
        Data.client = client


    # Verify if token is right for the id
    def check_team_table_credentials(team_id: str, token: str) -> bool:
        response = Data.client.table("teams_public").select("encrypted_token").eq("id", team_id).execute()

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
            response = Data.client.table("teams").insert({"owner_id": user_id, "division": division, "email": email, "paid": False}).execute()
            if response is None:
                return None
            if len(response.data) < 1:
                return None
            team_id = str(response.data[0]["id"])
            _ = Data.client.table("teams_public").insert({"id": team_id, "owner_id": user_id, "team_name": team_name,  "encrypted_token": generate_password_hash(token)}).execute()
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
    

    def get_all_teams_info():

        try:
            response = Data.client.table("teams_public").select("*").execute()
        except Exception as e:
            return []
        if response is None:
            return []
        if len(response.data) < 1:
            return []
        return response.data


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
            response = Data.client.table("teams").select("*").eq("id", team_id).execute()
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
            print(e)
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
    def create_new_basic_runner(user_id: str, email: str) -> bool:
        try:
             s = Data.client.table("runner_info").insert({"user_id": user_id, "email": email}).execute()
             if not s:
                 return False
        except Exception as e:
            print(e)
            return False
        return True
        

    def has_authority_over_member(user_id: str, target_id: str, team_id: str) -> bool:
        if target_id is None or team_id is None:
            return False
    
        # Then check if the member is in a team we own
        user_owned_teams = Data.get_owned_teams(user_id)
        members = Data.get_members_list(team_id)
        if team_id not in user_owned_teams or target_id not in members:
            return False
        
        return True


    # Update user info with the provided dict
    def update_runner_info(user_id: str, user_info: dict) -> bool:
        try:
            _ = Data.client.table("runner_info").update(user_info).eq("user_id", user_id).execute()
        except Exception as e:
            return False
        return True
    

    def unenroll_member_from_team(member_id: str, team_id: str) -> bool:
        try:
            _ = Data.client.table("enrollment").delete().match({"user_id": member_id, "team_id": team_id}).execute()
            #print(_)
        except Exception as e:
            print("Unenrollment Problem:", e)
            return False
        return True
    

    def generate_new_team_token(team_id: str):
        token = secrets.token_urlsafe()
        try:
            _ = Data.client.table("teams_public").update({"encrypted_token": generate_password_hash(token)}).eq("id", team_id).execute()
        except Exception as e:
            print("Problem during generating new team token,", e)
            return None
        return token
    

    def create_transaction(team_id: str, user_id: str, product: str, quantity: int, amount_paid, currency: str, email: str) -> bool:
        try:
            _ = Data.client.table("transactions").insert({"team_id": team_id, "user_id": user_id, "product": product, "quantity": quantity, "amount_paid": amount_paid, "transaction_id": str(uuid.uuid4()), "currency": currency, "transaction_email": email}).execute()
        except Exception as e:
            print("Transaction problem", e)
            return False
        return True
    

    def set_team_payment_status(team_id: str, payment: bool) -> bool:
        try:
            _ = Data.client.table("teams").update({"paid": payment}).eq("id", team_id).execute()
        except Exception as e:
            return False
        return True