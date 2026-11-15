import QtQuick
import QtQuick.Controls
ApplicationWindow {
    id:window
    required property var app
    objectName:"settingsWindow"
    width:1120;height:820;minimumWidth:800;minimumHeight:600
    title:app.ready?app.config.labels.title+" · "+app.config.labels.settings:"Ajustes"
    visible:app.ready && app.settingsVisible
    onClosing:app.settingsVisible=false
    SettingsContent { anchors.fill:parent;app:window.app }
}
