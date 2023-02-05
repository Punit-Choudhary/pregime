import os
from twilio.rest import Client

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']

client = Client(account_sid, auth_token)


def make_call(name, phno):
  call = client.calls.create(method='GET', url=f'https://handler.twilio.com/twiml/EH3c4ea76261d0149a7a96c0ec655274b8?Name={name}', to=phno, from_='+17753464379')

  print("Calling, SID: " + str(call.sid))


def send_sms(name, phno, map):
  message_body = f"""
  Hello from Pregime,
  this is a emergency call regarding pregnancy of
  Your friend {name}, she needs your help, kindly contact her. 
  Her last location at the time of emergency was {map}
  """

  message = client.messages.create(body=message_body, to=phno, from_='+17753464379')

  print("Message sent with the SID: " + str(message.sid))
