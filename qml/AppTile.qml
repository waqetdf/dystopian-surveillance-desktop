import QtQuick
import QtQuick.Controls

AbstractButton {
    id:tile
    required property var entry
    implicitWidth:90
    implicitHeight:104
    enabled:!!entry
    hoverEnabled:true
    Accessible.name:entry?entry.name:"Aplicación"
    property var themes:({terminal:["#304452",">_"],browser:["#238bcb","◎"],files:["#d99536","▤"],media:["#bc5062","▶"],monitor:["#418b78","▥"],settings:["#718494","⚙"]})
    property var theme:themes[entry?entry.id:""] || ["#5669a4","✦"]
    property string iconValue:entry?(entry.icon||""):""
    property bool imageIcon:iconValue.startsWith("file:") || iconValue.startsWith("/")
    background:Rectangle { radius:10;color:tile.hovered?"#22333f":"transparent";border.width:tile.activeFocus?1:0;border.color:"#a4ced7" }
    contentItem:Column {
        spacing:8
        Rectangle {
            anchors.horizontalCenter:parent.horizontalCenter
            width:58;height:58;radius:13
            scale:tile.down?.92:tile.hovered?1.05:1
            Behavior on scale { NumberAnimation { duration:120 } }
            gradient:Gradient {
                GradientStop { position:0;color:Qt.lighter(tile.theme[0],1.25) }
                GradientStop { position:1;color:tile.theme[0] }
            }
            border.color:Qt.lighter(tile.theme[0],1.45)
            Image {
                id:customIcon
                anchors.fill:parent;anchors.margins:7
                source:tile.imageIcon?tile.iconValue:(tile.themes[tile.entry?tile.entry.id:""] && (!tile.iconValue || tile.iconValue===tile.theme[1]) ? Qt.resolvedUrl("icons/"+tile.entry.id+".svg") : "")
                fillMode:Image.PreserveAspectFit
                sourceSize.width:64;sourceSize.height:64
            }
            Text {
                anchors.centerIn:parent
                visible:customIcon.status!==Image.Ready
                text:tile.imageIcon?tile.theme[1]:(tile.iconValue||tile.theme[1])
                color:"#ffffff";font.pixelSize:28;font.bold:true
                width:48;horizontalAlignment:Text.AlignHCenter;elide:Text.ElideRight
            }
        }
        Text {
            width:parent.width;text:tile.entry?tile.entry.name:""
            color:"#d5e0e6";font.pixelSize:11
            horizontalAlignment:Text.AlignHCenter;wrapMode:Text.Wrap
            maximumLineCount:2;elide:Text.ElideRight
        }
    }
    ToolTip.visible:hovered
    ToolTip.text:entry?entry.name:""
    ToolTip.delay:600
}
