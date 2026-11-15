import QtQuick
import QtQuick.Controls

Button {
    id:control
    property string label:"Ajustes"
    implicitWidth:30
    implicitHeight:30
    hoverEnabled:true
    Accessible.name:label
    ToolTip.visible:hovered
    ToolTip.delay:450
    ToolTip.text:label
    contentItem:Item {
        Image {
            anchors.centerIn:parent
            width:18;height:18
            source:"icons/settings.svg"
            sourceSize.width:36;sourceSize.height:36
            opacity:control.enabled?0.85:0.4
        }
    }
    background:Rectangle {
        radius:5
        color:control.down?"#344650":control.hovered?"#27363f":"transparent"
        border.width:control.activeFocus?1:0
        border.color:"#e6b17e"
    }
}
