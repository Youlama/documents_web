from django.db import models
from django.contrib.auth.models import User


class Document(models.Model):
    title = models.CharField(max_length=255, unique=True, blank=False, null=False)
    prod_period = models.IntegerField()
    replace_period = models.TextField()
    docs = models.TextField()
    logo_file_path = models.CharField(max_length=255, null=True, default="")
    number_length = models.IntegerField(default=0)
    def __str__(self):
        return self.title

    class Meta:
        db_table = 'documents'


class InstallDocumentRequest(models.Model):
    class RequestStatus(models.TextChoices):
        DRAFT = "DRAFT"
        DELETED = "DELETED"
        FORMED = "FORMED"
        COMPLETED = "COMPLETED"
        REJECTED = "REJECTED"

    status = models.CharField(
        max_length=10,
        choices=RequestStatus.choices,
        default=RequestStatus.DRAFT,
    )

    creation_datetime = models.DateTimeField(auto_now_add=True)
    formation_datetime = models.DateTimeField(blank=True, null=True)
    completion_datetime = models.DateTimeField(blank=True, null=True)
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_requests')
    manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name='managed_requests', blank=True, null=True)
    new_client_surname = models.TextField(blank=True, null=True, default='Пятигорская')
    replace_reason = models.TextField(blank=True, null=True, default='Вступление в брак')

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'install_document_requests'


class DocumentInRequest(models.Model):
    replacing_request = models.ForeignKey(InstallDocumentRequest, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    comment = models.TextField(blank=True, null=True, default='')
    new_document_number = models.BigIntegerField(default=0)
    def __str__(self):
        return f"{self.replacing_request}-{self.document_id}"

    class Meta:
        db_table = 'document_in_request'
        unique_together = ('replacing_request', 'document'),
