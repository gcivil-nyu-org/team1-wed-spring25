import json
import os
from django.conf import settings

def intro_content(request):
    try:
        # Load the intros.json file
        json_path = os.path.join(settings.BASE_DIR, "static", "intros.json")
        with open(json_path, "r") as f:
            intros = json.load(f)

        # Match current URL name to the correct intro
        url_name = request.resolver_match.url_name if request.resolver_match else None
        intro = intros.get(url_name)
        return {"intro": intro}
    except Exception:
        return {"intro": None}