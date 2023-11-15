from PIL import Image

from django.template import Library
from django.conf import settings
register = Library()


@register.filter
def pdf_and_docx_to_png(file_path):
    """Converts a PDF or DOCX file to a PNG image.

    Args:
        file_path: The path to the PDF or DOCX file.

    Returns:
        A PIL Image object.
    """
    if file_path.endswith('.pdf'):
        image = Image.open(settings.BASE_DIR / file_path)
        image = image.convert('RGB')
        return image
    elif file_path.endswith('.docx'):
        from docx import Document
        document = Document(file_path)
        image = Image.open(document.part.blob)
        image = image.convert('RGB')
        return image
    else:
        raise Exception('Unsupported file type.')
