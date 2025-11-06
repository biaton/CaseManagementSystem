from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required 
from .models import OfficialDisplay
from .forms import OfficialDisplayForm
from django.contrib import messages
from .models import Hotline 
from .forms import HotlineForm 
from .models import BarangayInfo
from .forms import BarangayInfoForm
from .models import ExternalLink, Contact
from .forms import ExternalLinkForm, ContactForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from .models import LuponMember, LuponAvailability
from .forms import LuponMemberAddForm, LuponMemberUpdateForm


@login_required
def settings_hub_view(request):
    # I-rrender lang natin ang hub template na binigay mo
    return render(request, 'system_settings/hub.html')

@login_required # or @staff_required
def manage_officials_display_view(request):
    officials = OfficialDisplay.objects.all()
    
    if request.method == 'POST':
        form = OfficialDisplayForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Official has been added to the display list.")
            return redirect('system_settings:manage_officials_display')
    else:
        form = OfficialDisplayForm()

    context = {
        'form': form,
        'officials': officials,
    }
    return render(request, 'system_settings/manage_officials_display.html', context)

@login_required
def edit_official_display_view(request, pk):
    official_to_edit = get_object_or_404(OfficialDisplay, pk=pk)
    
    if request.method == 'POST':
        form = OfficialDisplayForm(request.POST, request.FILES, instance=official_to_edit)
        if form.is_valid():
            form.save()
            messages.success(request, f"Official '{official_to_edit.full_name}' has been updated.")
            return redirect('system_settings:manage_officials_display')
    else:
        form = OfficialDisplayForm(instance=official_to_edit)
    
    context = {
        'form': form,
        'official_to_edit': official_to_edit,
        'officials': OfficialDisplay.objects.all()
    }
    return render(request, 'system_settings/manage_officials_display.html', context)


@login_required
def delete_official_display_view(request, pk):
    if request.method == 'POST':
        official = get_object_or_404(OfficialDisplay, pk=pk)
        messages.success(request, f"Official '{official.full_name}' has been removed from the list.")
        official.delete()
    return redirect('system_settings:manage_officials_display')

@login_required
def edit_barangay_info_view(request):
    # Kunin ang unang-unang BarangayInfo object, o gumawa kung wala
    info, created = BarangayInfo.objects.get_or_create(pk=1)
    
    if request.method == 'POST':
        form = BarangayInfoForm(request.POST, request.FILES, instance=info)
        if form.is_valid():
            form.save()
            messages.success(request, "Barangay information has been updated.")
            return redirect('system_settings:edit_barangay_info')
    else:
        form = BarangayInfoForm(instance=info)
        
    context = {'form': form, 'info': info}
    return render(request, 'system_settings/edit_barangay_info.html', context)

# =======================================================================
# MANAGE HOTLINES (CRUD)
# =======================================================================
@login_required
def manage_hotlines_view(request):
    """
    Ipinapakita ang listahan ng hotlines at ang form para magdagdag ng bago.
    """
    hotlines = Hotline.objects.all()
    form = HotlineForm() # Form para sa pag-add

    if request.method == 'POST':
        form = HotlineForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "New hotline has been added.")
            return redirect('system_settings:manage_hotlines')
            
    context = {'form': form, 'hotlines': hotlines}
    return render(request, 'system_settings/manage_hotlines.html', context)

@login_required
def edit_hotline_view(request, pk):
    """
    View para i-edit ang isang specific na hotline.
    Ipinapakita rin ang listahan sa gilid.
    """
    hotline_to_edit = get_object_or_404(Hotline, pk=pk)
    
    if request.method == 'POST':
        form = HotlineForm(request.POST, instance=hotline_to_edit)
        if form.is_valid():
            form.save()
            messages.success(request, f"Hotline '{hotline_to_edit.name}' has been updated.")
            return redirect('system_settings:manage_hotlines')
    else:
        form = HotlineForm(instance=hotline_to_edit)

    context = {
        'form': form,
        'hotline_to_edit': hotline_to_edit,
        'hotlines': Hotline.objects.all()
    }
    return render(request, 'system_settings/manage_hotlines.html', context)

@login_required
def delete_hotline_view(request, pk):
    """
    View para i-delete ang isang hotline. Tumatanggap lang ng POST request.
    """
    if request.method == 'POST':
        hotline = get_object_or_404(Hotline, pk=pk)
        messages.success(request, f"Hotline '{hotline.name}' has been deleted.")
        hotline.delete()
    return redirect('system_settings:manage_hotlines')

# =======================================================================
# MANAGE CONTACTS (CRUD)
# =======================================================================
@login_required
def manage_contacts_view(request):
    contacts = Contact.objects.all().order_by('name')
    form = ContactForm()
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "New contact has been added.")
            return redirect('system_settings:manage_contacts')
    context = {'form': form, 'contacts': contacts}
    return render(request, 'system_settings/manage_contacts.html', context)

@login_required
def edit_contact_view(request, pk):
    contact_to_edit = get_object_or_404(Contact, pk=pk)
    if request.method == 'POST':
        form = ContactForm(request.POST, instance=contact_to_edit)
        if form.is_valid():
            form.save()
            messages.success(request, f"Contact '{contact_to_edit.name}' has been updated.")
            return redirect('system_settings:manage_contacts')
    else:
        form = ContactForm(instance=contact_to_edit)
    context = {
        'form': form,
        'contact_to_edit': contact_to_edit,
        'contacts': Contact.objects.all().order_by('name')
    }
    return render(request, 'system_settings/manage_contacts.html', context)

