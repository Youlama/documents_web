from django.shortcuts import render, redirect
from django.db import connection
from django.db.models import Q

from replacing_documents.models import Document, DocumentInRequest, InstallDocumentRequest

USER_ID = 1

def get_request_data(request_id: int):
    """
    Формирование данных по заявке
    """
    req = InstallDocumentRequest.objects.filter(~Q(status=InstallDocumentRequest.RequestStatus.DELETED),
                                                id=request_id).first()
    if req is None:
        return {
            'id': request_id,
            'document_list': [],
            'total': 0,
            'req_id': request_id,
        }
    items = DocumentInRequest.objects.filter(replacing_request_id=request_id).select_related('document')
    replace_data = (DocumentInRequest.objects.filter(replacing_request_id=request_id)
                    .select_related('replacing_request').first())
    req_docs_data = DocumentInRequest.objects.filter(replacing_request_id=request_id).first()
    print(replace_data, 'and ', req_docs_data)
    return {
        'id': request_id,
        'document_list': items,
        'req_docs_data': req_docs_data,
        'req_id': request_id,
        'replace_data': replace_data,
    }


def get_items_in_request(request_id: int) -> int:
    """
    Получение колическа элементов в заявке по её id
    """
    return DocumentInRequest.objects.filter(replacing_request_id=request_id).select_related('document').count()


def get_or_create_user_cart(user_id: int) -> int:
    """
    Если у пользователя есть заявка в статусе DRAFT (корзина), возвращает её Id.
    Если нет - создает и возвращает id созданной заявки
    """
    old_req = InstallDocumentRequest.objects.filter(client_id=USER_ID,
                                                    status=InstallDocumentRequest.RequestStatus.DRAFT).first()
    if old_req is not None:
        return old_req.id

    new_req = InstallDocumentRequest(client_id=USER_ID, status=InstallDocumentRequest.RequestStatus.DRAFT)
    new_req.save()
    return new_req.id

def add_item_to_request(request_id: int, document_id: int):
    """
    Добавление услуги в заявку
    """
    print('add')
    sir = DocumentInRequest(replacing_request_id=request_id, document_id=document_id)
    sir.save()


def get_document_list(request):
    """
    Получение страницы списка услуг
    """
    document_title = request.GET.get('document_title', '')
    req = InstallDocumentRequest.objects.filter(client_id=USER_ID,
                                                status=InstallDocumentRequest.RequestStatus.DRAFT).first()
    document_list = Document.objects.filter(title__istartswith=document_title)
    return render(request, 'document_list.html',
                  {'data':
                      {
                          'document_list': document_list,
                          'items_in_cart': (get_items_in_request(req.id) if req is not None else 0),
                          'document_title': document_title,
                          'request_id': (req.id if req is not None else 0),
                      }, })


def add_document_to_cart(request, document_id: int):
    """
    Добавление услуги в заявку с проверкой на дублирование.
    """
    if request.method != "POST":
        return redirect('document_list')

    request_id = get_or_create_user_cart(USER_ID)

    # Проверяем, существует ли уже документ в текущей заявке
    if not DocumentInRequest.objects.filter(replacing_request_id=request_id, document_id=document_id).exists():
        add_item_to_request(request_id, document_id)
    else:
        print(f"Документ с ID {document_id} уже добавлен в заявку {request_id}.")

    return redirect('document_list')



def document_page(request, id):
    """
    Получение страницы услуги
    """
    data = Document.objects.filter(id=id).first()
    if data is None:
        return render(request, 'document.html')

    return render(request, 'document.html',
                  {'data': {
                      'document': data,
                  }})


def delete_request(request, request_id: int):
    """
    Удаление заявки по id
    """
    raw_sql = "UPDATE install_document_requests SET status='DELETED' WHERE id=%s"
    with connection.cursor() as cursor:
        cursor.execute(raw_sql, (request_id,))
    return redirect('document_list')

def remove_document_request(request, id: int):
    """
    Удаление услуги из заявки
    """
    if request.method != "POST":
        return redirect('install_document_request')

    data = request.POST
    action = data.get("request_action")
    if action == "delete_request":
        delete_request(id)
        return redirect('document_list')
    return get_document_request(request, id)


def get_document_request(request, id: int):
    """
    Получение страницы заявки
    """
    return render(request, 'replace.html',
                  {'data': get_request_data(id)})
