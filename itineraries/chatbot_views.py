# views.py (ou chatbot_views.py)

import json
import os
from datetime import timedelta

import openai
from django.conf import settings
from django.contrib.auth.decorators import login_required # type: ignore
from django.http import JsonResponse # type: ignore
from django.shortcuts import redirect, render

from .forms import ItineraryForm
from .models import Day, Itinerary
from .services import (generate_itinerary_overview,
                       get_cordinates_google_geocoding, plan_one_day_itinerary)

openai.api_key = os.getenv('OPENAI_KEY')  # Certifique-se de usar sua chave

@login_required
def chatbot_view(request):

    # 1) Se for GET, apenas renderiza a página de chat
    if request.method == "GET":
        # Garante que a sessão de chat comece limpa, se preferir.
        if "chat_history" not in request.session:
            request.session["chat_history"] = []
        return render(request, "itineraries/chatbot.html", {
            "googlemaps_key": settings.GOOGLEMAPS_KEY,
        })

    # 2) Se for POST AJAX (envio de mensagem do usuário)
    elif request.method == "POST":
        user_message = request.POST.get("message", "").strip()

        # Verifica se há histórico de chat na sessão
        chat_history = request.session.get("chat_history", [])
        
        # Adiciona a mensagem do usuário ao histórico
        chat_history.append({"role": "user", "content": user_message})

        # ----------------------------------------
        # Se o usuário pedir para criar o itinerário
        # você pode detectar via regex ou string simples.
        # Por exemplo, se contiver "crie o itinerário" ou "finalizar".
        # ----------------------------------------
        if "crie o itinerário" in user_message.lower() or "finalizar" in user_message.lower():
            # Aqui podemos pedir ao GPT que retorne (em JSON) os dados:
            # destino, datas, budget etc. Caso prefira, podemos pular
            # e apenas perguntar ao usuário passo a passo.
            # Vamos supor que já temos tudo no histórico ou vamos
            # pedir para o GPT formatar:
            response_text = _extract_or_ask_for_itinerary_data(chat_history)

            # Dependendo da sua lógica, "response_text" pode ser algo como
            # "Entendi, vou criar o itinerário com base nas informações X..."
            # E, em seguida, chamamos create_itinerary_from_chat(...)
            created_itinerary = None
            try:
                created_itinerary = create_itinerary_from_chat(request, chat_history)
            except Exception as e:
                response_text += f"\n\nOcorreu um erro ao criar o itinerário: {str(e)}"

            if created_itinerary:
                response_text += (
                    f"\n\nItinerário criado com sucesso! Destino: {created_itinerary.destination}."
                    f" Veja em 'Meus Itinerários' na Dashboard."
                )
            
            # Adiciona resposta final ao histórico
            chat_history.append({"role": "assistant", "content": response_text})
            request.session["chat_history"] = chat_history
            return JsonResponse({"reply": response_text})

        else:
            # Caso normal: gerar uma resposta usando ChatCompletion
            gpt_reply = _ask_gpt(chat_history)
            # Armazena no histórico
            chat_history.append({"role": "assistant", "content": gpt_reply})
            # Salva
            request.session["chat_history"] = chat_history
            return JsonResponse({"reply": gpt_reply})

    return JsonResponse({"reply": "Método não suportado."}, status=400)

def _ask_gpt(chat_history):
    """
    Envia todo o chat_history para o GPT e retorna a resposta mais recente.
    Você pode personalizar o 'system' prompt para orientar o "Robert".
    """
    system_message = {
        "role": "system", 
        "content": (
            "Você é Robert, um assistente de planejamento de viagens. "
            "Converse em português e seja amigável. "
            "Peça informações importantes sobre a viagem. "
            "Se o usuário disser 'crie o itinerário', tente gerar todos "
            "os dados necessários (destino, datas, orçamento etc.)."
        )
    }

    # Monta a conversa
    conversation = [system_message] + chat_history
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=conversation,
        max_tokens=6000,
        temperature=0.8
    )
    return response.choices[0].message["content"]


def _extract_or_ask_for_itinerary_data(chat_history):
    """
    Exemplo bem simples: Faz parse manual de algo no chat_history ou
    pede para o GPT reorganizar as infos. Fica a critério de como você
    quer implementar. Aqui vamos só retornar um texto básico.
    """
    # Se quiser parsear do chat_history, seria algo como:
    # - Procurar por "Destino", "Data início", etc.
    # Para exemplo, apenas retornamos um texto fixo.
    return (
        "Claro! Vou criar o itinerário com base nas informações que tenho no histórico. "
        "Caso algo não esteja claro, favor confirmar."
    )


def create_itinerary_from_chat(request, chat_history):
    """
    Exemplo que cria o Itinerary igual ao form.
    Precisamos extrair:
      - destination
      - start_date
      - end_date
      - budget
      - travelers
      - interests
      - food_preferences
      - extras
      - transport_mode
      - interest_places
      - trip_type
    Aqui vamos colocar dados 'dummy', mas a ideia é extrair do chat.
    """
    # Exemplo: (em produção, parse de fato do chat)
    destination = "Paris, França"
    start_date = "2025-03-10"
    end_date = "2025-03-15"
    budget = 2000
    travelers = 2
    interests = "Cultura, Gastronomia"
    food_preferences = "nenhuma"
    extras = ""
    transport_mode = "driving"
    interest_places = "Museu do Louvre, Torre Eiffel"
    trip_type = "turismo"

    # 1) Criar itinerário
    itinerary = Itinerary.objects.create(
        user=request.user,
        destination=destination,
        start_date=start_date,
        end_date=end_date,
        budget=budget,
        travelers=travelers,
        interests=interests,
        food_preferences=food_preferences,
        extras=extras,
        transport_mode=transport_mode,
        interest_places=interest_places,
        trip_type=trip_type,
    )

    # 2) Coordenadas
    lat, lng = get_cordinates_google_geocoding(destination)
    itinerary.lat = lat
    itinerary.lng = lng

    # 3) Overview
    overview = generate_itinerary_overview(itinerary)
    itinerary.generated_text = overview
    itinerary.save()

    # 4) Criar Days
    from datetime import datetime, timedelta
    current_date = itinerary.start_date
    day_number = 1
    visited_places_list = []
    while current_date <= itinerary.end_date:
        day = Day.objects.create(
            itinerary=itinerary,
            day_number=day_number,
            date=current_date
        )
        day_text, final_places = plan_one_day_itinerary(
            itinerary=itinerary,
            day=day,
            already_visited=visited_places_list
        )
        day.generated_text = day_text
        day.save()

        visited_places_list.extend(final_places)
        current_date += timedelta(days=1)
        day_number += 1

    return itinerary