@login_required
def delete_contact_view(request, pk):
    if request.method == 'POST':
        contact = get_object_or_404(Contact, pk=pk)
        messages.success(request, f"Contact '{contact.name}' has been deleted.")
        contact.delete()
    return redirect('system_settings:manage_contacts')

# =======================================================================
# MANAGE LINKS (CRUD)
# =======================================================================
@login_required
def manage_links_view(request):
    links = ExternalLink.objects.all().order_by('name')
    form = ExternalLinkForm()
    if request.method == 'POST':
        form = ExternalLinkForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "New link has been added.")
            return redirect('system_settings:manage_links')
    context = {'form': form, 'links': links}
    return render(request, 'system_settings/manage_links.html', context)

@login_required
def edit_link_view(request, pk):
    link_to_edit = get_object_or_404(ExternalLink, pk=pk)
    if request.method == 'POST':
        form = ExternalLinkForm(request.POST, instance=link_to_edit)
        if form.is_valid():
            form.save()
            messages.success(request, f"Link '{link_to_edit.name}' has been updated.")
            return redirect('system_settings:manage_links')
    else:
        form = ExternalLinkForm(instance=link_to_edit)
    context = {
        'form': form,
        'link_to_edit': link_to_edit,
        'links': ExternalLink.objects.all().order_by('name')
    }
    return render(request, 'system_settings/manage_links.html', context)

@login_required
def delete_link_view(request, pk):
    if request.method == 'POST':
        link = get_object_or_404(ExternalLink, pk=pk)
        messages.success(request, f"Link '{link.name}' has been deleted.")
        link.delete()
    return redirect('system_settings:manage_links')

@login_required
def manage_lupon_schedule_view(request):
    # Ang POST logic ay para lang sa "Update Schedule" button
    if request.method == 'POST':
        # I-loop lahat ng members para i-check ang kanilang schedule
        for member in LuponMember.objects.all():
            for day_index in range(5):  # Monday (0) to Friday (4)
                # Ang pangalan ng checkbox ay ganito, e.g., "availability_1_0"
                checkbox_name = f'availability_{member.id}_{day_index}'
                
                # I-check kung ang checkbox na ito ay kasama sa sinubmit na data
                is_available = checkbox_name in request.POST
                
                # Gamitin ang update_or_create para maging efficient
                # Kung may record na, i-u-update lang. Kung wala, gagawa ng bago.
                LuponAvailability.objects.update_or_create(
                    lupon_member=member,
                    day_of_week=day_index,
                    defaults={'is_available': is_available}
                )
        
        messages.success(request, "Lupon schedule has been successfully updated.")
        return redirect('system_settings:manage_lupon_schedule')

    # Ang GET logic ay para ihanda ang data na ipapakita sa template
    add_form = LuponMemberAddForm()
    members = LuponMember.objects.all().order_by('full_name')
    
    # I-prepare natin ang data sa isang dictionary para mabilis i-access
    availability_map = { 
        (avail.lupon_member_id, avail.day_of_week): avail.is_available 
        for avail in LuponAvailability.objects.all()
    }

    # I-a-attach natin ang availability list sa bawat member object
    for member in members:
        # Gagawa tayo ng listahan ng True/False para sa bawat araw
        member.availability_list = [availability_map.get((member.id, i), False) for i in range(5)]
        
    context = {
        'lupon_members': members,
        'add_form': add_form,
        'edit_form': LuponMemberUpdateForm(),
    }
    return render(request, 'system_settings/manage_lupon_schedule.html', context)

@login_required
def add_lupon_member_view(request):
    """
    Ito ang nagpo-proseso ng form mula sa "Add New Member" modal.
    """
    if request.method == 'POST':
        form = LuponMemberAddForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "New Lupon Member has been successfully added.")
        else:
            # Pwede kang magdagdag ng mas specific na error message dito
            messages.error(request, "Error adding member. Please check the data provided.")
    return redirect('system_settings:manage_lupon_schedule')


@login_required
def edit_lupon_member_view(request, pk):
    """
    Ito ang nagpo-proseso ng form mula sa "Edit Member" modal.
    """
    member = get_object_or_404(LuponMember, pk=pk)
    if request.method == 'POST':
        # Manwal nating i-handle ang checkbox
        post_data = request.POST.copy()
        # Ang 'is_active' ay mase-send lang kung naka-check. Kung hindi, 'off' ang value.
        # So, i-che-check natin kung ang value ay 'on'.
        post_data['is_active'] = (request.POST.get('is_active') == 'on')

        form = LuponMemberUpdateForm(post_data, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, f"Details for {member.full_name} have been updated.")
        else:
            messages.error(request, "Error updating member.")
    return redirect('system_settings:manage_lupon_schedule')


@login_required
def delete_lupon_member_view(request, pk):
    """
    Ito ang nagpo-proseso ng "Delete Member" modal.
    """
    if request.method == 'POST':
        member = get_object_or_404(LuponMember, pk=pk)
        messages.success(request, f"Member '{member.full_name}' has been deleted from the list.")
        member.delete()
    return redirect('system_settings:manage_lupon_schedule')