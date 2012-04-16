# Create your views here.
from django.http import HttpResponse
from redditarchiver.r.models import *

def index(request):
    return HttpResponse("Archiving %s Reddits and %s threads" %(Reddits.objects.count(),Threads.objects.count()))

def reddit(request, reddit_name):
    return HttpResponse("Reddit: %s" % reddit_name)