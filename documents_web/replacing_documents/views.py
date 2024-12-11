import os

from datetime import datetime
from dateutil.parser import parse
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
import random

from documents_web import settings
from replacing_documents.minio import MinioStorage
from replacing_documents.serializers import *

SINGLETON_USER = User(id=1, username="admin")
SINGLETON_MANAGER = User(id=2, username="manager")

@api_view(['GET'])
def get_document_list(request):
    """
    Получение списка документов
    """
    document_title = request.query_params.get("document_title", "")
    document_list = Document.objects.filter(title__istartswith=document_title, is_active=True)
    req = InstallDocumentRequest.objects.filter(client_id=SINGLETON_USER.id,
                                                status=InstallDocumentRequest.RequestStatus.DRAFT).first()
    items_in_cart = 0
    if req is not None:
        items_in_cart = DocumentInRequest.objects.filter(replacing_request_id=req.id).count()
    serializer = DocumentSerializer(document_list, many=True)
    return Response({
                          "document_list": serializer.data,
                          "items_in_cart": items_in_cart,
                          'document_title': document_title,
                          "install_document_request_id": req.id if req else None,
                      }, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_document(request, pk):
    """
        Получение документа
    """
    document = Document.objects.filter(id=pk, is_active=True).first()
    if document is None:
        return Response("Document not found", status=status.HTTP_404_NOT_FOUND)
    serialized_document = DocumentSerializer(document)
    return Response(serialized_document.data, status=status.HTTP_200_OK)


@api_view(['POST'])
def post_document(request):
    """
    Добавление документа
    """
    serializer = DocumentSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    new_document = serializer.save()
    serializer = DocumentSerializer(new_document)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT'])
def put_document(request, pk):
    """
    Изменение документа
    """
    document = Document.objects.filter(id=pk, is_active=True).first()
    if document is None:
        return Response("Document not found", status=status.HTTP_404_NOT_FOUND)
    serializer = DocumentSerializer(document, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def delete_document(request, pk):
    """
    Удаление документа
    """
    document = Document.objects.filter(id=pk, is_active=True).first()
    if document is None:
        return Response("Document not found", status=status.HTTP_404_NOT_FOUND)
    if document.logo_file_path != "":
        minio_storage = MinioStorage(endpoint=settings.MINIO_ENDPOINT_URL,
                                     access_key=settings.MINIO_ACCESS_KEY,
                                     secret_key=settings.MINIO_SECRET_KEY,
                                     secure=settings.MINIO_SECURE)
        file_extension = os.path.splitext(document.logo_file_path)[1]
        file_name = f"{pk}{file_extension}"
        try:
            minio_storage.delete_file(settings.MINIO_BUCKET_NAME, file_name)
        except Exception as e:
            return Response(f"Failed to delete image: {e}",
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        document.logo_file_path = ""
    document.is_active = False
    document.save()
    return Response(status=status.HTTP_200_OK)


@api_view(['POST'])
def post_document_to_request(request, pk):
    """
    Добавление документа в заявку на замену
    """
    document = Document.objects.filter(id=pk, is_active=True).first()
    if document is None:
        return Response("Document not found", status=status.HTTP_404_NOT_FOUND)
    request_id = get_or_create_user_cart(SINGLETON_USER.id)
    add_item_to_request(request_id, pk)
    return Response(status=status.HTTP_200_OK)


def get_or_create_user_cart(user_id: int) -> int:
    """
    Если у пользователя есть заявка в статусе DRAFT (корзина), возвращает её Id.
    Если нет - создает и возвращает id созданной заявки
    """
    old_req = InstallDocumentRequest.objects.filter(client_id=SINGLETON_USER.id,
                                                    status=InstallDocumentRequest.RequestStatus.DRAFT).first()
    if old_req is not None:
        return old_req.id

    new_req = InstallDocumentRequest(client_id=SINGLETON_USER.id,
                                     status=InstallDocumentRequest.RequestStatus.DRAFT)
    new_req.save()
    return new_req.id


@api_view(['POST'])
def post_document_image(request, pk):
    """
    Загрузка изображения документа в Minio
    """
    document = Document.objects.filter(id=pk, is_active=True).first()
    if document is None:
        return Response("Document not found", status=status.HTTP_404_NOT_FOUND)

    minio_storage = MinioStorage(endpoint=settings.MINIO_ENDPOINT_URL,
                                 access_key=settings.MINIO_ACCESS_KEY,
                                 secret_key=settings.MINIO_SECRET_KEY,
                                 secure=settings.MINIO_SECURE)
    file = request.FILES.get("image")
    if not file:
        return Response("No image in request", status=status.HTTP_400_BAD_REQUEST)

    file_extension = os.path.splitext(file.name)[1]
    file_name = f"{pk}{file_extension}"
    try:
        minio_storage.load_file(settings.MINIO_BUCKET_NAME, file_name, file)
    except Exception as e:
        return Response(f"Failed to load image: {e}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    document.logo_file_path = f"http://{settings.MINIO_ENDPOINT_URL}/{settings.MINIO_BUCKET_NAME}/{file_name}"
    document.save()
    return Response(status=status.HTTP_200_OK)


@api_view(['GET'])
def get_install_document_requests(request):
    """
    Получение списка заявок на установку ПО
    """
    status_filter = request.query_params.get("status")
    formation_datetime_start_filter = request.query_params.get("formation_start")
    formation_datetime_end_filter = request.query_params.get("formation_end")

    filters = ~Q(status=InstallDocumentRequest.RequestStatus.DELETED) & ~Q(status=InstallDocumentRequest.RequestStatus.DRAFT)
    if status_filter is not None:
        filters &= Q(status=status_filter.upper())
    if formation_datetime_start_filter is not None:
        filters &= Q(formation_datetime__gte=parse(formation_datetime_start_filter))
    if formation_datetime_end_filter is not None:
        filters &= Q(formation_datetime__lte=parse(formation_datetime_end_filter))

    install_document_requests = InstallDocumentRequest.objects.filter(filters).select_related("client")
    serializer = InstallDocumentRequestSerializer(install_document_requests, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_install_document_request(request, pk):
    """
    Получение заявки
    """
    filters = Q(id=pk) & ~Q(status=InstallDocumentRequest.RequestStatus.DELETED)
    install_document_request = InstallDocumentRequest.objects.filter(filters).first()
    if install_document_request is None:
        return Response("InstallDocumentRequest not found", status=status.HTTP_404_NOT_FOUND)

    serializer = FullInstallDocumentRequestSerializer(install_document_request)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT'])
def put_install_document_request(request, pk):
    """
    Изменение заявки на замену документов
    """
    install_document_request = InstallDocumentRequest.objects.filter(id=pk,
                                                                     status=InstallDocumentRequest.RequestStatus.DRAFT).first()
    if install_document_request is None:
        return Response("InstallDocumentRequest not found", status=status.HTTP_404_NOT_FOUND)

    serializer = PutInstallDocumentRequestSerializer(install_document_request,
                                                     data=request.data,
                                                     partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
def form_install_document_request(request, pk):
    """
    Формирование заявки
    """
    install_document_request = InstallDocumentRequest.objects.filter(id=pk,
                                                                     status=InstallDocumentRequest.RequestStatus.DRAFT).first()
    if install_document_request is None:
        return Response("InstallDocumentRequest not found", status=status.HTTP_404_NOT_FOUND)
    if not is_valid_fields(pk):
        return Response("One or more documents is empty", status=status.HTTP_400_BAD_REQUEST)
    install_document_request.status = InstallDocumentRequest.RequestStatus.FORMED
    install_document_request.formation_datetime = datetime.now()
    install_document_request.save()
    serializer = InstallDocumentRequestSerializer(install_document_request)
    return Response(serializer.data, status=status.HTTP_200_OK)


def generate_document_number(number_length):
    new_number = ''
    for i in range(number_length):
        new_number += str(random.randint(0,9))
    return int(new_number)


def is_valid_fields(request_id):
    """
    Проверка: в заявке должна быть указана новая фамилия и причина замены
    """
    request = InstallDocumentRequest.objects.get(id=request_id)
    print(request)
    if request.new_client_surname is None or request.new_client_surname == "":
        return False
    if request.replace_reason is None or request.replace_reason == "":
        return False
    return True


@api_view(['PUT'])
def resolve_install_document_request(request, pk):
    """
    Закрытие заявки
    """
    install_document_request = InstallDocumentRequest.objects.filter(id=pk,
                                                                     status=InstallDocumentRequest.RequestStatus.FORMED).first()
    if install_document_request is None:
        return Response("InstallDocumentRequest not found", status=status.HTTP_404_NOT_FOUND)

    serializer = ResolveInstallDocumentRequestSerializer(install_document_request,
                                                         data=request.data,
                                                         partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    install_document_request = InstallDocumentRequest.objects.get(id=pk)
    install_document_request.completion_datetime = datetime.now()
    request_documents = DocumentInRequest.objects.filter(replacing_request_id=pk)
    for req_doc in request_documents:
        document = Document.objects.get(id=req_doc.document_id)
        number_length = document.number_length
        req_doc.new_document_number = generate_document_number(number_length)
        req_doc.save()
    install_document_request.manager = SINGLETON_MANAGER
    install_document_request.status = InstallDocumentRequest.RequestStatus.COMPLETED
    install_document_request.save()
    serializer = InstallDocumentRequestSerializer(install_document_request)
    return Response(serializer.data)



@api_view(['DELETE'])
def delete_install_document_request(request, pk):
    """
    Удаление заявки
    """
    install_document_request = InstallDocumentRequest.objects.filter(id=pk,
                                                                     status=InstallDocumentRequest.RequestStatus.DRAFT).first()
    if install_document_request is None:
        return Response("InstallDocumentRequest not found", status=status.HTTP_404_NOT_FOUND)

    install_document_request.status = InstallDocumentRequest.RequestStatus.DELETED
    install_document_request.save()
    return Response(status=status.HTTP_200_OK)


@api_view(['DELETE'])
def delete_document_in_request(request, request_pk, document_pk):
    """
    Удаление из заявки
    """
    document_in_request = DocumentInRequest.objects.filter(replacing_request_id=request_pk, document_id=document_pk).first()
    if document_in_request is None:
        return Response("DocumentInRequest not found", status=status.HTTP_404_NOT_FOUND)
    document_in_request.delete()
    return Response(status=status.HTTP_200_OK)


@api_view(['PUT'])
def put_document_in_request(request, request_pk, document_pk):
    """
    Изменение данных в заявке
    """
    document_in_request = DocumentInRequest.objects.filter(replacing_request_id=request_pk, document_id=document_pk).first()
    if document_in_request is None:
        return Response("DocumentInRequest not found", status=status.HTTP_404_NOT_FOUND)
    serializer = DocumentInRequestSerializer(document_in_request, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def create_user(request):
    """
    Регистрация пользователя
    """
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def update_user(request):
    """
    Обновление данных пользователя
    """
    user = request.user
    serializer = UserSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def login_user(request):
    """
    Аутентификация пользователя
    """
    username = request.POST.get('username')
    password = request.POST.get('password')
    user = authenticate(username=username, password=password)
    if user is not None:
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key}, status=status.HTTP_200_OK)
    return Response({'error': 'Invalid Credentials'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """
    Деавторизация пользователя
    """
    request.auth.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


def get_items_in_request(request_id: int) -> int:
    """
    Получение колическа элементов в заявке по её id
    """
    return DocumentInRequest.objects.filter(replacing_request_id=request_id).select_related('document').count()

def add_item_to_request(request_id: int, document_id: int):
    """
    Добавление услуги в заявку
    """
    doc_in_request = DocumentInRequest(replacing_request_id=request_id, document_id=document_id)
    doc_in_request.save()


def add_document_to_request(request_id: int, document_id: int):
    """
    Добавление документа в заявку
    """
    if not DocumentInRequest(replacing_request_id=request_id, document_id=document_id).exists():
        sir = DocumentInRequest(replacing_request_id=request_id, document_id=document_id)
        sir.save()