import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

RowLayout {
    id: row
    required property var target
    required property string field
    required property string label
    property string kind: "text"
    property real minimum: 0
    property real maximum: 100
    property real step: 1
    Layout.fillWidth:true
    Label { text:row.label;color:"#b7c7ce";Layout.preferredWidth:220;wrapMode:Text.Wrap }
    CheckBox { visible:row.kind==="bool";checked:row.target?!!row.target[row.field]:false;onToggled:row.target[row.field]=checked }
    SpinBox {
        visible:row.kind==="number";editable:true
        property int factor:row.step<1?1000:1
        from:Math.round(row.minimum*factor);to:Math.round(row.maximum*factor);stepSize:Math.max(1,Math.round(row.step*factor))
        value:row.kind==="number" && row.target?Math.round(row.target[row.field]*factor):0
        textFromValue:function(v,locale){return Number(v/factor).toLocaleString(locale,'f',factor===1?0:3)}
        valueFromText:function(text,locale){return Math.round(Number.fromLocaleString(locale,text)*factor)}
        onValueModified:row.target[row.field]=value/factor
        Layout.preferredWidth:180
    }
    TextField {
        visible:row.kind==="text";text:row.target?String(row.target[row.field]||""):""
        onTextEdited:row.target[row.field]=text;Layout.fillWidth:true
        selectByMouse:true
    }
    Item { Layout.fillWidth:row.kind!=="text" }
}
