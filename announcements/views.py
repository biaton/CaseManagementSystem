from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required # Use your @staff_required later
from .models import Announcement
from .forms import AnnouncementForm

@login_required
def announcement_list_view(request):
    announcements = Announcement.objects.all()
    context = {'announcements': announcements}
    return render(request, 'announcements/announcement_list.html', context)

@login_required
def create_announcement_view(request):
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.author = request.user
            announcement.save()
            messages.success(request, "Announcement has been successfully published.")
            return redirect('announcements:list')
    else:
        form = AnnouncementForm()
    
    context = {'form': form}
    # Ito ang template na binigay mo
    return render(request, 'announcements/create_announcement.html', context)

@login_required
def edit_announcement_view(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    
    if request.method == 'POST':
        # I-pass ang 'instance' para i-update ang existing object
        form = AnnouncementForm(request.POST, request.FILES, instance=announcement)
        if form.is_valid():
            form.save()
            messages.success(request, f"Announcement '{announcement.title}' has been updated successfully.")
            return redirect('announcements:list')
    else:
        # I-populate ang form ng existing data
        form = AnnouncementForm(instance=announcement)
    
    context = {
        'form': form,
        'announcement': announcement # Para sa title at iba pang display
    }
    # Gagamitin natin ulit ang create template
    return render(request, 'announcements/create_announcement.html', context)

@login_required
def delete_announcement_view(request, pk):
    if request.method == 'POST':
        announcement = get_object_or_404(Announcement, pk=pk)
        title = announcement.title
        announcement.delete()
        messages.success(request, f"Announcement '{title}' has been successfully deleted.")
    else:
        messages.error(request, "Invalid request method.")
    
    return redirect('announcements:list')