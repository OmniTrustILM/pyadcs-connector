class WinRMExecutionException(Exception):
    def __init__(self, status_code, std_err):
        self.status_code = status_code
        self.std_err = std_err
