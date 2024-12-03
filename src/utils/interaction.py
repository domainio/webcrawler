from typing import TypeVar, Callable, Any
from tqdm import tqdm

T = TypeVar('T')

def with_progress_bar(operation: Callable[..., T], 
                 desc: str = None,
                 total: int = None) -> T:
    """Wrap an operation with a progress bar."""
    with tqdm(desc=desc, total=total) as pbar:
        result = operation()
        if total is None:
            pbar.update(1)
        return result
