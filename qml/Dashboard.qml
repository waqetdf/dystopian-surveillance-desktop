import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "Geometry.js" as Geometry

Rectangle {
    id: desk
    required property var app
    property string screenName: "preview"
    property bool obscured: false
    property var active: app.ready ? app.config.panels.find(p=>p.id===app.activePanel) : null
    property bool hasActive: !!active && app.activeScreen===screenName
    property var arrangement: hasActive ? Geometry.arrange(active, feeds.width, feeds.height) : ({x:0,y:0,w:0,h:0,mx:0,my:0,mw:0,mh:0})
    color:app.ready?app.config.appearance.background:"#10171c"
    Rectangle { height:2;width:parent.width;color:app.ready?app.config.appearance.accent:"#83a6ae";opacity:.65 }
    RowLayout {
        x:18;y:12;width:parent.width-36;height:32
        Column {
            Text { text:desk.app.ready?desk.app.config.labels.title:""; color:"#c6d2d7";font.family:"DejaVu Sans Mono";font.pixelSize:14;font.bold:true }
            Text { text:desk.app.ready?desk.app.config.labels.subtitle:"";color:"#718b98";font.family:"DejaVu Sans Mono";font.pixelSize:9 }
        }
        Item { Layout.fillWidth:true }
        Text { visible:desk.width>720;text:clock.text; color:"#8da4af";font.family:"DejaVu Sans Mono";font.pixelSize:12 }
        ActionButton { objectName:"settingsButton";text:desk.app.ready?desk.app.config.labels.settings:"";onClicked:desk.app.openSettings() }
    }
    Item {
        id:feeds;x:12;y:59;width:parent.width-24;height:parent.height-93
        Repeater {
            model:desk.app.ready ? desk.app.config.panels : []
            VideoPanel {
                required property var modelData
                app:desk.app; panel:modelData
                objectName:"panel-"+modelData.id
                selected:desk.hasActive && desk.app.activePanel===panel.id
                occluded:desk.obscured || (desk.hasActive && !selected)
                x:selected?desk.arrangement.x:panel.x*feeds.width+app.config.appearance.gap/2
                y:selected?desk.arrangement.y:panel.y*feeds.height+app.config.appearance.gap/2
                width:selected?desk.arrangement.w:Math.max(1,panel.w*feeds.width-app.config.appearance.gap)
                height:selected?desk.arrangement.h:Math.max(1,panel.h*feeds.height-app.config.appearance.gap)
                z:selected?3:0
                opacity:desk.hasActive && !selected?.24:1
                Behavior on x { NumberAnimation { duration:desk.app.config.appearance.transitionMs;easing.type:Easing.InOutCubic } }
                Behavior on y { NumberAnimation { duration:desk.app.config.appearance.transitionMs;easing.type:Easing.InOutCubic } }
                Behavior on width { NumberAnimation { duration:desk.app.config.appearance.transitionMs;easing.type:Easing.InOutCubic } }
                Behavior on height { NumberAnimation { duration:desk.app.config.appearance.transitionMs;easing.type:Easing.InOutCubic } }
                Behavior on opacity { NumberAnimation { duration:180 } }
                onClicked:{ desk.forceActiveFocus(); desk.app.select(panel,desk.screenName); }
            }
        }
        Rectangle {
            id:menu;objectName:"sceneMenu";z:4
            visible:desk.hasActive
            x:desk.arrangement.mx;y:desk.arrangement.my;width:desk.arrangement.mw;height:desk.arrangement.mh
            color:"#152028";border.color:"#5c7886";border.width:1
            property var scene:desk.app.scene(desk.app.activeScene)
            ScrollView {
                anchors.fill:parent;anchors.margins:16;clip:true;contentWidth:availableWidth
                ColumnLayout {
                    width:menu.width-32;spacing:12
                    RowLayout {
                        Layout.fillWidth:true
                        Label { text:desk.app.ready?desk.app.config.labels.uplink:"";color:"#91b9b5";font.pixelSize:10;Layout.fillWidth:true }
                        ActionButton { text:"× Cerrar";implicitWidth:90;onClicked:desk.app.close() }
                    }
                    Label { text:menu.scene?menu.scene.name:"";font.pixelSize:22;color:"#d1d9db";wrapMode:Text.Wrap;Layout.fillWidth:true }
                    Label { text:menu.scene?menu.scene.personality:"";font.pixelSize:11;color:"#8da0a9";wrapMode:Text.Wrap;Layout.fillWidth:true }
                    Rectangle { Layout.fillWidth:true;height:1;color:"#3a4c56" }
                    GridLayout {
                        Layout.fillWidth:true
                        columns:Math.max(1, Math.min(4, Math.floor(width/90)))
                        columnSpacing:10;rowSpacing:16
                        Repeater {
                            model:menu.scene?menu.scene.apps:[]
                            AppTile {
                                required property string modelData
                                entry:desk.app.ready?desk.app.config.apps.find(a=>a.id===modelData):null
                                objectName:"app-tile-"+modelData
                                Layout.fillWidth:true
                                onClicked:desk.app.send("launch",{scene:desk.app.activeScene,app:modelData})
                            }
                        }
                    }
                    ActionButton { Layout.fillWidth:true;text:desk.app.ready?desk.app.config.labels.talk:"";onClicked:desk.app.send("talk",{scene:desk.app.activeScene}) }
                    TextField { id:prompt;visible:desk.app.ready&&desk.app.config.ai.enabled;placeholderText:"Mensaje al personaje…";Layout.fillWidth:true;maximumLength:4000 }
                    ActionButton { visible:prompt.visible;text:"Enviar a IA activada";Layout.fillWidth:true;enabled:prompt.text.trim().length>0;onClicked:{desk.app.send("ai",{scene:desk.app.activeScene,text:prompt.text});prompt.clear();} }
                    Label { text:"ESC para cerrar  /  conexión ficticia";color:"#6d8795";font.pixelSize:9;Layout.fillWidth:true;wrapMode:Text.Wrap }
                }
            }
        }
    }
    RowLayout {
        x:18;anchors.bottom:parent.bottom;anchors.bottomMargin:9;width:parent.width-36
        Text { text:(desk.app.economy?"● AHORRO":"● ONLINE")+"  /  "+(desk.app.ready?desk.app.config.panels.length:0)+" CANALES";color:"#7c9a9f";font.pixelSize:10;font.family:"DejaVu Sans Mono" }
        Item { Layout.fillWidth:true }
        Text { visible:desk.width>650;text:"CPU "+(desk.app.stats.cpu===null||desk.app.stats.cpu===undefined?"—":desk.app.stats.cpu+"%")+"   RAM "+(desk.app.stats.ramUsedMiB||"—")+" MiB   GPU "+(desk.app.stats.gpu===null||desk.app.stats.gpu===undefined?"N/D":desk.app.stats.gpu+"%");color:"#738d9a";font.pixelSize:10 }
    }
    Rectangle {
        z:10;visible:!!desk.app.notice;anchors.horizontalCenter:parent.horizontalCenter;anchors.bottom:parent.bottom;anchors.bottomMargin:40
        width:Math.min(parent.width-32,640);height:noticeText.implicitHeight+24;color:"#26343c";border.color:desk.app.noticeError?"#cd8c70":"#7faba9"
        Text { id:noticeText;x:12;y:12;width:parent.width-24;text:desk.app.notice;color:"#dbe2e3";wrapMode:Text.Wrap;font.pixelSize:12 }
        MouseArea { anchors.fill:parent;onClicked:desk.app.notice="" }
    }
    QtObject { id:clock;property string text:Qt.formatDateTime(new Date(),"ddd  dd.MM.yyyy  hh:mm:ss") }
    Timer { interval:1000;running:true;repeat:true;onTriggered:clock.text=Qt.formatDateTime(new Date(),"ddd  dd.MM.yyyy  hh:mm:ss") }
    Shortcut { sequence:"Escape"; enabled:desk.hasActive; context:Qt.WindowShortcut; onActivated:desk.app.close() }
    focus:true
    Keys.onEscapePressed:desk.app.close()
}
