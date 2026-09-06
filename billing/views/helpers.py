from school_config.models import School
def get_current_school():
    school=School.objects.first()
    if not school: raise RuntimeError("School settings must be configured first.")
    return school
