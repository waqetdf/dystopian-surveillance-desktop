"""Low frequency /proc sampling; no recurring GPU utility subprocess."""
from pathlib import Path
import os


class Metrics:
    def __init__(self): self.last=None
    def read(self):
        result={'cpu':None,'ramUsedMiB':None,'ramTotalMiB':None,'gpu':None,'rssMiB':None,'batteryLow':False,'fullscreen':False}
        try:
            values=[int(v) for v in Path('/proc/stat').read_text().splitlines()[0].split()[1:9]]
            total=sum(values); idle=values[3]+values[4]
            if self.last:
                delta=total-self.last[0]
                result['cpu']=round(100*(1-(idle-self.last[1])/delta),1) if delta else 0
            self.last=(total,idle)
            mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()}
            result['ramTotalMiB']=round(mem['MemTotal']/1024)
            result['ramUsedMiB']=round((mem['MemTotal']-mem['MemAvailable'])/1024)
            result['rssMiB']=round(int(Path('/proc/self/statm').read_text().split()[1])*os.sysconf('SC_PAGE_SIZE')/1048576,1)
        except (OSError,ValueError,KeyError): pass
        for p in Path('/sys/class/drm').glob('card*/device/gpu_busy_percent'):
            try: result['gpu']=float(p.read_text()); break
            except (OSError,ValueError): pass
        for p in Path('/sys/class/power_supply').glob('*'):
            try:
                if (p/'type').read_text().strip()=='Battery' and (p/'status').read_text().strip()=='Discharging' and int((p/'capacity').read_text())<20: result['batteryLow']=True
            except (OSError,ValueError): pass
        return result
