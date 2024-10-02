from django.shortcuts import render

document_list = [
    {
        'id': 0,
        'title': 'Паспорт РФ',
        'logo_file_path': 'http://127.0.0.1:9000/lab/0.jpg',
        'docs': 'Старый паспорт, свидетельство о браке или разводе, смене ФИО или даты рождения, фото 35 × 45 мм, чек об оплате госпошлины.',
        'replace_period':' В течение 90 календарных дней',
        'prod_period': 10,
    },
    {
        'id': 1,
        'title': 'Загранпаспорт',
        'logo_file_path': 'http://127.0.0.1:9000/lab/1.jpg',
        'docs': 'Ранее выданные загранпаспорта — при наличии, паспорт РФ',
        'replace_period':'Неограничен. Старый документ недействителен.',
        'prod_period': 30,
    },
    {
        'id': 2,
        'title': 'Водительское удостоверение',
        'logo_file_path': 'http://127.0.0.1:9000/lab/2.jpg',
        'docs': 'Водительское удостоверение, паспорт РФ',
        'replace_period':'Неограничен. Старый документ недействителен.',
        'prod_period': 1,
    },
    {
        'id': 3,
        'title': 'Полис ОМС',
        'logo_file_path': 'http://127.0.0.1:9000/lab/3.jpg',
        'docs': 'Паспорт РФ, старый полис ОМС',
        'replace_period': '30 календарных дней',
        'prod_period': 45,
    },
    {
        'id': 4,
        'title': 'ИНН',
        'logo_file_path': 'http://127.0.0.1:9000/lab/4.jpg',
        'docs': 'Паспорт РФ',
        'replace_period': 'Неограничен. Старый документ недействителен.',
        'prod_period': 5,
    },
]

replace_list = [
    {
        'id': 0,
        'reason': "Вступление в брак",
        'new_surname': "Пятигорская",
        'organization': "Лениградское шоссе, д. 31/2",
    },
]

def get_document_list(search_query: str):
    res = []
    for document in document_list:
        if document["title"].lower().startswith(search_query.lower()):
            res.append(document)
    return res


def get_replace_data(id):
    replace_data = replace_list[id].copy()
    document_data = document_list[0:3].copy()
    return {
        'replace_data': replace_data,
        'document_list': document_data,
    }


def document_list_page(replace):
    document_title = replace.GET.get('document_title', '')

    return render(replace, 'document_list.html',
                  {'data': {
                      'document_list': get_document_list(document_title),
                      'count': len(replace_list),
                      'document_title': document_title,
                      'replace_id': 0,
                  }, })


def document_page(replace, id):
    for document in document_list:
        if document['id'] == id:
            return render(replace, 'document.html',
                          {'data': document})
    render(replace, 'document.html')

def replace_page(replace, id):
    if id != 0:
        return render(replace, 'replace.html')

    return render(replace, 'replace.html',
                  {'data': get_replace_data(id)})
