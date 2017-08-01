from django.shortcuts import render

from kinksorter_app.models import Storage
# Create your views here.


def index(request):
    return render(request, 'index.html', {})
