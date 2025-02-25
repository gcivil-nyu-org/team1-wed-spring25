import requests
from django.shortcuts import render
from django.http import HttpResponse

from django.views import generic

from users.models import Provider


# Create your views here.
def login(request):
    return render(request, 'users/login.html')


class ProviderDetailView(generic.DetailView):
    model = Provider
    template_name = "profile/provider_detail.html" 
    context_object_name = "provider"
    

class ProviderListView(generic.ListView):
    model = Provider
    template_name = "profile/provider_list.html" 
    context_object_name = "all_provider"

    def get_queryset(self):
        API_URL = 'https://data.cityofnewyork.us/resource/fgq8-am2v.json'
        response = requests.get(API_URL)
        if response.status_code == 200:
            all_data = response.json()  

            for data in all_data:
                provider_name = data.get("organization_name", "").strip()

                if not provider_name:
                    continue  # skip invalid data

                # check whether provider exists
                provider, created = Provider.objects.get_or_create(name=provider_name, defaults={
                    "phone_num": data.get("phone1", "0000000000"),
                    "address": data.get("address1", "Unknown"),
                    "open_time": data.get("open_time", "N/A"),
                    "provider_desc": data.get("provider_description", "No description"),
                    "website": data.get("website", ""),
                })

        else:
            print(f"Call API failed, the status code is: {response.status_code}")

        return Provider.objects.all()