#!/usr/bin/env python3
"""Exercise actual QML components, actual videos and the Python service.
Optional PySide6 required. Render on a GL-capable display or Qt offscreen.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
os.environ.setdefault('QT_QUICK_CONTROLS_STYLE','Basic')
os.environ.setdefault('QT_AUDIO_BACKEND','pulseaudio')
from PySide6.QtCore import QUrl, QObject, QPoint, Qt, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickWindow, QQuickItem
from PySide6.QtQml import QQmlApplicationEngine, QQmlExpression, QQmlEngine
from PySide6.QtTest import QTest
from preview import Bridge, ROOT


def main():
    errors=[]
    def handler(kind,context,message):
        if any(s in message for s in ('TypeError','ReferenceError','Unable to assign','Binding loop','failed to load component')):errors.append(message)
        if not message.startswith(('Input #','  ','qt.multimedia')):print(message,file=sys.stderr)
    qInstallMessageHandler(handler)
    with tempfile.TemporaryDirectory(prefix='dsd-ui-') as tmp:
        for var,name in [('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data'),('XDG_STATE_HOME','state')]:os.environ[var]=str(Path(tmp)/name)
        application=QGuiApplication(sys.argv);bridge=Bridge();engine=QQmlApplicationEngine();engine.rootContext().setContextProperty('bridge',bridge)
        engine.load(QUrl.fromLocalFile(str(ROOT/'qml/Preview.qml')))
        assert engine.rootObjects(),'QML root failed to load'
        window=engine.rootObjects()[0];state=window.findChild(QObject,'appState')
        def js(code,obj=state):
            e=QQmlExpression(QQmlEngine.contextForObject(obj),obj,code);result=e.evaluate()
            if e.hasError():raise AssertionError(e.error().toString())
            return result[0] if isinstance(result,tuple) else result
        def wait(ms=500):QTest.qWait(ms)
        def value(prop):return state.property(prop)
        try:
            wait(1600);assert value('ready')
            def walk(item):
                yield item
                for child in item.childItems(): yield from walk(child)
            cards=[next((item for item in walk(window.contentItem()) if item.objectName()=='panel-cam-'+str(i)),None) for i in range(1,7)]
            assert all(cards)
            js('config.performance.autoPowerSave=false; config=Object.assign({},config)')
            for _ in range(80):
                if all(js('player.position',c)>0 for c in cards):break
                wait(200)
            for card in cards:
                print(card.objectName(),js('JSON.stringify({play:shouldPlay,state:player.playbackState,pos:player.position,status:player.mediaStatus,width:width,height:height})',card))
                assert js('player.error',card)==0
                assert js('player.position',card)>0,'Video timeline did not advance'
            capture=Path(os.environ.get('DSD_TEST_ARTIFACTS',str(ROOT/'work/test-artifacts')));capture.mkdir(parents=True,exist_ok=True)
            window.grabWindow().save(str(capture/'desktop.png'))
            # Click an actual panel, not a simulated controller.
            QTest.mouseClick(window,Qt.LeftButton,Qt.NoModifier,QPoint(250,250));wait()
            assert value('activePanel')=='cam-1'
            menu=window.findChild(QQuickItem,'sceneMenu');assert menu.isVisible()
            assert js('JSON.stringify(dialogLines)')!='[]','Offline greeting absent'
            window.grabWindow().save(str(capture/'expanded.png'))
            js("select(config.panels[1],'preview')");wait(650)
            assert value('activePanel')=='cam-2'
            assert sum(1 for c in cards if c.property('selected'))==1
            # Check actual geometry at multiple viewport sizes including portrait.
            for w,h in [(800,600),(1920,1080),(720,1100),(1024,768)]:
                window.resize(w,h);wait(400)
                for item in (cards[1],menu):
                    pt=item.mapToScene(QPoint(0,0));assert pt.x()>=0 and pt.y()>=0
                    assert pt.x()+item.width()<=w+1 and pt.y()+item.height()<=h+1
            window.resize(1440,900);wait()
            # Accelerate the existing elapsed clock: same connection state logic as real timer.
            js('expandedAt=Date.now()-(app.config.connection.seconds+app.config.connection.interferenceSeconds+1)*1000',cards[1]);wait(300)
            assert cards[1].property('lost') is True
            window.grabWindow().save(str(capture/'connection-lost.png'))
            js('reconnectSerial++');wait(400);assert cards[1].property('lost') is False
            QTest.keyClick(window,Qt.Key_Escape);wait();assert value('activePanel')==''
            state.setProperty('settingsVisible',True);wait(650)
            settings=next((w for w in application.allWindows() if 'Centro de control' in w.title()),None)
            assert settings is not None,'Settings window did not open'
            # Visit every section. Controls must instantiate without warnings.
            for i in range(8):
                settings.setProperty('sectionIndex',i);wait(180)
            settings.setProperty('sectionIndex',2);wait(500);settings.grabWindow().save(str(capture/'settings.png'))
            js('draft.appearance.gap=8; draft.panels[0].scene="market"; refresh(); apply(null)',settings);wait(700)
            assert Path(tmp,'config/dystopian-surveillance/config.json').is_file()
            saved=json.loads(Path(tmp,'config/dystopian-surveillance/config.json').read_text());assert saved['appearance']['gap']==8
            assert saved['panels'][0]['scene']=='market'
            # Import the bundled clip through the real async service, then assign via GUI callback.
            js('send("import",{path:'+json.dumps(str(ROOT/'assets/scenes/alley/scene.mp4'))+',name:"Prueba GUI",category:"Interiores"})')
            for _ in range(200):
                wait(200)
                if js('panel.scene',settings).startswith('import-'):break
            assert js('panel.scene',settings).startswith('import-')
            js('apply(null)',settings);wait(500)
            saved=json.loads(Path(tmp,'config/dystopian-surveillance/config.json').read_text())
            assert saved['panels'][0]['scene'].startswith('import-')
            assert not errors,'\n'.join(errors)
            print('PASS: real QML load, six video timelines, clicks, one menu, offline dialogue, four geometries, disconnect/reconnect, Escape, eight settings pages, scene replacement, real async import, saved settings')
        finally:
            bridge.close()
            for w in application.allWindows():w.close()
        return 0

if __name__=='__main__':raise SystemExit(main())
