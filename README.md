# CanvasReminderSkill

For use with Amazon Alexa and Clemson students. Loads upcoming calendar events and reads out due dates for today and tomorrow.
Designed to be used with routines so it can be automatically played upon starting the day.

## Requirements:
- Python 3.9
- AWS Dev Account
- AWS CLI
- "zip" CLI command

## Building + Deploying
This is designed to be deployed with AWS lambda to a function named "CanvasDailyReminderSkill." The intent to target is called "DailyIntent."

Run `pip install -r requirements.txt` and then `./deploy` to get started. An environmental variable named CANVAS_API_TOKEN **must** be populated with an access token from Canvas in order for the program to run.

## Usage
"Alexa, ask <skill launch name> <intent phrases>."

ex. "Alexa, ask canvas reminders what's due."
