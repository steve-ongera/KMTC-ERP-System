from .models import AcademicYear

def get_current_academic_year():
    return AcademicYear.objects.filter(is_current=True).first()
