from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Resource, ResourceCategory
from .forms import ResourceForm

@login_required
def resource_list_view(request):
    resources = Resource.objects.all()
    categories = ResourceCategory.objects.all()

    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        resources = resources.filter(category_id=category_id)

    # Filter by type
    resource_type = request.GET.get('type')
    if resource_type:
        resources = resources.filter(resource_type=resource_type)

    # Search
    search_query = request.GET.get('search')
    if search_query:
        resources = resources.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(tags__icontains=search_query)
        )

    return render(request, 'resources/resource_list.html', {
        'resources': resources,
        'categories': categories,
        'selected_category': category_id,
        'selected_type': resource_type,
        'search_query': search_query
    })

@login_required
def resource_detail_view(request, resource_id):
    resource = get_object_or_404(Resource, id=resource_id)
    return render(request, 'resources/resource_detail.html', {'resource': resource})

@login_required
def resource_create_view(request):
    if request.user.role not in ['admin', 'counselor']:
        messages.error(request, 'You do not have permission to create resources.')
        return redirect('resource_list')

    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.created_by = request.user

            # Handle file attachment
            if 'attachment' in request.FILES:
                attachment = request.FILES['attachment']
                resource.attachment = attachment
                resource.attachment_name = attachment.name
                resource.attachment_size = attachment.size

            resource.save()
            messages.success(request, 'Resource created successfully!')
            return redirect('resource_detail', resource_id=resource.id)
    else:
        form = ResourceForm()

    return render(request, 'resources/resource_form.html', {
        'form': form,
        'title': 'Create Resource',
        'submit_text': 'Create Resource'
    })

@login_required
def resource_edit_view(request, resource_id):
    resource = get_object_or_404(Resource, id=resource_id)

    # Only allow editing if user is admin or created the resource
    if request.user.role != 'admin' and resource.created_by != request.user:
        messages.error(request, 'You do not have permission to edit this resource.')
        return redirect('resource_detail', resource_id=resource.id)

    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES, instance=resource)
        if form.is_valid():
            updated_resource = form.save(commit=False)

            # Handle attachment deletion
            if request.POST.get('delete_attachment') == '1':
                # Delete the old file from storage
                if updated_resource.attachment:
                    updated_resource.attachment.delete(save=False)
                updated_resource.attachment = None
                updated_resource.attachment_name = None
                updated_resource.attachment_size = None
            # Handle file attachment update (only if not deleting and new file uploaded)
            elif 'attachment' in request.FILES:
                # Delete old file if it exists
                if updated_resource.attachment:
                    updated_resource.attachment.delete(save=False)
                attachment = request.FILES['attachment']
                updated_resource.attachment = attachment
                updated_resource.attachment_name = attachment.name
                updated_resource.attachment_size = attachment.size

            updated_resource.save()
            messages.success(request, 'Resource updated successfully!')
            return redirect('resource_detail', resource_id=resource.id)
    else:
        form = ResourceForm(instance=resource)

    return render(request, 'resources/resource_form.html', {
        'form': form,
        'title': 'Edit Resource',
        'submit_text': 'Update Resource'
    })

@login_required
def resource_delete_view(request, resource_id):
    resource = get_object_or_404(Resource, id=resource_id)

    # Only allow deletion if user is admin or created the resource
    if request.user.role != 'admin' and resource.created_by != request.user:
        messages.error(request, 'You do not have permission to delete this resource.')
        return redirect('resource_detail', resource_id=resource.id)

    if request.method == 'POST':
        resource.delete()
        messages.success(request, 'Resource deleted successfully!')
        return redirect('resource_list')

    return render(request, 'resources/resource_confirm_delete.html', {'resource': resource})
