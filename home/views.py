from django.shortcuts import render


def index_view(request):
    """
    The main dashboard view.
    It renders the index.html template, which then uses
    template logic to include the correct dashboard partial
    based on the user's role.
    """
    return render(request, 'home/index.html')