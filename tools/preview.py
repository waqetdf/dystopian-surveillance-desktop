#!/usr/bin/env python3
"""Runs the REAL UI and local service in a normal Qt window, without layer-shell.
Developer aid only: this does not certify Hyprland integration.
Requires optional PySide6 (Arch: pyside6).
"""
import os
import sys
from pathlib import Path
from PySide6.QtCore import QObject, Signal, Slot, QProcess, QUrl, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickWindow
from PySide6.QtQml import QQmlApplicationEngine

ROOT=Path(__file__).resolve().parents[1]

class Bridge(QObject):
    message=Signal(str)
    def __init__(self):
        super().__init__(); self.buffer=b'';self.process=QProcess(self)
        self.process.readyReadStandardOutput.connect(self.read)
        self.process.readyReadStandardError.connect(lambda:sys.stderr.write(bytes(self.process.readAllStandardError()).decode()))
    @Slot()
    def start(self): self.process.start(sys.executable,[str(ROOT/'backend/service.py')])
    @Slot(str)
    def send(self, msg): self.process.write((msg+'\n').encode())
    def read(self):
        self.buffer+=bytes(self.process.readAllStandardOutput())
        while b'\n' in self.buffer:
            line,self.buffer=self.buffer.split(b'\n',1);self.message.emit(line.decode())
    def close(self):
        self.process.closeWriteChannel()
        if not self.process.waitForFinished(3000): self.process.kill();self.process.waitForFinished()


def main():
    os.environ.setdefault('QT_QUICK_CONTROLS_STYLE','Basic')
    app=QGuiApplication(sys.argv); bridge=Bridge();engine=QQmlApplicationEngine()
    engine.rootContext().setContextProperty('bridge',bridge)
    engine.load(QUrl.fromLocalFile(str(ROOT/'qml/Preview.qml')))
    if not engine.rootObjects(): return 1
    app.aboutToQuit.connect(bridge.close)
    # Opt-in capture for reproducible local smoke tests.
    if os.environ.get('DSD_CAPTURE'):
        def capture():
            engine.rootObjects()[0].grabWindow().save(os.environ['DSD_CAPTURE']); app.quit()
        QTimer.singleShot(5000,capture)
    return app.exec()

if __name__=='__main__':raise SystemExit(main())
