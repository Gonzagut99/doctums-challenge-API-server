class ResponseModel:
    def __init__(self, message:str, code:int, data:any=None, error:bool=False, detail:any=None):
        self.data:any = data
        self.message:str = message
        self.code:int = code
        self.error:bool = error
        self.detail:any = detail

    def get_serialized_response(self):
        return {
            'code': self.code,
            'message': self.message,
            'data': self.data,
            'error': self.error,
            'detail': self.detail
        }