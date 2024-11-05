from django.contrib import admin

from replacing_documents.models import Document, DocumentInRequest, InstallDocumentRequest

admin.site.register(Document)
admin.site.register(InstallDocumentRequest)
admin.site.register(DocumentInRequest)
