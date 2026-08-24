import yaml
def load_theme():
    with open("backend\\app\\config\\themes.yaml", "r") as f:
        data = yaml.safe_load(f)
    return data
def get_themes():
    data = load_theme()
    print(len(data['themes']))
    for theme in range(0, len(data['themes'])):
        print(f"{theme+1}. {data['themes'][theme]}")
    return data['themes']

get_themes()

def validate_theme(user_themes:str):
    data = load_theme()
    test_themes = user_themes.split(",")
    valid_themes=[]
    invalid_themes=[]



    """
    for test_theme in test_themes:
        if test_theme in data['themes']:
            valid_themes.append(test_theme)
        else:
            invalid_themes.append(test_theme)
    """
    """
    if count == 0:
        return {"status":True, "valid_themes":valid_themes,"message":"All themes are valid."}
    else:
        return {"status":False, "valid_themes":valid_themes, "invalid_themes":invalid_themes,
                "message":f"check the theme section for all themes"}
    """
    if invalid_themes==[]:
        return {"status":True, "valid_themes":valid_themes,"message":"All themes are valid."}
    else:
        return {"status":False, "valid_themes":valid_themes, "invalid_themes":invalid_themes,
                "message":f"check the theme section for all themes"}
def add_theme(new_theme:str):
    data=load_theme()
    if new_theme not in data['themes']:
        data['themes'].append(new_theme)
        with open("backend\\app\\config\\themes.yaml", "w") as f:
            yaml.dump(data, f)
        print(f"Theme '{new_theme}' added successfully.")
        return {"status":True,"theme":new_theme, "message":f"Theme  added successfully."}
    else:
        print(f"Theme '{new_theme}' already exists.")
        return {"status":False, "theme":new_theme, "message":f" theme already exists."}
    