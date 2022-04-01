from df_engine.core.keywords import GLOBAL, TRANSITIONS, RESPONSE
from df_engine.core import Context, Actor
import df_engine.conditions as cnd
from typing import Union

# create plot of dialog
plot = {
    GLOBAL: {
        TRANSITIONS: {
            ('global_flow', 'iamabot'): cnd.regexp(r'who are you')
        }
    },
    "global_flow": {
        'start_node': {
            RESPONSE: '',
            TRANSITIONS: {'iamabot': cnd.true()}
        },
        "iamabot": {RESPONSE: "I am an assistant for a DVD rental shop, I will help you rent a film"},
        "fallback_node": {RESPONSE: "I don't get it. Could you try again?"},
    },
    'genre_recommendation_flow': {
        'start_node': {
            RESPONSE: '',
            TRANSITIONS: {
                'iamabot': cnd.true()
            },
        },
        'iamabot': {
            RESPONSE: ''
        }
    }
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
