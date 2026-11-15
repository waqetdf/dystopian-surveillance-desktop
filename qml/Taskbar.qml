import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland

PanelWindow {
    id:bar
    required property var app
    anchors { left:true;right:true;bottom:true }
    implicitHeight:48
    exclusiveZone:48
    WlrLayershell.layer:WlrLayer.Top
    WlrLayershell.namespace:"dystopian-taskbar"
    WlrLayershell.keyboardFocus:WlrKeyboardFocus.None
    color:"#111b22"
    RowLayout {
        anchors.fill:parent;anchors.margins:5;spacing:6
        ActionButton { text:bar.app.ready?bar.app.config.labels.settings:"Ajustes";onClicked:bar.app.openSettings() }
        ScrollView {
            Layout.fillWidth:true;Layout.fillHeight:true
            contentWidth:tasks.implicitWidth;contentHeight:38
            clip:true
            ScrollBar.vertical.policy:ScrollBar.AlwaysOff
            Row {
                id:tasks;spacing:5
                Repeater {
                    model:ToplevelManager.toplevels
                    Row {
                        required property var modelData
                        spacing:1
                        ActionButton {
                            width:Math.min(190,Math.max(100,bar.width/5));height:38
                            text:modelData.title || modelData.appId || "Ventana"
                            accent:modelData.activated?"#e6b17e":"#83a6ae"
                            onClicked:{modelData.minimized=false;modelData.activate();}
                            ToolTip.visible:hovered;ToolTip.text:text
                        }
                        ActionButton {
                            width:32;implicitWidth:32;text:"□"
                            Accessible.name:"Pantalla completa / restaurar"
                            onClicked:modelData.fullscreen=!modelData.fullscreen
                            ToolTip.visible:hovered;ToolTip.text:"Pantalla completa / restaurar"
                        }
                        ActionButton {
                            width:32;implicitWidth:32;text:"×";accent:"#e99588"
                            Accessible.name:"Cerrar "+(modelData.title || "ventana")
                            onClicked:modelData.close()
                            ToolTip.visible:hovered;ToolTip.text:"Cerrar ventana"
                        }
                    }
                }
            }
        }
        Text { text:Qt.formatTime(new Date(),"hh:mm");color:"#b4c8d0";id:clock }
        Timer { interval:1000;running:true;repeat:true;onTriggered:clock.text=Qt.formatTime(new Date(),"hh:mm") }
    }
}
