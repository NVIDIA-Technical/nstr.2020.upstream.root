
## Rate Limiter
from slowapi import Limiter
from slowapi.util import get_remote_address
limiter = Limiter(key_func=get_remote_address)

## Logarithmic slider to file size
import math
def logSliderToSize(position):
    """Convert slider position to file size in KB"""
    maxp = 500
    minv = math.log(1)
    maxv = math.log(102400)
    
    return round(math.exp(minv + (maxv - minv) * pow(position / maxp, 1.5))) * 1024