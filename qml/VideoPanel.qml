import QtQuick
import QtQuick.Controls
import QtMultimedia

Rectangle {
    id: card
    required property var app
    required property var panel
    property var scene: app.scene(panel.scene)
    property bool selected: false
    property bool occluded: false
    property bool preview: false
    property bool playingAllowed: true
    property real expandedAt: Date.now()
    property real elapsed: 0
    property real signalDamage: selected && app.config.connection.enabled ?
        Math.max(0,Math.min(1,(elapsed-app.config.connection.seconds)/app.config.connection.interferenceSeconds)) : 0
    property bool lost: signalDamage >= 1
    property bool shouldPlay: !!scene && scene.available !== false && playingAllowed && !lost && (!app.config.performance.pauseHidden || !occluded) &&
        (!app.economy || selected || preview)
    property string playbackError: ""
    property alias player: player
    signal clicked()
    color: "#080e13"; border.color: selected ? "#c29a75" : app.config.appearance.accent
    border.width: selected ? 2 : app.config.appearance.border
    clip: true
    onSelectedChanged: { elapsed=0; expandedAt=Date.now(); }
    Connections {
        target: card.app
        function onReconnectSerialChanged() { if(card.selected) {card.expandedAt=Date.now();card.elapsed=0;} }
    }
    onShouldPlayChanged: { if (shouldPlay) player.play(); else player.pause(); }
    Item {
        id: videoFrame
        anchors.fill: parent; anchors.margins: 3; anchors.topMargin: 27; anchors.bottomMargin: 23
        clip: true; visible: !card.lost
        VideoOutput {
            id: output
            width: parent.width*card.panel.scale; height: parent.height*card.panel.scale
            x: (parent.width-width)/2 + card.panel.offsetX*parent.width*.5
            y: (parent.height-height)/2 + card.panel.offsetY*parent.height*.5
            fillMode: card.panel.fit === "cover" ? VideoOutput.PreserveAspectCrop : VideoOutput.PreserveAspectFit
        }
        Rectangle { anchors.fill:parent; color:card.app.stats.ambient || "#395266"; opacity:card.app.config.appearance.ambient ? card.app.config.appearance.ambientIntensity : 0 }
        Repeater {
            model: card.app.config.appearance.crt && !card.app.economy ? Math.max(0,Math.ceil(videoFrame.height/4)) : 0
            Rectangle { required property int index; width:videoFrame.width; height:1; y:index*4; color:"#000000"; opacity:.16 }
        }
    }
    MediaPlayer {
        id: player
        source: card.scene ? card.scene.videoUrl : ""
        videoOutput: output
        audioOutput: AudioOutput { muted: card.panel.muted || !card.selected || card.preview; volume:.5 }
        loops: card.panel.loop ? MediaPlayer.Infinite : 1
        playbackRate: card.panel.speed
        onSourceChanged: { card.playbackError=""; if(card.shouldPlay) play(); }
        Component.onCompleted: { if(card.shouldPlay) play(); }
        onErrorOccurred: function(error,errorString) { card.playbackError=errorString; }
    }
    Text {
        anchors.centerIn:parent; width:parent.width-30; wrapMode:Text.Wrap; color:"#ce9a80"; font.pixelSize:12
        visible:!!card.playbackError || !card.scene
        text:card.scene ? "ERROR DE REPRODUCCIÓN\n"+card.playbackError : "ESCENA NO DISPONIBLE\nSelecciona otra en Configuración."
    }
    Column {
        visible:!!card.scene && card.scene.available===false
        anchors.centerIn:parent;width:Math.min(parent.width-24,260);spacing:10
        Text { width:parent.width;text:"CÁMARA PREPARADA";color:"#8aa5b2";font.pixelSize:12;horizontalAlignment:Text.AlignHCenter }
        Text { width:parent.width;text:"Elige el vídeo de esta escena\nen Ajustes → Animaciones.";color:"#718b98";font.pixelSize:11;horizontalAlignment:Text.AlignHCenter }
    }
    Rectangle { x:4; y:4; width:parent.width-8; height:21; color:"#121b21" }
    Text { x:12; y:7; text:(card.panel.name || card.panel.id)+" / "+(card.scene?card.scene.name:"SIN SEÑAL"); color:"#b1c1c7"; font.family:card.app.config.appearance.font; font.pixelSize:10; width:parent.width-62; elide:Text.ElideRight }
    Rectangle { width:5; height:5; x:parent.width-(card.selected?47:17); y:12; color:card.lost ? "#b65a4a" : card.scene && card.scene.available===false ? "#b68a57" : "#86b5ad" }
    Text { x:12; anchors.bottom:parent.bottom; anchors.bottomMargin:7; text:card.scene && card.scene.available===false ? "NO MEDIA / SELECT VIDEO" : card.lost ? "SIGNAL / OFFLINE" : card.selected ? "UPLINK / ACTIVE" : "LIVE FEED / ENCRYPTED"; color:"#6f8b98"; font.pixelSize:9; font.family:card.app.config.appearance.font }
    MouseArea { anchors.fill:parent; enabled:!card.preview; cursorShape:Qt.PointingHandCursor; onClicked:card.clicked() }
    ActionButton {
        objectName:"closeScene-"+card.panel.id
        visible:card.selected && !card.preview
        anchors.top:parent.top;anchors.right:parent.right
        anchors.topMargin:3;anchors.rightMargin:4
        width:26;height:22;implicitWidth:26;implicitHeight:22
        z:20;text:"×";Accessible.name:"Cerrar escena";accent:"#df998c"
        onClicked:card.app.close()
    }

    Rectangle {
        id: bubble
        visible:!card.preview && card.app.config.dialogue.enabled && card.app.dialogScene===card.panel.scene && !!card.app.dialogText && !card.lost
        width: Math.min(parent.width-28,360); height: Math.min(parent.height*.42,bubbleText.implicitHeight+24)
        anchors.left:parent.left; anchors.leftMargin:14; anchors.bottom:parent.bottom; anchors.bottomMargin:32
        color:"#18232b"; border.color:"#78939d"; clip:true
        opacity:visible ? 1 : 0
        Behavior on opacity { NumberAnimation { duration:180 } }
        Text { id:bubbleText; anchors.fill:parent; anchors.margins:12; text:card.app.dialogText; wrapMode:Text.Wrap; color:"#d7dfe0"; font.family:card.app.config.appearance.font; font.pixelSize:card.selected?13:11; elide:Text.ElideRight }
    }
    Canvas {
        id: noise
        anchors.fill:parent
        visible:card.signalDamage>0 && !card.lost && card.app.config.appearance.interference
        opacity:card.signalDamage*card.app.config.connection.intensity
        onPaint: {
            let ctx=getContext("2d");ctx.clearRect(0,0,width,height);
            for(let i=0;i<90;i++) {
                let y=Math.random()*height,h=1+Math.random()*8;
                ctx.fillStyle=Math.random()>.5 ? "#b6c5cb" : "#050a0f";
                ctx.fillRect(Math.random()*width*.2,y,width,h);
            }
            ctx.fillStyle="#9aafb7";ctx.fillRect(0,Math.random()*height,width,2);
        }
    }
    Rectangle {
        anchors.fill:parent; anchors.margins:3; visible:card.lost; color:"#0c1319"
        Column {
            anchors.centerIn:parent; spacing:12; width:Math.min(parent.width-24,260)
            Text { width:parent.width;text:card.app.config.labels.lost; color:"#c2967b"; font.family:card.app.config.appearance.font; font.pixelSize:Math.min(22,card.width/17);horizontalAlignment:Text.AlignHCenter }
            Text { width:parent.width;text:"CÁMARA SIN RESPUESTA\nLa red del sistema sigue activa.";color:"#7c929e";font.pixelSize:11;horizontalAlignment:Text.AlignHCenter }
            ActionButton { width:parent.width;text:"Reconectar cámara";onClicked:card.app.reconnectSerial++ }
        }
    }
    Timer { interval:200;running:card.selected;repeat:true;onTriggered:card.elapsed=(Date.now()-card.expandedAt)/1000 }
    Timer { interval:card.app.economy?150:65;running:noise.visible;repeat:true;onTriggered:noise.requestPaint() }
}
