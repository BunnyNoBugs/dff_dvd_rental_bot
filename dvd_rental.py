from df_engine.core.keywords import GLOBAL, TRANSITIONS, RESPONSE, PROCESSING
from df_engine.core import Context, Actor
import df_engine.conditions as cnd
import df_engine.labels as lbl

from typing import Union
import re

FILMS_DB = {
    'action': ['film1', 'film2'],
    'comedy': ['film1', 'film2'],
    'drama': ['film1', 'film2'],
    'horror': ['film1', 'film2'],
    'thriller': ['film1', 'film2'],
    'romance': ['film1', 'film2']
}

MOOD_GENRE_RECOMMENDATIONS = {
    'bored': ['action', 'thriller'],
    'great': ['thriller', 'comedy'],
    'unhappy': ['comedy'],
    'lonely': ['romance']
}


def is_mood(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    request = ctx.last_request
    for i in MOOD_GENRE_RECOMMENDATIONS:
        if re.search(i, request):
            return True
    else:
        return False


def reacted_to_recommendation(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    return bool(ctx.misc.get('reacted_to_recommendation'))


def has_preferred_genre(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    return bool(ctx.misc.get('preferred_genre'))


def has_film_name(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    return bool(ctx.misc.get('film_name'))


def has_rental_period(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    return bool(ctx.misc.get('rental_period'))


def set_current_mood():
    def set_current_mood_processing(ctx: Context, actor: Actor):
        ctx.misc['current_mood'] = ctx.last_request
        return ctx

    return set_current_mood_processing


def recommend_genre():
    def recommend_genre_processing(ctx: Context, actor: Actor):
        processed_node = ctx.a_s.get("processed_node", ctx.a_s["next_node"])
        current_mood = ctx.misc['current_mood']
        recommended_genre = MOOD_GENRE_RECOMMENDATIONS[current_mood][0]
        ctx.misc['recommended_genre'] = recommended_genre
        processed_node.response = f'Do you feel like watching a {recommended_genre} film?'
        ctx.misc['reacted_to_recommendation'] = False
        ctx.a_s["processed_node"] = processed_node
        return ctx

    return recommend_genre_processing


def inform_preferred_genre():
    def inform_preferred_genre_processing(ctx: Context, actor: Actor):
        processed_node = ctx.a_s.get("processed_node", ctx.a_s["next_node"])
        preferred_genre = ctx.misc['preferred_genre']
        processed_node.response = f'OK, I will remember that you prefer {preferred_genre}'
        ctx.a_s["processed_node"] = processed_node
        return ctx

    return inform_preferred_genre_processing


def validate_recommended_genre():
    def validate_recommended_genre_processing(ctx: Context, actor: Actor):
        processed_node = ctx.a_s.get("processed_node", ctx.a_s["next_node"])
        recommended_genre = ctx.misc['recommended_genre']
        request = ctx.last_request
        if re.search(r'yes', request):
            ctx.misc['reacted_to_recommendation'] = True
            ctx.misc['preferred_genre'] = recommended_genre
            processed_node.response = f'OK, I will remember that you prefer {recommended_genre}'
        elif re.search(r'no', request):
            ctx.misc['reacted_to_recommendation'] = True
            processed_node.response = "OK, it's up to you"
        else:
            processed_node.response = f"Sorry, I didn't get you. Do you feel like watching a {recommended_genre} film?"
        ctx.a_s["processed_node"] = processed_node
        return ctx

    return validate_recommended_genre_processing


def validate_preferred_genre():
    def validate_preferred_genre_processing(ctx: Context, actor: Actor):
        processed_node = ctx.a_s.get("processed_node", ctx.a_s["next_node"])
        request = ctx.last_request
        if request in FILMS_DB:
            ctx.misc['preferred_genre'] = request
            processed_node.response = f'OK! Your preferred genre is {request}'
        else:
            processed_node.response = f'Please choose from the genres available: {", ".join(FILMS_DB)}'
        ctx.a_s["processed_node"] = processed_node
        return ctx

    return validate_preferred_genre_processing


def validate_film_name():
    def validate_film_name_processing(ctx: Context, actor: Actor):
        processed_node = ctx.a_s.get("processed_node", ctx.a_s["next_node"])
        preferred_genre = ctx.misc['preferred_genre']
        request = ctx.last_request
        if request in FILMS_DB[preferred_genre]:
            ctx.misc['film_name'] = request
            processed_node.response = f'OK! You would like to rent "{request}"'
        else:
            film_list = [f'"{i}"' for i in FILMS_DB[preferred_genre]]
            processed_node.response = f'Please choose a film from our list: {", ".join(film_list)}'
        ctx.a_s["processed_node"] = processed_node
        return ctx

    return validate_film_name_processing


def validate_rental_period():
    def validate_rental_period_processing(ctx: Context, actor: Actor):
        processed_node = ctx.a_s.get("processed_node", ctx.a_s["next_node"])
        request = ctx.last_request
        if request.isdigit() and (1 <= int(request) <= 14):
            ctx.misc['rental_period'] = request
            processed_node.response = f"OK! I will rent \"{ctx.misc['film_name']}\" for {request} days for you"
        else:
            processed_node.response = 'Please choose a number of days between 1 and 14'
        ctx.a_s["processed_node"] = processed_node
        return ctx

    return validate_rental_period_processing


# create plot of dialog
plot = {
    GLOBAL: {
        TRANSITIONS: {
            ('global_flow', 'iamabot'): cnd.regexp(r'who are you'),
            ('genre_recommendation_flow', 'greet'): cnd.regexp(r'hi'),
            ('genre_recommendation_flow', 'chitchat'): cnd.regexp(r'chat'),
            ('film_rental_form', 'ask_preferred_genre'): cnd.all([cnd.regexp(r'rent'), cnd.neg(has_preferred_genre)]),
            ('film_rental_form', 'ask_film_name'): cnd.all([cnd.regexp(r'rent'), has_preferred_genre])
        }
    },
    "global_flow": {
        'start_node': {
            TRANSITIONS: {}
        },
        "iamabot": {RESPONSE: "I am an assistant for a DVD rental shop, I will help you rent a film"},
        "fallback_node": {
            RESPONSE: "I didn't get it. Could you try again?",
            TRANSITIONS: {lbl.previous(): cnd.true()}
        },
    },
    'film_rental_form': {
        'ask_preferred_genre': {
            RESPONSE: 'What film genre do you prefer?',
            TRANSITIONS: {'validate_preferred_genre': cnd.true()}
        },
        'validate_preferred_genre': {
            PROCESSING: {1: validate_preferred_genre()},
            TRANSITIONS: {
                'ask_film_name': has_preferred_genre,
                lbl.repeat(): cnd.neg(has_preferred_genre)
            }
        },
        'ask_film_name': {
            RESPONSE: 'Please choose the film you would like to rent',
            TRANSITIONS: {'validate_film_name': cnd.true()}
        },
        'validate_film_name': {
            PROCESSING: {1: validate_film_name()},
            TRANSITIONS: {
                'ask_rental_period': has_film_name,
                lbl.repeat(): cnd.neg(has_film_name)
            }
        },
        'ask_rental_period': {
            RESPONSE: 'For how many days would you like to rent?',
            TRANSITIONS: {'validate_rental_period': cnd.true()}
        },
        'validate_rental_period': {
            PROCESSING: {1: validate_rental_period()},
            TRANSITIONS: {lbl.repeat(): cnd.neg(has_rental_period)}
        }
    },
    'genre_recommendation_flow': {
        'greet': {
            RESPONSE: 'Hi! How are you?',
            TRANSITIONS: {'recommend_genre': is_mood}
        },
        'chitchat': {
            RESPONSE: 'Oh, so you want to chat. How are you?',
            TRANSITIONS: {'recommend_genre': is_mood}
        },
        'recommend_genre': {
            PROCESSING: {1: set_current_mood(), 2: recommend_genre()},
            TRANSITIONS: {'validate_recommended_genre': cnd.true()}
        },
        'validate_recommended_genre': {
            PROCESSING: {1: validate_recommended_genre()},
            TRANSITIONS: {lbl.repeat(): cnd.neg(reacted_to_recommendation)}
        },
    },
}

# init actor
actor = Actor(plot, start_label=("global_flow", "start_node"),
              fallback_label=('global_flow', 'fallback_node')
              )


# handler requests
def turn_handler(in_request: str, ctx: Union[Context, dict], actor: Actor):
    # Context.cast - gets an object type of [Context, str, dict] returns an object type of Context
    ctx = Context.cast(ctx)
    # Add in current context a next request of user
    ctx.add_request(in_request)
    # pass the context into actor and it returns updated context with actor response
    ctx = actor(ctx)
    # get last actor response from the context
    out_response = ctx.last_response
    # the next condition branching needs for testing
    return out_response, ctx


ctx = {}
while True:
    in_request = input("type your answer: ")
    out_response, ctx = turn_handler(in_request, ctx, actor)
    print(out_response)
