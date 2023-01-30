from urllib.parse import urlparse, parse_qs
import json
import requests
import datetime
import time


code_errors = {
    '0': 'Удачное выполнение операции ',
    '1': 'Недействительная сессия',
    '2': 'Неверное имя сервиса',
    '3': 'Неверный результат',
    '4': 'Неверный ввод',
    '5': 'Ошибка выполнения запроса',
    '6': 'Неизвестная ошибка',
    '7': 'Доступ запрещен',
    '8': 'Неверный пароль или имя пользователя',
    '9': 'Сервер авторизации недоступен, пожалуйста попробуйте повторить запрос позже',
    '10': 'Превышен лимит одновременных запросов',
    '11': 'Ошибка во время выполнения запроса на сброс пароля',
    '14': 'Ошибка биллинга',
    '1001': 'Нет сообщений для выбранного интервала',
    '1002': 'Элемент с таким уникальным свойством уже существует или Невозможно создать элемент в связи с ограничениями биллинга',
    '1003':	['1 - Только один запрос разрешается в данный момент времени',
            '2 - превышено кол-во API запросов/«reason»:«LIMIT api_concurrent»',
    	    '3 - превышено кол-во слоев /«reason»:«LAYERS_MAX_COUNT»',
    	    '4 - превышен лимит сессий/«reason»:«NO_SESSION»',
    	    '5 - временно недоступна база /«reason»:«LOCKER_ERROR»'],
    '1004':	'Превышено ограничение по числу сообщений',
    '1005':	'Ограничение по времени выполнения было превышено',
    '1006':	'Превышение лимита попыток ввода кода двухфакторной авторизации',
    '1011':	'Время сессии истекло либо ваш IP изменился',
    '2006':	'Учетная запись не может быть изменена',
    '2008':	'Нет прав пользователя на объект (при изменении учетной записи)',
    '2014':	'Текущий пользователь не может быть выбран при создании учетной записи',
    '2015':	'Удаление датчика запрещено по причине использования в другом датчике или дополнительных свойствах объекта'
}

HOST = 'http://hst-api.wialon.com'


#Получение токена
def get_token():#Получение токина для работы с SDK-Wialon
    while True:
        response =requests.post('https://hst-api.wialon.com/oauth/authorize.html',params={
            'client_id':'wialon',
            'wialon_sdk_url':'http://hst-api.wialon.com',
            'access_type':-1,
            'activation_time':0,
            'duration':2592000,
            'redirect_uri': 'http://hst-api.wialon.com',
            'login':input('Press login: '),
            'passw':input('Press password: '),
            'response_type': 'token',
            'lang':'ru',
            'flags':7
        })
        URL=response.url
        parsed_url = urlparse(URL)
        url_rsp= parse_qs(parsed_url.query)
        try:
            return url_rsp['access_token']
        except:
            TypeError
            error = url_rsp['svc_error']
            print(code_errors[error[0]])
            False

TOKEN = get_token()
# login

response = requests.post(f'{HOST}/wialon/ajax.html', params={
    'svc': 'token/login',
    'params': json.dumps({
        'token': TOKEN[0]
    })
})
jsonData = response.json()
SID = jsonData['eid']
#print('Login\n', SID, '\n')

# TEST

def find_id_and_name_obj(propValueMask):
    list_obj = []
    response = requests.post(f'{HOST}/wialon/ajax.html', params={
         'svc': 'core/search_items',
         'sid': SID,
         'params': json.dumps({
            "spec": {
                "itemsType": "avl_unit",
                "propName": "sys_name",
                "propValueMask": propValueMask,
                "sortType": "sys_name"
            },
            "force": 1,
            "flags": 1,
            "from": 0,
            "to": 0
         })

    })
    jsonData = response.json()
    # print('Тестовый ответ\n', jsonData, '\n', SID)
    # Получение ID обьекта из словаря вкоторый вложен спиок с словарем
    for item in jsonData['items']:
        new_obj = (item['id'],item['nm'])
        list_obj.append(new_obj)
    return (list_obj)


