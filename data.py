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
    

    def team_name_exists(team_name: str) -> bool:
        try:
            response = Data.client.table("teams_public").select("team_name").eq("team_name", team_name).execute()
        except Exception as e:
            print("Error checking team name:", e)
            return False
        if response is None:
            return False
        return len(response.data) > 0


    # Creates a team and returns the ID. None if failure.
    def create_team(team_name: str, user_id: str, token: str, division: str, email: str, captain_name: str) -> str:
        try:
            if Data.team_name_exists(team_name):
                return None
            response = Data.client.table("teams").insert({"owner_id": user_id, "email": email, "paid": False, "captain_name": captain_name}).execute()
            if response is None:
                return None
            if len(response.data) < 1:
                return None
            team_id = str(response.data[0]["id"])
            _ = Data.client.table("teams_public").insert({"id": team_id, "owner_id": user_id, "team_name": team_name, "division": division, "encrypted_token": generate_password_hash(token)}).execute()
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
    

    def setup_user_position(user_id: str, team_id: str):
        try:
            members = Data.get_positions_info(Data.get_members_list(team_id))

            used_positions = []
            for m in members:
                used_positions.append(m["position"])
            position = 1
            while position in used_positions:
                position += 1 

            Data.client.table("runner_positions").insert({"user_id": user_id, "position": position}).execute()
        except Exception as e:
            print("Error occurred while setting up user position:", e)
            return False


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
            

    def get_positions_info(member_ids: list):

        member_infos = []
        for member_id in member_ids:
            try:
                response = Data.client.table("runner_positions").select("*").eq("user_id", member_id).execute()
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
            removed_position = Data.get_member_position_in_team(member_id)
            member_ids = Data.get_members_list(team_id)
            positions_info = Data.get_positions_info(member_ids)

            if removed_position != -1:
                for position_entry in positions_info:
                    if position_entry.get("user_id") == member_id:
                        continue
                    if position_entry.get("position", 0) > removed_position:
                        new_position = position_entry["position"] - 1
                        _ = Data.client.table("runner_positions").update({"position": new_position}).eq("user_id", position_entry["user_id"]).execute()

            _ = Data.client.table("runner_positions").delete().match({"user_id": member_id}).execute()
            _ = Data.client.table("enrollment").delete().match({"user_id": member_id, "team_id": team_id}).execute()

        except Exception as e:
            print("Unenrollment Problem:", e)
            return False
        return True
    

    def generate_new_team_token(team_id: str):
        token = secrets.token_urlsafe(3)
        try:
            _ = Data.client.table("teams_public").update({"encrypted_token": generate_password_hash(token)}).eq("id", team_id).execute()
        except Exception as e:
            print("Problem during generating new team token,", e)
            return None
        return token
    

    def create_transaction(team_id: str, user_id: str, product: str, quantity: int, amount_paid, currency: str, email: str) -> bool:
        transaction_id = str(uuid.uuid4())
        try:
            _ = Data.client.table("transactions").insert({"team_id": team_id, "user_id": user_id, "product": product, "quantity": quantity, "amount_paid": amount_paid, "transaction_id": transaction_id, "currency": currency, "transaction_email": email}).execute()
        except Exception as e:
            print("Transaction problem", e)
            return None
        return transaction_id
 
    
    def set_team_payment_status(team_id: str, payment: bool) -> bool:
        try:
            _ = Data.client.table("teams").update({"paid": payment}).eq("id", team_id).execute()
        except Exception as e:
            return False
        return True
    

    def get_member_position_in_team(member_id: str) -> int:
        try:
            response = Data.client.table("runner_positions").select("position").eq("user_id", member_id).execute()
        except Exception as e:
            print("Error occurred while retrieving member position:", e)
            return -1
        if response is None or len(response.data) < 1:
            return -1
        return response.data[0]["position"]
    

    def swap_team_positions(member_id_1: str, member_id_2: str) -> bool:
        try:
            position_1 = Data.get_member_position_in_team(member_id_1)
            position_2 = Data.get_member_position_in_team(member_id_2)
            if position_1 == -1 or position_2 == -1:
                return False
            Data.client.table("runner_positions").update({"position": position_2}).eq("user_id", member_id_1).execute()
            Data.client.table("runner_positions").update({"position": position_1}).eq("user_id", member_id_2).execute()
        except Exception as e:
            print("Error occurred while swapping team positions:", e)
            return False
        return True


    def move_member_position_in_team(member_id: str, team_id: str, direction: str) -> bool:
        try:
            target_position = Data.get_member_position_in_team(member_id)
            match direction:
                case "up":
                    target_position -= 1
                case "down":
                    target_position += 1
                case _:
                    return False
            if target_position < 1 or target_position > 8:
                return False
            positions_info = Data.get_positions_info(Data.get_members_list(team_id))
            for neighbouring_member in positions_info:
                if neighbouring_member["position"] == target_position:
                    Data.swap_team_positions(member_id, neighbouring_member["user_id"])
                    return True
        except Exception as e:
            print("Error occurred while moving member position:", e)
        return False
    

    def is_user_admin(member_id: str) -> bool:
        try:
            response = Data.client.table("admin").select("is_admin").eq("user_id", member_id).execute()
        except Exception as e:
            print("Error occurred while checking if user is admin:", e)
            return False
        if response is None or len(response.data) < 1:
            return False
        return response.data[0]["is_admin"]