import os
from twilio.rest import Client

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']

client = Client(account_sid, auth_token)


def make_call(name, phno):
  call = client.calls.create(method='GET', url=f'https://handler.twilio.com/twiml/EH3c4ea76261d0149a7a96c0ec655274b8?Name={name}', to=phno, from_='+17753464379')

  print("Calling, SID: " + str(call.sid))


def send_sms(name, phno):
  message_body = f"""
  Hey {name}
  Hello Pregime :)
  """

  message = client.messages.create(body=message_body, to=phno, from_='+17753464379')

  print("Message sent with the SID: " + str(message.sid))

# make_call("Reema", "")