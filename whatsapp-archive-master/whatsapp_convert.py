#!/usr/bin/python3
"""Reads a WhatsApp conversation export file and writes a HTML file."""

import argparse
import datetime
from traceback import print_tb
import dateutil.parser
import itertools
import jinja2
import logging
import os
import re
import random

# Format of the standard WhatsApp export line. This is likely to change in the
# future and so this application will need to be updated.
DATE_RE = '(?P<date>[\d/-]+)'
TIME_RE = '(?P<time>[\d:]+( [AP]M)?)'
DATETIME_RE = '\[?' + DATE_RE + ',? ' + TIME_RE + '\]?'
SEPARATOR_RE = '( - |: | )'
NAME_RE = '(?P<name>[^:]+)'
WHATSAPP_RE = (DATETIME_RE +
               SEPARATOR_RE +
               NAME_RE +
               ': '
               '(?P<body>.*$)')

FIRSTLINE_RE = (DATETIME_RE +
               SEPARATOR_RE +
               '(?P<body>.*$)')


class Error(Exception):
    """Something bad happened."""


def ParseLine(line):
    """Parses a single line of WhatsApp export file."""
    m = re.match(WHATSAPP_RE, line)
    if m:
        d = dateutil.parser.parse("%s %s" % (m.group('date'),
            m.group('time')), dayfirst=True)
        return d, m.group('name'), m.group('body')
    # Maybe it's the first line which doesn't contain a person's name.
    m = re.match(FIRSTLINE_RE, line)
    if m:
        a = re.match(DATETIME_RE, line)
        if (a.end()-a.start()) != 16:
            return None
            
    if m:
        d = dateutil.parser.parse("%s %s" % (m.group('date'),
            m.group('time')), dayfirst=True)
        return d, "Whatsapp", m.group('body')
    return None
    

def IdentifyMessages(lines):
    """Input text can contain multi-line messages. If there's a line that
    doesn't start with a date and a name, that's probably a continuation of the
    previous message and should be appended to it.
    """
    messages = []
    msg_date = None
    msg_user = None
    msg_body = None
    for line in lines:
        m = ParseLine(line)
        if m is not None:
            if msg_date is not None:
                # We have a new message, so there will be no more lines for the
                # one we've seen previously -- it's complete. Let's add it to
                # the list.
                messages.append((msg_date, msg_user, msg_body))
            msg_date, msg_user, msg_body = m
        else:
            if msg_date is None:
                raise Error("Can't parse the first line: " + repr(line) +
                        ', regexes are FIRSTLINE_RE=' + repr(FIRSTLINE_RE) +
                        ' and WHATSAPP_RE=' + repr(WHATSAPP_RE))
            msg_body += '\n' + line.strip()
    # The last message remains. Let's add it, if it exists.
    if msg_date is not None:
        messages.append((msg_date, msg_user, msg_body))
    return messages


def TemplateData(messages, input_filename):
    """Create a struct suitable for procesing in a template.
    Returns:
        A dictionary of values.
    """
    by_user = []
    file_basename = os.path.basename(input_filename)
    for user, msgs_of_user in itertools.groupby(messages, lambda x: x[1]):
        by_user.append((user, list(msgs_of_user)))
    
    l = []
    n = []
    for i in by_user:
        if i[0] not in n:
            l.append((i[0], (random.randint(100, 200), random.randint(100, 200), random.randint(100, 200))))
            n.append(i[0])
    
    """
        by_user =
            [grupo de mensagens por usuário que enviou, vai de 0 até a quantidade de agrupamentos de mensagens por pessoa]
            [0 - usuário que enviou aquele grupo de mensagens; 1 - grupo de mensagens]
            [tuplas com: (data, usuário, mensagem), todas as mensagens daquele grupo de mensagens]
            [3 valores: 0 - horário da mensagem; 1 - usuário da mensagem; 2 - mensagem]
    """
    return dict(by_user=by_user, input_basename=file_basename,
            input_full_path=input_filename, users=l)


