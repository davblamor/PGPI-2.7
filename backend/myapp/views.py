from django.shortcuts import render
from django.http import HttpRequest, HttpResponse



def index(request: HttpRequest) -> HttpResponse:
    return HttpResponse("PGPI Grupo 2.7")
# Create your views here.
