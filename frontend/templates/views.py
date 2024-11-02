from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from django.template.loader import render_to_string


def index(request):
    return render(request, 'index.html')


def scrape(request):
    if request.method == 'POST':
        url = request.POST.get('url')
        return render(request, 'scrape.html')
    
    return redirect('index')



def csrf_failure(request, reason=""):
    ctx = {'reason': reason}
    return HttpResponseForbidden(render_to_string('403_csrf.html', ctx))