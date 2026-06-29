import string
from flask import flash

class Util:
    valid_characters = string.ascii_letters + string.digits + string.punctuation
    valid_username_characters = string.ascii_letters + string.digits + "._ " 

    def verify_email_characters(email: str) -> bool:
        #  verify correctness
        # https://stackoverflow.com/questions/1323364/in-python-how-to-check-if-a-string-only-contains-certain-characters
        if all(c in Util.valid_characters for c in email):
            return True
        return False
       
    def verify_username_characters(username: str) -> bool:
        if all(c in Util.valid_username_characters for c in username):
            return True
        return False
    
    def verify_password_characters(password: str) -> bool:
        if all(c in Util.valid_characters for c in password):
            return True
        return False
    
    def verify_email_length(email: str) -> bool:
        if email is not None and len(email) < 321 and len(email) > 0:
            return True
        return False
    
    def verify_password_length(password: str) -> bool:
        if password is not None and len(password) < 65 and len(password) > 7:
            return True
        return False
    
    def verify_username_length(username: str) -> bool:
        if username is not None and len(username) < 17 and len(username) > 2:
            return True
        return False
    
    def verify_email_correctness(email: str) -> bool:
        if email.count("@") == 1:
            if email.split("@")[1].count(".") == 1:
                return True
        return False 
    
    def verify_all_and_create_response(email: str, username: str, password: str) -> bool:
        # Verify lengths
        if not Util.verify_email_length(email):
            flash("Bad email length.")
            return False
        if not Util.verify_username_length(username):
            flash("Username must be 3-16 characters long.")
            return False
        if not Util.verify_password_length(password):
            flash("Password must be 8-64 characters long.")
            return False
        
        
        # Verify characters
        if not Util.verify_email_characters(email):
            flash("Email contains invalid characters.")
            return False
        if not Util.verify_username_characters(username):
            flash("Username contains invalid characters.")
            return False
        if not Util.verify_password_characters(password):
            flash("Password contains invalid characters")
            return False

        # Verify email
        if not Util.verify_email_correctness(email):
            flash("Invalid email.")
            return False
        return True

