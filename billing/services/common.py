from uuid import uuid4
from django.utils import timezone

def generate_document_number(prefix):
    safe=(prefix or "DOC").strip().upper()
    return f"{safe}-{timezone.now().strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"
