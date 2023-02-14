MESSAGE_LENGTH = 1024 # TODO: change this

def formatMessage(sender : str, recipient: str, messageBody: str):
    return f"{sender}|{recipient}|{messageBody}"