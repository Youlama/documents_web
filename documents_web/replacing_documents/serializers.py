from rest_framework import serializers
from django.contrib.auth.models import User

from replacing_documents.models import Document, InstallDocumentRequest, DocumentInRequest


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["pk", "title", "prod_period", "replace_period", "docs", "logo_file_path", "number_length", "is_active"]


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]


class InstallDocumentRequestSerializer(serializers.ModelSerializer):
    client = ClientSerializer()

    class Meta:
        model = InstallDocumentRequest
        fields = ["pk", "status", "creation_datetime", "formation_datetime", "completion_datetime", "client", "manager",
                  "new_client_surname", "replace_reason"]


class PutInstallDocumentRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstallDocumentRequest
        fields = ["pk", "status", "creation_datetime", "formation_datetime", "completion_datetime", "client", "manager",
                  "new_client_surname", "replace_reason"]
        read_only_fields = ["pk", "status", "creation_datetime", "formation_datetime", "completion_datetime", "client", "manager"]


class ResolveInstallDocumentRequestSerializer(serializers.ModelSerializer):
    def validate(self, data):
        if data.get('status', '') not in (
                InstallDocumentRequest.RequestStatus.FORMED):
            raise serializers.ValidationError("invalid status")
        return data
    class Meta:
        model = InstallDocumentRequest
        fields = ["pk", "status", "creation_datetime", "formation_datetime", "completion_datetime", "client", "manager",
                  "new_client_surname", "replace_reason"]
        read_only_fields = ["pk", "creation_datetime", "formation_datetime", "completion_datetime", "client", "manager",
                  "new_client_surname", "replace_reason"]


class DocumentInRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentInRequest
        fields = ["replacing_request", "document", "comment", "new_document_number"]


class DocumentForRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["pk", "title", "prod_period", "logo_file_path"]


class RelatedSerializer(serializers.ModelSerializer):
    document = DocumentForRequestSerializer()
    class Meta:
        model = DocumentInRequest
        fields = ["document", "comment", "new_document_number"]


class FullInstallDocumentRequestSerializer(serializers.ModelSerializer):
    document_list = RelatedSerializer(source='documentinrequest_set', many=True)

    class Meta:
        model = InstallDocumentRequest
        fields = ["pk", "status", "creation_datetime", "formation_datetime", "completion_datetime", "client", "manager",
                  "new_client_surname", "replace_reason", "document_list"]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', '')
        )
        return user

    def update(self, instance, validated_data):
        instance.email = validated_data.get('email', instance.email)
        if 'password' in validated_data:
            instance.set_password(validated_data['password'])
        instance.save()
        return instance
