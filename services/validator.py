import re

SUPPORTED_LANGUAGES=["hi", "bn_IN", "gu", "kn", "ml", "mr", "pa", "ta", "te", "ur","en", "en_IN", "en_US", "en_GB"]

def validate_template(template : dict) -> list:
    errors = []

    name = template.get("name","")
    category = template.get("category","")
    langugae = template.get("language","")

    if not re.match(r"^[a-z0-9_]+$", name) or len(name) > 512:
        errors.append("Name must be lowercase, digits, underscores only, and max 512 chars.")

    if category not in ["MARKETING", "UTILITY", "AUTHENTICATION"]:
        errors.append(f"Invalid Category : {category}")

    if langugae not in SUPPORTED_LANGUAGES:
        errors.append(f"Unsupported Language : {langugae}")

    components = template.get("components",[])
    has_body = False

    for comp in components:
        comp_type = comp.get("type")

        if comp_type == "BODY":
            has_body = True
            text = comp.get("text","")

            if not text:
                errors.append("BODY text cannot be empty.")

            stripped_text = text.strip()
            clean_text = re.sub(r'^[^\w\{]+|[^\w\}]+$', '', stripped_text)
            if clean_text.startswith("{{") or clean_text.endswith("}}"):
                errors.append("BODY must not start or end with a variable (even if followed by punctuation).")

            vars_found = re.findall(r'\{\{(.+?)\}\}', text)

            is_positional = any(v.isdigit() for v in vars_found)
            is_named = any(not v.isdigit() for v in vars_found)

            if is_positional and is_named:
                errors.append("BODY cannot mix positional {{1}} and named {{var}} variables.")

            if is_positional:
                positions = [int(v) for v in vars_found if v.isdigit()]
                if positions:
                    if sorted(positions) != list(range(1,len(positions)+1)):
                        errors.append("Positional variables must start at 1 and be sequential with no gaps or duplicates.")
            
            if is_named:
                for v in vars_found:
                    if not re.match(r'^[a-z_]+$',v):
                        errors.append("Named variables must be lowercase and have no special characters.")

            if len(text) > 1024:
                errors.append("BODY text cannot exceed 1024 characters")

        elif comp_type == "HEADER":
            format_type = comp.get("format","")

            if category == "AUTHENTICATION" and format_type != "TEXT":
                errors.append("AUTHENTICATION templates cannot have media headers.")

            if format_type == "TEXT":
                header_text = comp.get("text","")
                if len(header_text) > 60:
                    errors.append("HEADER text cannot exceed 60 characters.")

                headers_vars = re.findall(r'\{\{(.+?)\}\}', header_text)
                if len(headers_vars) > 1 :
                    errors.append("TEXT HEADER can have at most 1 variable.")

            else:
                example = comp.get("example",{})
                if "header_handle" not in example:
                    errors.append(f"HEADER of format {format_type} must have 'example.header_handle'. ")
            
        elif comp_type == "FOOTER":
            footer_text = comp.get("text", "")
            if len(footer_text) > 60:
                errors.append("FOOTER text cannot exceed 60 characters.")
            
            if re.search(r'\{\{.+?\}\}', footer_text):
                errors.append("FOOTER cannot contain variables.")
            
        elif comp_type == "BUTTONS":
            buttons = comp.get("buttons", [])
            if len(buttons) > 10:
                errors.append("Cannot have more than 10 buttons total.")
                
            url_count = 0
            phone_count = 0
            otp_copy_count = 0
            
            for btn in buttons:
                btn_type = btn.get("type", "")
                
                if btn_type == "QUICK_REPLY":
                    if len(btn.get("text", "")) > 25:
                        errors.append("QUICK_REPLY text cannot exceed 25 characters.")
                        
                elif btn_type == "URL":
                    url_count += 1
                    if category == "AUTHENTICATION":
                        errors.append("AUTHENTICATION templates cannot have URL buttons.")
                    
                    url_val = btn.get("url", "")
                    if len(url_val) > 2000:
                        errors.append("URL cannot exceed 2000 characters.")
                    
                    url_vars = re.findall(r'\{\{(.+?)\}\}', url_val)
                    if len(url_vars) > 1:
                        errors.append("URL button can have at most 1 variable.")
                    elif len(url_vars) == 1 and not url_val.strip().endswith("}}"):
                        errors.append("URL button variable must be placed exactly at the end of the URL.")

                elif btn_type == "PHONE_NUMBER":
                    phone_count += 1
                    phone_val = btn.get("phone_number", btn.get("value", ""))
                    if len(phone_val) > 20:
                        errors.append("PHONE_NUMBER value cannot exceed 20 characters.")
                        
                elif btn_type in ["OTP", "COPY_CODE"]:
                    otp_copy_count += 1

            if url_count > 2:
                errors.append("Cannot have more than 2 URL buttons.")
            if phone_count > 1:
                errors.append("Cannot have more than 1 PHONE_NUMBER button.")
            if otp_copy_count > 1:
                errors.append("Cannot have more than 1 OTP or COPY_CODE button.")
            
        elif comp_type == "CAROUSEL":
            cards = comp.get("cards", [])
            if not (2 <= len(cards) <= 10):
                errors.append("CAROUSEL must have between 2 and 10 cards.")
                
            first_header_format = None
            for i, card in enumerate(cards):
                card_comps = card.get("components", [])
                
                header = next((c for c in card_comps if c.get("type") == "HEADER"), None)
                if not header:
                    errors.append(f"Card {i+1} is missing a HEADER.")
                else:
                    h_fmt = header.get("format", "")
                    if h_fmt not in ["IMAGE", "VIDEO"]:
                        errors.append(f"Card {i+1} HEADER must be IMAGE or VIDEO.")
                    
                    if first_header_format is None:
                        first_header_format = h_fmt
                    elif h_fmt != first_header_format:
                        errors.append("All Carousel cards must have the exact same header format.")
                        
                body = next((c for c in card_comps if c.get("type") == "BODY"), None)
                if body:
                    b_text = body.get("text", "")
                    if len(b_text) > 160:
                        errors.append(f"Card {i+1} BODY cannot exceed 160 characters.")
                    
                    num_vars = len(re.findall(r'\{\{(.+?)\}\}', b_text))
                    num_words = len(b_text.split())
                    if num_vars > 0 and num_words < (2 * num_vars + 1):
                        errors.append(f"Card {i+1} BODY needs at least {2*num_vars + 1} words for {num_vars} variables.")

                btn_comp = next((c for c in card_comps if c.get("type") == "BUTTONS"), None)
                if btn_comp:
                    btn_list = btn_comp.get("buttons", [])
                    if not (1 <= len(btn_list) <= 2):
                        errors.append(f"Card {i+1} must have 1-2 buttons.")

    if not has_body:
        errors.append("Template must have a BODY component.")

    all_text = " ".join([c.get("text", "") for c in components if "text" in c])
    letters = [c for c in all_text if c.isalpha()]
    if letters:
        upper_count = sum(1 for c in letters if c.isupper())
        if (upper_count / len(letters)) > 0.6:
            errors.append("Template rejected: Over 60% uppercase letters (Spam).")
            
    if re.search(r'[!?]{5,}', all_text):
        errors.append("Template rejected: Too many repeated punctuation marks (Spam).")
        
    all_text_lower = all_text.lower()
    if "password" in all_text_lower or "ssn" in all_text_lower:
        errors.append("Template rejected: Contains sensitive words (password, ssn).")

    return errors
