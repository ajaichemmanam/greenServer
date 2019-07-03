#For auth Tokens
#pip install pyjwt
import jwt
import datetime
import json
#import os
#os.urandom(24)
SECRETKEY = "secretkey"

class plantData:
    def __init__(self, plantId, noLeaf, regions, maskArea, totalArea, greenPercentage, inputUrl, outputUrl, date):
        self.plantId = plantId
        self.noLeaf = noLeaf
        self.regions = regions
        self.maskArea =  maskArea
        self.totalArea = totalArea
        self.greenPercentage = greenPercentage
        self.inputUrl = inputUrl
        self.outputUrl = outputUrl
        self.date = date

def encode_auth_token(user_id, isAdmin):
    """
    Generates the Auth Token
    :return: string
    """
    try:
        payload = {
            'exp': datetime.datetime.now() + datetime.timedelta(days=0, seconds=300),
            'iat': datetime.datetime.now(),
            'user': user_id,
            'isAdmin': str(isAdmin)
        }
        return jwt.encode(
            payload,
            SECRETKEY,
            algorithm='HS256'
        )
    except Exception as e:
        return e

def decode_auth_token(auth_token):
    """
    Decodes the auth token
    :param auth_token:
    :return: integer|string
    """
    try:
        payload = jwt.decode(auth_token, SECRETKEY)
        return True, payload['user'], payload['isAdmin']
    except jwt.ExpiredSignatureError:
        return False, 'Signature expired. Please log in again.', ''
    except jwt.InvalidTokenError:
        return False, 'Invalid token. Please log in again.', ''