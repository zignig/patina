import amaranth

import amaranth_soc
from  amaranth_soc.memory import MemoryMap, ResourceInfo

from rich.console import Console
from rich.table import Table

class ShowMap:
    def __init__(self,soc):
        self._soc = soc
        table = Table(title="devices")
        table.add_column("Path", justify="left", style="cyan", no_wrap=True)
        table.add_column("Start", style="magenta")
        table.add_column("End", style="magenta")
        
        mm = self._soc.memory_map
        for res in mm.all_resources():
            print(res)
            table.add_row(str(res.path),str(res.start),str(res.end))
        
        console = Console()
        console.print(table)
        