def add_obj_in_sid(id_item):
    response = requests.post(f'{HOST}/wialon/ajax.html', params={
         'svc': 'events/update_units',# Добавление событий в сессию
         'sid': SID,
         'params': json.dumps({
                 "mode":"add",
                 "units":[
                     {
                        "id":id_item,
                        "detect":
                            {
                                "lls":0,#Уровень ДУТ
                                "counters":0#счетчики пробег , моточасы и т.д.
                            }
                     },
                ]}),
    })
    jsonData = response.json()
    return (jsonData)


def check_updates():
    response = requests.post(f'{HOST}/wialon/ajax.html', params={
        'svc': 'events/check_updates',#Обновление событий
        'sid': SID,
        'params': json.dumps({
            "detalization": 2#При измниении флага дитилизации разный ответ смотреть в документации значение флагов
        })
    })
    jsonData = response.json()
    return (jsonData)


def load_params(id,data):#загрузка событий в сессию за период времени
    response = requests.post(f'{HOST}/wialon/ajax.html', params={
        'svc': 'events/load',#загрузка событий в сессию за период времени
        'sid': SID,
        'params': json.dumps({
            "itemId":id,
            "ivalType":1,
            "timeFrom":1674842400,
            "timeTo":data,
                "detectors": [
        {
                    "type":'lls',
                    "filter1":0
        }],
                    "selector":#загрузка событий из сессию по датчику за период времени
                        {"type": 'lls',
                         "timeFrom": 1674842400,
                         "timeTo": data,
                         "detalization":2
                         }
        })
    })

    jsonData = response.json()
    return (jsonData)


def create_put_list():
    list_a = find_id_and_name_obj(input('Введите назавние транспорта'))
    for i in list_a:
        add_obj_in_sid(i[0])

    list_b = check_updates()
    list_c = []

#Подготовка списка из вложеного словаря для удобства работыс данными
    for i in list_b:
        for value in list_b[i][1]['lls'].values():
            list_d=[]
            list_d.append(int(i))
            list_d.append(value["value"])
            list_d.append(list_b[i][0]['counters']['engine_hours']/3600)
            list_d.append(list_b[i][0]['counters']['mileage']/1000)
            list_c.append(list_d)


    for i in list_a:
        for j in list_c:
            if i[0]==j[0]:
                j.append(i[1])



#print(load_params())

    return print(list_c,'Путевой лист создан','Время на момент записи данных',datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),sep='\n')


def finish_put_list():
    data = int(
        time.mktime(time.strptime(input('Введите время на момент завешения путевоголиста: '), '%Y-%m-%d %H:%M:%S')))
    list_a = find_id_and_name_obj(input('Введите назавние транспорта'))
    print('Процесс завершение путевого листа, пожалуйста подождите...')
    for i in list_a:
        add_obj_in_sid(i[0])

    list_b = check_updates()
    list_c = []

    # Подготовка списка из вложеного словаря для удобства работыс данными
    for i in list_b:
        for value in list_b[i][1]['lls'].values():
            list_d = []
            list_d.append(int(i))
            list_d.append(value["value"])
            list_d.append(list_b[i][0]['counters']['engine_hours'] / 3600)
            list_d.append(list_b[i][0]['counters']['mileage'] / 1000)
            list_c.append(list_d)

    for i in list_a:
        for j in list_c:
            if i[0] == j[0]:
                j.append(i[1])


    for i in list_c:
        s = load_params(i[0],data)
        for j in s['selector'].values():
            for f in j.values():
                if len(f) == 0:
                    z = 0
                    i.append(z)
                for k in f:
                    z = k['filled']
                    i.append(z)


    return print(list_c,'Создание путевго листа завершено','Время на момент записи данных',datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),sep="\n")


print('Добро пожаловать в "Путевые листы",Выберите действие','Для создания путевого листа нажмите клавишу "1"',
      'Для завершения путевого листа нажмите клавишу"2"',sep='\n')
q=int(input())
if q == 1:
    print('Процесс создания путевого листа, пожалуйста подождите...')
    create_put_list()
elif q == 2:
    print(finish_put_list())

else:
    print('Вы нажали нету клавишу')


response = requests.post(f'{HOST}/wialon/ajax.html', params={
    'svc': 'core/logout',
    'sid': SID,
    'params': json.dumps({})
})

#print('logout\n', response.text)
'''

'''