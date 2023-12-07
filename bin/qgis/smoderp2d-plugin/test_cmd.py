import sys
sys.path.append(r'C:\Users\martin\Documents\GitHub\smoderp2d\bin\qgis\smoderp2d-plugin')

from connect_grass import find_grass_bin

grass_bin = find_grass_bin()

import grass.script.setup as gsetup

gisdb = r"C:\Users\martin\Documents\grassdata"
gsetup.init(gisdb, "world_latlong_wgs84", 'PERMANENT')

from grass.pygrass.modules import Module as GrassModule

class Module:
    def __init__(self, *args, **kwargs):
        if sys.platform == 'win32':
            import subprocess
            
            si = subprocess.STARTUPINFO()
            si.dwFlags = subprocess.CREATE_NEW_CONSOLE | subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
            #m = GrassModule(*args, **kwargs, run_=False)
            # # very ugly hack of m.run()
            #m._finished = False
            #if m.inputs["stdin"].value:
            #    m.stdin = m.inputs["stdin"].value
            #    m.stdin_ = subprocess.PIPE
            #m.start_time = time.time()
            # cmd = m.make_cmd()
            # cmd = [shutil.which(cmd[0])] + cmd[1:]
            cmd = list(args)
            for p, v in kwargs.items():
                if p == 'overwrite' and v is True:
                    cmd.append(f'--{p}')
                elif p == "flags":
                    cmd.append(f"-{v}")
                else:
                    cmd.append(f"{p}={v}")
            print(cmd)
            with open(r"C:\users\martin\cmd.bat", "w") as fd:
                 # fd.write("chcp {self._getWindowsCodePage()}>NUL\n")
                 fd.write(' '.join(cmd))
            with subprocess.Popen( #gs.core.Popen(
                 r"C:\users\martin\cmd.bat",
            #     shell=False,
            #     universal_newlines=True,
            #     stdin=subprocess.DEVNULL,
            #     stdout=subprocess.PIPE,
            #     stderr=subprocess.STDOUT,
            #     env=m.env_,
            startupinfo=si
            ) as x:
                pass
            #     for line in iter(lambda: self._readline_with_recover(m._popen.stdout), ''):
            #         QgsMessageLog.logMessage(line, 'SMODERP2D', level=Qgis.Info)

from subprocess import PIPE
Module("g.region", n=90, s=0, w=0, e=100, res=0.03, flags="p")
Module("r.random.surface", output="x", overwrite=True)
print("done")