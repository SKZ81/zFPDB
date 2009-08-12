class DuplicateError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class FpdbError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class FpdbParseError(Exception): 
    def __init__(self,value='',hid=''):
        self.value = value
        self.hid = hid
    def __str__(self):
        if hid:
            return repr("HID:"+hid+", "+self.value)
        else:
            return repr(self.value)


