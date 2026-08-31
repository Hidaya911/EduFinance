from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import SchoolForm
from .models import School


@login_required
def school_settings(request):

    school = (
        School.objects
        .first()
    )

    if request.method == "POST":

        form = SchoolForm(
            request.POST,
            request.FILES,
            instance=school,
        )

        if form.is_valid():

            school = form.save()

            messages.success(
                request,
                (
                    "School configuration "
                    "was saved successfully."
                ),
            )

            return redirect(
                "school_config:school_settings"
            )

    else:

        form = SchoolForm(
            instance=school,
        )

    return render(
        request,
        (
            "school_config/"
            "school_settings.html"
        ),
        {
            "form":
                form,

            "school":
                school,

            "is_configured":
                school is not None,
        },
    )