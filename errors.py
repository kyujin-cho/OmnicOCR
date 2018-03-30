class DataNotFoundError(Exception):
    def __str__(self):
        return "Requested data not found"

class UnauthorizedError(Exception):
    def __str__(self):
        return "Unauthorized Authentication Key"

class TooManyRequestsError(Exception):
    def __str__(self):
        return "Too many request to server!"

class PUBGUnknownError(Exception):
    def __str__(self):
        return "Unknown Error from server"
