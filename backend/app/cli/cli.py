import yaml
from backend.app.services.theme_service import load_theme, get_themes, validate_theme, add_theme
import typer
app=typer.Typer()
@app.command()
def show_themes():
    get_themes()
@app.command()

def valiate_theme(themes:str):
    result=validate_theme(themes)
    if result['status']==True:
        print(result['message'])
    else:
        print(result['message'])
        print(f"Valid themes: {result['valid_themes']}")
        print(f"Invalid themes: {result['invalid_themes']}")



@app.command()
def new_theme(theme:str):
    result=add_theme(theme)
    if result['status']==True:
        print(result['message'],result['theme'])
    else:
        print(result['message'])
if  __name__ == "__main__":
    app()