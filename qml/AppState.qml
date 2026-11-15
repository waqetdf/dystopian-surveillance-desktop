import QtQuick

QtObject {
    id: app
    property var config: ({})
    property var defaults: ({})
    property var scenes: []
    property var stats: ({})
    property bool ready: false
    property string activePanel: ""
    property string activeScreen: ""
    property string activeScene: ""
    property bool settingsVisible: false
    property string settingsPanel: ""
    property string notice: ""
    property bool noticeError: false
    property var dialogLines: []
    property string dialogScene: ""
    property int dialogIndex: 0
    property string dialogText: dialogLines.length > dialogIndex ? dialogLines[dialogIndex] : ""
    property bool fullscreen: false
    property bool busyImport: false
    property int reconnectSerial: 0
    property bool saving: false
    property var pendingSelection: null
    property bool economy: ready && (config.performance.powerSave || (config.performance.autoPowerSave &&
        (fullscreen || stats.batteryLow || (stats.cpu !== null && stats.cpu > config.performance.cpuThreshold))))
    signal settingsRequested()
    function openSettings() { settingsPanel=activePanel; settingsVisible=true; settingsRequested(); }
    signal request(var message)
    signal saved()
    signal imported(string sceneId)
    function send(op, args) { let m = args || {}; m.op = op; request(m); }
    function scene(id) { for (let s of scenes) if (s.id === id) return s; return null; }
    function receive(m) {
        if (m.type === "state") {
            config = m.config; defaults = m.defaults; scenes = m.scenes; ready = true;
            if (activePanel && !config.panels.some(p => p.id === activePanel && p.scene === activeScene)) close();
            if (saving) { saving = false; saved(); flash("Configuración guardada.", false); }
            if (m.warnings.length) flash(m.warnings.join("\n"), true);
        } else if (m.type === "stats") stats = m;
        else if (m.type === "event" && config.dialogue.enabled) {
            dialogScene = m.scene; dialogLines = m.lines; dialogIndex = 0; dialogueTimer.restart();
        } else if (m.type === "error") { saving = false; busyImport = false; flash(m.text, true); }
        else if (m.type === "notice") flash(m.text, false);
        else if (m.type === "settings") openSettings();
        else if (m.type === "catalogReady") { busyImport=false; flash("Selección opcional disponible en la biblioteca.",false); }
        else if (m.type === "imported") { busyImport = false; imported(m.scene); flash("Animación importada.", false); }
    }
    function flash(text, error) { notice = text; noticeError = error; noticeTimer.restart(); }
    function select(panel, screen) {
        if (activePanel === panel.id && activeScreen === screen) { close(); return; }
        if (activePanel) {
            pendingSelection = {panel:panel,screen:screen}; activePanel = ""; activeScene = "";
            send("close"); switchTimer.restart();
        } else activate(panel,screen);
    }
    function activate(panel, screen) {
        activePanel = panel.id; activeScreen = screen; activeScene = panel.scene;
        dialogLines = []; reconnectSerial++; send("open", {scene:panel.scene});
    }
    function close() { pendingSelection=null; switchTimer.stop(); activePanel=""; activeScene=""; dialogLines=[]; send("close"); }
    property Timer switchTimer: Timer {
        interval: app.ready ? app.config.appearance.transitionMs : 260
        onTriggered: { let p=app.pendingSelection; app.pendingSelection=null; if(p) app.activate(p.panel,p.screen); }
    }
    property Timer dialogueTimer: Timer {
        interval: app.ready ? app.config.dialogue.duration*1000 : 7000
        onTriggered: {
            if (app.dialogIndex+1 < app.dialogLines.length) { app.dialogIndex++; restart(); }
            else app.dialogLines = [];
        }
    }
    property Timer noticeTimer: Timer { interval: 12000; onTriggered: app.notice="" }
}
