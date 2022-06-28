from django.shortcuts import render

def landing(request):
    return render(
        request,
        'start_pages/start_pages_01.html'
    )
