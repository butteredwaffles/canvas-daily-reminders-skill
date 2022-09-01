import os
import re
import traceback
from dataclasses import dataclass
from datetime import datetime, timedelta

import pytz
from ask_sdk.standard import StandardSkillBuilder
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_model import Response
from ask_sdk_model.ui import SimpleCard, AskForPermissionsConsentCard
from canvasapi import Canvas
from pytz import timezone

eastern = timezone('US/Eastern')
sb = StandardSkillBuilder()
course_pattern = re.compile(r"(?:\d-)*(\w{3,4}-\d{4}.+?)\s-")


@dataclass
class Assignment:
    end_date: datetime
    pretty_date: str
    class_name: str
    assignment_name: str


def get_events():
    API_URL = "https://clemson.instructure.com"
    API_KEY = os.environ['CANVAS_API_TOKEN']

    canvas = Canvas(API_URL, API_KEY)
    assignments = []
    todays = 0
    tomorrows = 0
    for event in canvas.get_upcoming_events():
        time = datetime.fromisoformat(event["end_at"][:-1]).replace(tzinfo=pytz.UTC).astimezone(eastern)
        assignment_name = event['title']
        pretty_time = time.strftime("%A, %B %d, %Y @ %I:%M%p")
        class_name = event["context_name"]
        class_filtered = course_pattern.search(class_name)
        tomorrow = (datetime.now().replace(hour=23, minute=59, second=59) + timedelta(days=1)).astimezone(eastern)
        if class_filtered:
            class_name = class_filtered.group(1)
        if (time <= tomorrow) and 'assignment' in event:
            assignments.append(Assignment(time, pretty_time, class_name, assignment_name))
    return assignments


@sb.request_handler(can_handle_func=is_intent_name("DailyIntent"))
@sb.request_handler(can_handle_func=is_request_type("LaunchRequest"))
def hello_world_intent_handler(handler_input):
    # type: (HandlerInput) -> Response
    request_envelope = handler_input.request_envelope
    permissions = request_envelope.context.system.user.permissions
    try:
        name = handler_input.service_client_factory.get_ups_service().get_profile_given_name()
    except Exception as e:
        traceback.print_exc()
        name = "human"
    assignments = get_events()
    if not (permissions and permissions.consent_token):
        return (handler_input.response_builder.speak(
            "Please give permissions to speak your given name using the alexa app.")
                .set_card(AskForPermissionsConsentCard(permissions=["alexa::profile:given_name:read"]))
                .response)
    speech_text = f"Hello {name}! Here's your due assignments: "
    todays = 0
    for assignment in assignments:
        date = 'today' if datetime.now(tz=eastern).day == assignment.end_date.day else 'tomorrow'
        if date == 'today':
            todays += 1
        speech_text += f"<emphasis>{assignment.assignment_name}</emphasis> for {assignment.class_name}, is due {date} at {assignment.end_date.strftime('%I:%M%p')}. <break time=\"1s\"/>"
    num_assignments = len(assignments)
    if num_assignments == 0:
        "You don't have anything due today or tomorrow! Lucky! "
    else:
        if todays == 0:
            speech_text += "You don't have anything due today."
        if num_assignments - todays == 0:
            speech_text += "You don't have anything due tomorrow. "
    speech_text += "Good luck!"
    handler_input.response_builder.speak(speech_text).set_card(
        SimpleCard("Assignments", speech_text)).set_should_end_session(
        True)
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.HelpIntent"))
def help_intent_handler(handler_input):
    # type: (HandlerInput) -> Response
    speech_text = "You can say hello to me!"

    handler_input.response_builder.speak(speech_text).ask(speech_text).set_card(
        SimpleCard("Hello World", speech_text))
    return handler_input.response_builder.response


@sb.request_handler(
    can_handle_func=lambda handler_input:
    is_intent_name("AMAZON.CancelIntent")(handler_input) or
    is_intent_name("AMAZON.StopIntent")(handler_input))
def cancel_and_stop_intent_handler(handler_input):
    # type: (HandlerInput) -> Response
    speech_text = "Goodbye!"

    handler_input.response_builder.speak(speech_text).set_card(
        SimpleCard("Hello World", speech_text)).set_should_end_session(
        True)
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_request_type("SessionEndedRequest"))
def session_ended_request_handler(handler_input):
    # type: (HandlerInput) -> Response
    # any cleanup logic goes here

    return handler_input.response_builder.response


@sb.exception_handler(can_handle_func=lambda i, e: True)
def all_exception_handler(handler_input, exception):
    # type: (HandlerInput, Exception) -> Response
    # Log the exception in CloudWatch Logs
    print(traceback.format_exc())

    speech = "Oops. Had an exception."
    handler_input.response_builder.speak(speech)
    return handler_input.response_builder.response


lambda_handler = sb.lambda_handler()
