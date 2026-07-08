import string
from flask import flash

class Sanitization:
    valid_phone_characters = string.digits + "-"
    valid_name_characters = string.ascii_letters + "'- "
    valid_characters = string.ascii_letters + string.digits + string.punctuation
    valid_username_characters = string.ascii_letters + string.digits + "._ " 

    def verify_name_characters(name: str) -> bool:
        if all(c in Sanitization.valid_name_characters for c in name):
            return True
        return False
    
    def verify_phone_characters(phone: str) -> bool:
        if all(c in Sanitization.valid_phone_characters for c in phone):
            return True
        return False
    
    def verify_email_characters(email: str) -> bool:
        #  verify correctness
        # https://stackoverflow.com/questions/1323364/in-python-how-to-check-if-a-string-only-contains-certain-characters
        if all(c in Sanitization.valid_characters for c in email):
            return True
        return False
       
    def verify_username_characters(username: str) -> bool:
        if all(c in Sanitization.valid_username_characters for c in username):
            return True
        return False
    
    def verify_password_characters(password: str) -> bool:
        if all(c in Sanitization.valid_characters for c in password):
            return True
        return False
    
    def verify_name_length(name: str) -> bool:
        if name is not None and len(name) > 0 and len(name) < 129:
            return True
        return False
    
    def verify_phone_length(phone: str) -> bool:
        if phone is not None and len(phone) < 15 and len(phone) > 9:
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
    
    def verify_next_page(next_page: str) -> str:
        valid_next_pages = ("captain_registration","runner_registration")
        if next_page in valid_next_pages:
            return next_page
        return "index"

    def verify_all_and_create_response(email: str, username: str, password: str) -> bool:
        # Verify lengths
        if not Sanitization.verify_email_length(email):
            flash("Bad email length.")
            return False
        if not Sanitization.verify_username_length(username):
            flash("Username must be 3-16 characters long.")
            return False
        if not Sanitization.verify_password_length(password):
            flash("Password must be 8-64 characters long.")
            return False
        
        
        # Verify characters
        if not Sanitization.verify_email_characters(email):
            flash("Email contains invalid characters.")
            return False
        if not Sanitization.verify_username_characters(username):
            flash("Username contains invalid characters.")
            return False
        if not Sanitization.verify_password_characters(password):
            flash("Password contains invalid characters")
            return False

        # Verify email
        if not Sanitization.verify_email_correctness(email):
            flash("Invalid email.")
            return False
        return True

    def verify_all_lists_and_create_response(emails: list[str], usernames: list[str], passwords: list[str], phones: list[str], names: list[str], genders: list[str]):
        for email in emails:
            if not Sanitization.verify_email_length(email):
                flash("Bad email length.")
                return False
            if not Sanitization.verify_email_characters(email):
                flash("Email has invalid characters.")
                return False
            if not Sanitization.verify_email_correctness(email):
                flash("Invalid email.")
                return False
        
        for username in usernames:
            if not Sanitization.verify_username_length(username):
                flash("Username must be 3-16 characters long.")
                return False
            if not Sanitization.verify_username_characters(username):
                flash("Username contains invalid characters.")
                return False
            
        for password in passwords:
            if not Sanitization.verify_password_length(password):
                flash("Password must be 8-64 characters long.")
                return False
            if not Sanitization.verify_password_characters(password):
                flash("Password contains invalid characters")
                return False
            
        for phone in phones:
            if not Sanitization.verify_phone_length(phone):
                flash("Phone number should be 10-15 characters long")
                return False
            if not Sanitization.verify_phone_characters(phone):
                flash("Phone number contains invalid characters")
                return False
            
        for name in names:
            if not Sanitization.verify_name_length(name):
                flash("Please ensure your name is between 1-127 characters long(shorten if needed)")
                return False
            if not Sanitization.verify_name_characters(name):
                flash("Name contains invalid characters.")
                return False
            
        for gender in genders:
            if not Sanitization.verify_name_length(gender):
                flash("Please ensure your gender is between 1-127 characters")
                return False
            if not gender in ("male", "female", "non-binary"):
                flash("Please ensure your gender is either: male, female, or non-binary.")
                return False
            
        return True