def FormatHTML(data):
    tmpl = """<!DOCTYPE html>
    <html>
    <head>
        <title>WhatsApp {{ input_basename }}</title>
        <meta charset="utf-8"/>
        <link rel="icon" type="image/png" href="https://cdn-icons-png.flaticon.com/512/1384/1384095.png" />
        <!-- <a href="https://www.flaticon.com/free-icons/missed-call" title="missed call icons">Missed call icons created by Plastic Donut - Flaticon</a> -->
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * {
                box-sizing:border-box; 
            }
            body {
                font-family: sans-serif;
                font-size: 12px;
                background-color: #3F3F37;
            }
            h1 {
                color: #EAF2EF;
            }
            ol.users {
                list-style-type: none;
                list-style-position: inside;
                margin: 0;
                padding: 0;
            }
            ol.users li.conjunto {
                margin-bottom: 10px;
            }
            ol.messages {
                list-style-type: none;
                list-style-position: inside;
                margin: 0;
                padding: 0;
            }
            ol.messages li.le{
                color: #D6D6B1;
                margin-right: 1em;
                margin-left: 1em;
                font-size: 16px;
                display: flex;
                flex-direction: row;
                align-items: center;
            }
            ol.messages li.ri{
                color: #D6D6B1;
                margin-left: 1em;
                margin-right: 1em;
                font-size: 16px;
                display: flex;
                flex-direction: row;
                align-items: center;
                justify-content: end;
            }
            ol.messages li.Whatsapp{
                color: #D6D6B1;
                margin-left: 1em;
                margin-right: 1em;
                font-size: 16px;
                display: flex;
                flex-direction: row;
                align-items: center;
                justify-content: center;
            }
            div {
                display: flex;
                flex-direction: row;
                justify-content: flex-start;

                background-color: #30292F;
                margin: 2px;
                padding: 12px;
                border-radius: 12px;
            }
            div.Whatsapp-c {
                background-color: #181723;
            }

            img {
                max-width: 200px;
                max-height: 300px;
            }
            input[type=checkbox] {
                display: none;
            }
            img {
                transition: transform 0.25s ease;
                cursor: zoom-in;
            }
            input[type=checkbox]:checked ~ label > img {
                transform: scale(2.5);
                cursor: zoom-out;
                z-index: 1;
                position: relative;
            }
            #missed-call {
                width: 20px;
                height: 20px;
                margin: 0 15px;
            }
            audio {
                max-width: 100%;
                width: 300px;
            }
            video {
                max-height: 300px;
                max-width: 100%;
                width: 300px;
            }
            a{
                color: #ccbfb9;
            }
        {% for u in users %}
            span.{{ u[0].replace(' ', '-').replace("+", 'b').replace('.','') }} {
                margin: 0 2px;
                font-weight: bold;
                color: rgb{{ u[1] }};
            }
        {% endfor %}
            span.date {
                color: #878472;
            }
        </style>
    </head>
    <body>
        <h1>{{ input_basename }}</h1>
        <ol class="users">
        {% for user, messages in by_user %}
            <li class="conjunto">
            <ol class="messages">
        {% for message in messages %}
            {% if user == "Whatsapp" %}
                <li class="Whatsapp">
                    <div class="Whatsapp-c">
                        <span class="date">{{ message[0] }} -</span>
                        <span class="{{ user.replace(' ', '-') }}" >{{ user }}: </span>
                        {{message[2] | e}}
                    </div>
                </li>
            {% elif users|length <= 3 %}
                {% if user in input_basename %}
                <li class="le">
                    <div class="{{ user.replace(' ', '_') }}">
                        <span class="date">{{ message[0] }} -</span>
                        <span class="{{ user.replace("+", 'b').replace(' ', '-').replace('.','') }}" >{{ user }}: </span>
                        {% if message[2] == "Chamada de voz perdida" or message[2] == "Chamada de vídeo perdida" %}
                            <img id="missed-call" src='https://cdn-icons.flaticon.com/png/512/5604/premium/5604556.png?token=exp=1649681187~hmac=85540c3c1ac7984f32c86a041484e55f'>
                        {% endif %}
                        {% if "localização:" in message[2] %}
                            localização: <a href={{message[2][message[2].index('localização:')+13:] | e }} target='_blank'>{{message[2][message[2].index('localização:')+13:] | e }}</a>
                        
                        {% elif message[2].endswith('.opus (arquivo anexado)') or message[2].endswith('.mp3 (arquivo anexado)') or message[2].endswith('.mp3') %}
                            <audio controls>
                                <source src="./Midias/{{ message[2][1:message[2].index(' (arquivo')] | e }}" type="audio/mp3">
                                <source src="./Midias/{{ message[2][1:message[2].index(' (arquivo')] | e }}" type="audio/ogg">
                                Seu navegador não possui suporte para áudio.
                            </audio>

                        {% elif message[2].endswith('.mp4 (arquivo anexado)') %}
                            <video controls>
                                <source src="./Midias/{{ message[2][1:message[2].index(' (arquivo')] | e }}" type="video/mp4">
                                <source src="./Midias/{{ message[2][1:message[2].index(' (arquivo')] | e }}" type="video/ogg">
                                Seu navegador não possui suporte para Vídeos.
                            </video>
                        
                        {% elif ('.webp (arquivo') in message[2] %}
                            <picture>
                                <source srcset="./Midias/{{ message[2][1:message[2].index(' (arquivo')] | e }}" type="image/webp">
                                <source srcset="./Midias/{{ message[2][1:message[2].index(' (arquivo')] | e }}" type="image/jpeg">
                                <img src="./Midias/{{ message[2][1:message[2].index(' (arquivo')] | e }}">
                            </picture>

                        {% elif message[2].endswith('.jpg (arquivo anexado)') %}
                            <input type="checkbox" id="zoomCheck-{{ message[2][1:message[2].index(' (arquivo')] | e }}">
                            <label for='zoomCheck-{{ message[2][1:message[2].index(' (arquivo')] | e }}'>
                                <img src='./Midias/{{ message[2][1:message[2].index(' (arquivo')] | e }}'>                    
                            </label>
                        
                        {% elif '(arquivo anexado)' in message[2] %}
                            {% if message[2][message[2].index(')')+1:] %}
                                <a href='./Midias/{{ message[2][1:message[2].index(' (arquivo')] | e }}' target="_blank" download>{{ message[2][message[2].index(')')+2:] | e }}</a>
                            {% else %}
                                <a href='./Midias/{{ message[2][1:message[2].index(' (arquivo')] | e }}' target="_blank" download>{{ message[2].replace(" (arquivo anexado)","") | e }}</a>
                            {% endif %}
                        {% else %}
                            {% if '\n' in message[2] %}
                                {% for i in message[2].split("\n") %}
                                {{ i }}
                                <br>
                                {% endfor %}
                            {% else %}
                                {{ message[2] | e }}
                            {% endif %}
                        {% endif %}
                    </div>
                </li>
                {% else %}
                <li class="ri">
                    <div class="{{ user.replace(' ', '_') }}">
                        <span class="date">{{ message[0] }} -</span>
                        <span class="{{ user.replace("+", 'b').replace(' ', '-').replace('.','') }}" >{{ user }}: </span>
                        {% if message[2] == "Chamada de voz perdida" or message[2] == "Chamada de vídeo perdida" %}
                            <img id="missed-call" src='https://cdn-icons.flaticon.com/png/512/5604/premium/5604556.png?token=exp=1649681187~hmac=85540c3c1ac7984f32c86a041484e55f'>
                        {% endif %}
                        {% if "localização:" in message[2] %}
                            localização: <a href={{message[2][message[2].index('localização:')+13:] | e }} target='_blank'>{{message[2][message[2].index('localização:')+13:] | e }}</a>
                        
                        {% elif message[2].endswith('.opus (arquivo anexado)') or message[2].endswith('.mp3 (arquivo anexado)') or message[2].endswith('.mp3') %}
                            <audio controls>
                                <source src="./Midias/{{ message[2][1:message[2].index(' (arquivo')] | e }}" type="audio/mp3">
                                <source src="./Midias/{{ message[2][1:message[2].index(' (arquivo')] | e }}" type="audio/ogg">
                                Seu navegador não possui suporte para áudio.
                            </audio>

                        {% elif message[2].endswith('.mp4 (arquivo anexado)') %}
                            <video controls>
                                <source src="./Midias/{{ message[2][1:message[2].index(' (arquivo')] | e }}" type="video/mp4">
                                <source src="./Midias/{{ message[2][1:message[2].index(' (arquivo')] | e }}" type="video/ogg">
                                Seu navegador não possui suporte para Vídeos.
                            </video>

                        {% elif ('.webp (arquivo') in message[2] %}
                            <picture>
                                <source srcset="./Midias/{{ message[2][1:message[2].index(' (arquivo')] | e }}" type="image/webp">
                                <source srcset="./Midias/{{ message[2][1:message[2].index(' (arquivo')] | e }}" type="image/jpeg">
                                <img src="./Midias/{{ message[2][1:message[2].index(' (arquivo')] | e }}">
                            </picture>

                        {% elif message[2].endswith('.jpg (arquivo anexado)') %}
                            <input type="checkbox" id="zoomCheck-{{ message[2][1:message[2].index(' (arquivo')] | e }}">
                            <label for='zoomCheck-{{ message[2][1:message[2].index(' (arquivo')] | e }}'>
                                <img src='./Midias/{{ message[2][1:message[2].index(' (arquivo')] | e }}'>                    
                            </label>

                        {% elif '(arquivo anexado)' in message[2] %}
                            {% if message[2][message[2].index(')')+1:] %}
                                <a href='./Midias/{{ message[2][1:message[2].index(' (arquivo')] | e }}' target="_blank" download>{{ message[2][message[2].index(')')+2:] | e }}</a>
                            {% else %}
                                <a href='./Midias/{{ message[2][1:message[2].index(' (arquivo')] | e }}' target="_blank" download>{{ message[2].replace(" (arquivo anexado)","") | e }}</a>
                            {% endif %}
                        {% else %} 
                            {% if '\n' in message[2] %}
                                {% for i in message[2].split("\n") %}
                                {{ i }}
                                <br>
                                {% endfor %}
                            {% else %}
                                {{ message[2] | e }}
                            {% endif %}
                        {% endif %}
                    </div>
                </li>

                {% endif %}
            {% else %}
                <li class="le">
                    <div class="{{ user.replace(' ', '_') }}">
                        <span class="date">{{ message[0] }} -</span>
                        <span class="{{ user.replace(' ', '-').replace("+", "b").replace('.','') }}" >{{ user }}: </span>
                        {% if message[2] == "Chamada de voz perdida" or message[2] == "Chamada de vídeo perdida" %}
                            <img id="missed-call" src='https://cdn-icons.flaticon.com/png/512/5604/premium/5604556.png?token=exp=1649681187~hmac=85540c3c1ac7984f32c86a041484e55f'>
                        {% endif %}
                        {% if "localização:" in message[2] %}
                            localização: <a href={{message[2][message[2].index('localização:')+13:] | e }} target='_blank'>{{message[2][message[2].index('localização:')+13:] | e }}</a>
                        {% elif message[2].endswith('.opus (arquivo anexado)') or message[2].endswith('.mp3 (arquivo anexado)') or message[2].endswith('.mp3') %}
                            <audio controls>
                                <source src="./Midias/{{ message[2][1:message[2].index(' (arquivo')] | e }}" type="audio/ogg">
                                <source src="./Midias/{{ message[2][1:message[2].index(' (arquivo')] | e }}" type="audio/mp3">
                                Seu navegador não possui suporte para áudio.
                            </audio>

                        {% elif message[2].endswith('.mp4 (arquivo anexado)') %}
                            <video controls>
                                <source src="./Midias/{{ message[2][1:message[2].index(' (arquivo')] | e }}" type="video/mp4">
                                <source src="./Midias/{{ message[2][1:message[2].index(' (arquivo')] | e }}" type="video/ogg">
                                Seu navegador não possui suporte para Vídeos.
                            </video>

                        {% elif message[2].endswith('.jpg (arquivo anexado)') %}
                            <input type="checkbox" id="zoomCheck-{{ message[2][1:message[2].index(' (arquivo')] | e }}">
                            <label for='zoomCheck-{{ message[2][1:message[2].index(' (arquivo')] | e }}'>
                                <img src='./Midias/{{ message[2][1:message[2].index(' (arquivo')] | e }}'>                    
                            </label>
                        {% elif '(arquivo anexado)' in message[2] %}
                            {% if message[2][message[2].index(')')+1:] %}
                                <a href='./Midias/{{ message[2][1:message[2].index(' (arquivo')] | e }}' target="_blank" download>{{ message[2][message[2].index(')')+2:] | e }}</a>
                            {% else %}
                                <a href='./Midias/{{ message[2][1:message[2].index(' (arquivo')] | e }}' target="_blank" download>{{ message[2].replace(" (arquivo anexado)","") | e }}</a>
                            {% endif %}
                        {% else %}
                            {% if '\n' in message[2] %}
                                {% for i in message[2].split("\n") %}
                                {{ i }}
                                <br>
                                {% endfor %}
                            {% else %}
                                {{ message[2] | e }}
                            {% endif %}
                        {% endif %}
                    </div>
                </li>
            {% endif %}
        {% endfor %}
            </ol>
            <br>
            </li>
        {% endfor %}
        </ol>
    </body>
    </html>
    """
    return jinja2.Environment().from_string(tmpl).render(**data)

def main():
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description='Produce a browsable history of a WhatsApp conversation')
    parser.add_argument('-i', dest='input_file', required=True)
    parser.add_argument('-o', dest='output_file', required=True)

    args = parser.parse_args()

    with open(args.input_file, 'rt', encoding='utf-8-sig') as fd:
        messages = IdentifyMessages(fd.readlines())

    template_data = TemplateData(messages, args.input_file)
    HTML = FormatHTML(template_data)

    with open(args.output_file, 'w', encoding='utf-8') as fd:
        fd.write(HTML)
    
    print("Entrada=",parser.parse_args().input_file)
    print("Saída=",parser.parse_args().output_file)


if __name__ == '__main__':
    main()
