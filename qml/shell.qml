import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland

ShellRoot {
    id: root
    Component.onCompleted: Quickshell.watchFiles = false
    AppState { id:desktopState;settingsVisible:Quickshell.env("DSD_SETTINGS")==="1";onRequest:message=>service.write(JSON.stringify(message)+"\n") }
    Process {
        id:service
        command:["python3",Quickshell.env("DSD_ROOT") ? Quickshell.env("DSD_ROOT")+"/backend/service.py" : Quickshell.shellDir+"/../backend/service.py"]
        running:true;stdinEnabled:true
        stdout:SplitParser { onRead:data=>{try{desktopState.receive(JSON.parse(data));}catch(e){console.error("Invalid service message:",e.message);}} }
        stderr:SplitParser { onRead:data=>console.error("Service:",data) }
        onExited:(exitCode,exitStatus)=>desktopState.flash("El servicio local se ha detenido. Reinicia con dsd restart.",true)
    }
    Variants {
        model:Quickshell.screens
        PanelWindow {
            required property var modelData
            screen:modelData
            anchors { top:true;bottom:true;left:true;right:true }
            exclusionMode:ExclusionMode.Ignore
            WlrLayershell.namespace:"dystopian-surveillance"
            WlrLayershell.layer:WlrLayer.Bottom
            WlrLayershell.keyboardFocus:desktopState.activePanel?WlrKeyboardFocus.OnDemand:WlrKeyboardFocus.None
            color:"#10171c"
            Dashboard { anchors.fill:parent;app:desktopState;screenName:modelData.name;obscured:root.fullscreen }
        }
    }
    property bool fullscreen:ToplevelManager.toplevels.values.some(t=>t.activated&&t.fullscreen)
    onFullscreenChanged:desktopState.fullscreen=fullscreen
    Loader { active:desktopState.ready; sourceComponent:Settings { app:desktopState } }
    IpcHandler {
        target:"control"
        function open(panelId:string):void { let p=desktopState.ready?desktopState.config.panels.find(p=>p.id===panelId):null; if(p && Quickshell.screens.length) desktopState.select(p,Quickshell.screens[0].name); }
        function status():string { return JSON.stringify({ready:desktopState.ready,panels:desktopState.ready?desktopState.config.panels.length:0,activePanel:desktopState.activePanel,settings:desktopState.settingsVisible,economy:desktopState.economy}); }
        function settings():void { desktopState.openSettings(); }
        function close():void { desktopState.close(); }
        function quit():void { Qt.quit(); }
    }
}
