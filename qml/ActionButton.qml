import QtQuick
import QtQuick.Controls

Button {
    id: control
    property color accent: "#83a6ae"
    implicitHeight: 38
    implicitWidth: Math.max(80,contentItem.implicitWidth+26)
    font.family: "DejaVu Sans Mono"
    font.pixelSize: 12
    contentItem: Text {
        text: control.text; font: control.font; color: control.enabled ? "#d5e0e3" : "#657078"
        horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
    background: Rectangle {
        color: control.down ? "#344650" : control.hovered ? "#27363f" : "#1c282f"
        border.width: 1; border.color: control.activeFocus ? "#e6b17e" : control.hovered ? control.accent : "#3b4c56"
        Behavior on color { ColorAnimation { duration: 120 } }
    }
}
