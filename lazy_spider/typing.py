from typing import Dict, Callable


T_Headers = Dict[str, str]
T_Sleeper = Callable
T_Headers_Generator = Callable[[], T_Headers]
