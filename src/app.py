import mmh3
from bitarray import bitarray
from fastapi import FastAPI

# Initializing the fast api class
app = FastAPI()


# Model : URL
class URL:
    def __init__(self, url_string: str) -> None:
        self.url = url_string
    
    def __repr__(self):
        return str(self.url)
    

class BloomFilter:

    def __init__(self, size: int, hash_size: int) -> None:
        self.size = size
        self.hash_size = hash_size
        self.bit_array = bitarray(size)
        self.bit_array.setall(0)
    
    def add(self, url: URL) -> bool:
        
        for each in range(self.hash_size):
            index = mmh3.hash(url.url, each) % self.size
            self.bit_array[index] = 1

        return True

    def check(self, url: URL) -> bool:
        for each in range(self.hash_size):
            index = mmh3.hash(url.url, each) % self.size
            if self.bit_array[index] == 0:
                return False
        return True
    
@app.get("/")
def homepage():
    return {'data' : 'request recieved and response has been shared'}


