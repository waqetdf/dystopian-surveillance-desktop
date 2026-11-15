import QtQuick
Window {
    id:preview
    width:1440;height:900;visible:true;title:"Dystopian Surveillance · vista de desarrollo"
    AppState { id:desktopState;objectName:"appState";onRequest:message=>bridge.send(JSON.stringify(message)) }
    Connections { target:bridge;function onMessage(message){desktopState.receive(JSON.parse(message));} }
    Dashboard { anchors.fill:parent;app:desktopState }
    Loader { active:desktopState.ready && desktopState.settingsVisible; sourceComponent:Settings { app:desktopState } }
    Component.onCompleted:bridge.start()
}
