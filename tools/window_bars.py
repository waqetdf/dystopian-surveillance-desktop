#!/usr/bin/env python3
"""Opt-in Hyprbars integration. Keep other Hyprland settings intact."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import time

BEGIN='# BEGIN DSD WINDOW BARS'
END='# END DSD WINDOW BARS'
BLOCK='''# BEGIN DSD WINDOW BARS
exec-once = hyprpm reload
plugin {
    hyprbars {
        bar_height = 28
        bar_color = rgb(152028)
        col.text = rgb(d5e0e6)
        bar_text_font = DejaVu Sans
        bar_text_size = 11
        bar_buttons_alignment = right
        hyprbars-button = rgb(b85757), 18, ×, hyprctl dispatch killactive
    }
}
# END DSD WINDOW BARS
'''

def configure(path, remove=False):
    if not path.is_file():raise ValueError('No existe '+str(path)+'. Indica tu archivo con --config.')
    old=path.read_text()
    if BEGIN in old:
        if BLOCK not in old:raise ValueError('El bloque de barras fue modificado. Consérvalo o edítalo manualmente.')
        new=old.replace(BLOCK,'') if remove else old
    else:
        if remove:return
        if 'hyprbars' in old:raise ValueError('Ya existe configuración de hyprbars; no se sobrescribe.')
        new=old+('' if old.endswith('\n') else '\n')+BLOCK
    if new==old:return
    backup=path.with_name(path.name+'.dsd-bars-'+str(time.time_ns())+'.bak')
    shutil.copy2(path,backup)
    temporary=path.with_name(path.name+'.dsd-bars.tmp')
    try:
        with temporary.open('x') as f:f.write(new)
        shutil.copymode(path,temporary)
        temporary.replace(path)
    finally:
        if temporary.exists():temporary.unlink()
    print('Copia de seguridad:',backup)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--remove',action='store_true')
    parser.add_argument('--config',type=Path,default=Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))/'hypr/hyprland.conf')
    args=parser.parse_args()
    if os.geteuid()==0:raise ValueError('Ejecuta como usuario normal, sin sudo.')
    if not args.config.is_file():raise ValueError('No se encuentra hyprland.conf; utiliza --config RUTA.')
    if not os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'):raise ValueError('Ejecuta dentro de tu sesión Hyprland.')
    if not args.remove:
        for binary in ('hyprctl','pacman'):
            if not shutil.which(binary):raise ValueError('Falta '+binary)
        # Hyprpm builds the official plugin revision for the running compositor.
        subprocess.run(['sudo','pacman','-Syu','--needed','hyprpm','base-devel','cmake','meson','ninja','git','cpio','pkgconf'],check=True)
        listing=subprocess.check_output(['hyprpm','list'],text=True)
        if 'hyprbars' not in listing:
            subprocess.run(['hyprpm','add','https://github.com/hyprwm/hyprland-plugins'],check=True)
        subprocess.run(['hyprpm','enable','hyprbars'],check=True)
        subprocess.run(['hyprpm','reload'],check=True)
    configure(args.config,args.remove)
    subprocess.run(['hyprctl','reload'],check=True)
    print('Configuración retirada; el plugin compartido se conserva.' if args.remove else 'Barras configuradas. Comprueba la × en Kitty y otras ventanas normales.')
    print('Si una aplicación usa pantalla completa, sal de ella para ver la barra.')

if __name__=='__main__':
    try:main()
    except (ValueError,OSError,subprocess.CalledProcessError) as e:
        print('No se completó la configuración:',e)
        raise SystemExit(1)
