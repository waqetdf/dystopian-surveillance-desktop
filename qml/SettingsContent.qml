import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

Pane {
    id: settings
    objectName:"settingsContent"
    required property var app
    padding:0
    background:Rectangle { color:"#111b22" }
    font.family: "DejaVu Sans Mono"
    font.pixelSize: 12
    palette { window:"#111b22"; windowText:"#c4d3da"; base:"#1c2c36"; alternateBase:"#21343f"; text:"#c4d3da"; button:"#293e4b"; buttonText:"#c4d3da"; highlight:"#547f90"; highlightedText:"#ffffff"; placeholderText:"#8299a6"; light:"#5a7380"; mid:"#3a5260"; dark:"#12232d" }
    visible:app.settingsVisible && app.ready
    property var draft: ({})
    property alias sectionIndex: tabs.currentIndex
    property int panelIndex:0
    property int appIndex:0
    property int revision:0
    property var panel: draft.panels ? draft.panels[Math.min(panelIndex,draft.panels.length-1)] : null
    property var selectedScene: panel ? app.scene(panel.scene) : null
    property var sceneDraft: ({})
    property string sceneDraftId: ""
    property string category:"Todas"
    property string localError:""
    property bool initialized:false
    property bool completed:false
    Component.onCompleted: { completed=true; resetDraft(); if(visible) Qt.callLater(present); }
    onVisibleChanged: { if(visible && completed) Qt.callLater(present); else if(completed) initialized=false; }
    function present() { if(!visible || !app.ready)return; if(!initialized)resetDraft();  }
    Connections { target:settings.app; function onSettingsRequested() { Qt.callLater(settings.present); } }
    function clone(v) { return JSON.parse(JSON.stringify(v)); }
    function resetDraft() { draft=clone(app.config); let id=app.settingsPanel||app.activePanel; let i=draft.panels.findIndex(p=>p.id===id); if(i>=0)panelIndex=i; initialized=true;localError="";loadScene(); }
    function refresh() { draft=clone(draft);revision++; }
    function loadScene() {
        if(!selectedScene) return;
        let s=selectedScene; sceneDraftId=s.id;
        sceneDraft=clone(Object.assign({name:s.name,personality:s.personality,dialogues:s.dialogues,events:s.events,apps:s.apps},draft.sceneOverrides[s.id] || {}));
        dialogueJson.text=JSON.stringify(sceneDraft.dialogues,null,2);
        eventJson.text=JSON.stringify(sceneDraft.events,null,2);
    }
    onPanelIndexChanged:loadScene()
    onSelectedSceneChanged:if(initialized && selectedScene && selectedScene.id!==sceneDraftId) loadScene()
    function selectPanel(i) {
        try { storeScene(); panelIndex=i; localError=""; } catch(e) { localError=e.message; }
    }
    function storeScene() {
        if(!selectedScene)return;
        sceneDraft.dialogues=JSON.parse(dialogueJson.text);sceneDraft.events=JSON.parse(eventJson.text);
        draft.sceneOverrides[selectedScene.id]=clone(sceneDraft);
    }
    function apply(nextAction) {
        try { storeScene();localError="";app.saving=true;app.send("save",{config:draft,next:nextAction||null}); }
        catch(e) { localError="JSON de conversaciones/eventos inválido: "+e.message; }
    }
    Connections { target:settings.app;function onImported(sceneId) { if(settings.panel){settings.panel.scene=sceneId;settings.refresh();} } }
    FileDialog {
        id:importDialog;title:"Importar animación (máx. 5 minutos, 2 GiB)"
        nameFilters:["Animaciones (*.mp4 *.webm *.mkv *.gif *.apng *.mov *.avi)"]
        onAccepted:{app.busyImport=true;app.send("import",{path:decodeURIComponent(selectedFile.toString().replace(/^file:\/\//,"")),name:importName.text,category:settings.category==="Todas"?"Ciudad":settings.category});}
    }
    FolderDialog { id:packDialog;title:"Selecciona la carpeta que contiene scene.json";onAccepted:{app.busyImport=true;app.send("pack",{path:decodeURIComponent(selectedFolder.toString().replace(/^file:\/\//,""))});} }
    ColumnLayout {
        anchors.fill:parent;anchors.margins:20;spacing:16
        RowLayout {
            Layout.fillWidth:true
            Column {
                Label { text:app.ready?app.config.labels.controlTitle:"";font.pixelSize:23;font.bold:true;color:"#d1dde1" }
                Label { text:(app.ready?app.config.labels.sector:"")+" · Los cambios se guardan con Aplicar";font.pixelSize:11;color:"#829da9" }
            }
            Item { Layout.fillWidth:true }
            ActionButton { text:"Descartar cambios";onClicked:settings.resetDraft() }
            ActionButton { objectName:"applySettings";text:"Aplicar";enabled:!app.saving;onClicked:settings.apply(null) }
            ActionButton { objectName:"closeSettings";text:"×";implicitWidth:30;implicitHeight:30;Accessible.name:"Cerrar ajustes";accent:"#df998c";onClicked:app.settingsVisible=false }
        }
        Label { visible:!!settings.localError || !!app.notice;text:settings.localError || app.notice;color:(settings.localError||app.noticeError)?"#e2a180":"#a7c5c6";wrapMode:Text.Wrap;Layout.fillWidth:true }
        RowLayout {
            Layout.fillWidth:true;Layout.fillHeight:true;spacing:20
            ColumnLayout {
                Layout.preferredWidth:165;Layout.alignment:Qt.AlignTop
                Repeater {
                    model:["01  Apariencia","02  Paneles","03  Animaciones","04  Personajes","05  Inteligencia artificial","06  Connection Lost","07  Aplicaciones","08  Rendimiento"]
                    ActionButton { required property string modelData;required property int index;text:modelData;Layout.fillWidth:true;implicitHeight:44;accent:tabs.currentIndex===index?"#cea77e":"#59727f";onClicked:tabs.currentIndex=index }
                }
                Item { Layout.fillHeight:true }
            }
            StackLayout {
                id:tabs;Layout.fillWidth:true;Layout.fillHeight:true;currentIndex:0
                // Appearance
                ScrollView {
                    contentWidth:availableWidth;clip:true
                    ColumnLayout {
                        width:parent.width;spacing:12
                        Label { text:"APARIENCIA Y AMBIENTE";font.pixelSize:18;color:"#c5d4db" }
                        Label { text:"NOMBRES DEL ESCRITORIO";color:"#c5d4db" }
                        Repeater {
                            model:[{k:"title",l:"Título principal"},{k:"subtitle",l:"Subtítulo"},{k:"settings",l:"Botón de ajustes"},{k:"controlTitle",l:"Título del centro de control"},{k:"sector",l:"Sector"},{k:"uplink",l:"Título del menú de escena"},{k:"talk",l:"Botón de conversación"},{k:"lost",l:"Mensaje de desconexión"}]
                            ConfigField { required property var modelData;target:settings.draft.labels;field:modelData.k;label:modelData.l }
                        }
                        Label { text:"Cámaras: Paneles · Escenas y personajes: Personajes · Accesos: Aplicaciones";wrapMode:Text.Wrap;Layout.fillWidth:true;color:"#829da9" }

                        Repeater {
                            model:[{k:"accent",l:"Color de borde (#RRGGBB)"},{k:"background",l:"Fondo (#RRGGBB)"},{k:"font",l:"Familia tipográfica"},
                                {k:"border",l:"Grosor del borde",t:"number",min:0,max:5},{k:"gap",l:"Separación",t:"number",min:0,max:24},
                                {k:"crt",l:"Líneas CRT",t:"bool"},{k:"interference",l:"Interferencias",t:"bool"},
                                {k:"transitionMs",l:"Transiciones (ms)",t:"number",min:0,max:1500},
                                {k:"ambient",l:"Ambiente según hora local",t:"bool"},{k:"ambientIntensity",l:"Intensidad ambiental",t:"number",min:0,max:.6,step:.01}]
                            ConfigField { required property var modelData;target:settings.draft.appearance;field:modelData.k;label:modelData.l;kind:modelData.t||"text";minimum:modelData.min||0;maximum:modelData.max||100;step:modelData.step||1 }
                        }
                        Label { text:"La luz cambia gradualmente con la hora del equipo. La capa ambiental conserva el contraste de las escenas.";wrapMode:Text.Wrap;Layout.fillWidth:true;color:"#7f99a5" }
                    }
                }
                // Layout editor
                ScrollView {
                    contentWidth:availableWidth;clip:true
                    ColumnLayout {
                        width:parent.width;spacing:12
                        Label { text:"MOSAICO DE CÁMARAS";font.pixelSize:18;color:"#c5d4db" }
                        ComboBox { id:panelPicker;Layout.fillWidth:true;model:settings.draft.panels?settings.draft.panels.map(p=>(p.name||p.id)+" · "+p.scene):[];currentIndex:settings.panelIndex;onActivated:settings.selectPanel(currentIndex) }
                        ConfigField { target:settings.panel;field:"name";label:"Nombre de cámara (vacío = identificador)" }
                        Rectangle {
                            id:layoutMap;Layout.fillWidth:true;Layout.preferredHeight:235;color:"#080f14";border.color:"#415c68"
                            Repeater {
                                model:settings.draft.panels||[]
                                Rectangle {
                                    id:tile;required property var modelData;required property int index
                                    x:modelData.x*layoutMap.width;y:modelData.y*layoutMap.height
                                    width:modelData.w*layoutMap.width-2;height:modelData.h*layoutMap.height-2
                                    color:index===settings.panelIndex?"#38515f":"#253741";border.color:"#7495a2"
                                    Text { anchors.centerIn:parent;text:tile.modelData.id;color:"#c2d2d8";font.pixelSize:10 }
                                    MouseArea {
                                        anchors.fill:parent;drag.target:tile;drag.minimumX:0;drag.minimumY:0
                                        drag.maximumX:layoutMap.width-tile.width;drag.maximumY:layoutMap.height-tile.height
                                        onPressed:settings.panelIndex=tile.index
                                        onReleased:{tile.modelData.x=Math.round(tile.x/layoutMap.width*120)/120;tile.modelData.y=Math.round(tile.y/layoutMap.height*120)/120;settings.refresh();}
                                    }
                                }
                            }
                        }
                        Label { text:"Arrastra para mover. Coordenadas y tamaños normalizados (0–1). Al guardar se comprueban límites y solapamientos.";color:"#819aa6";wrapMode:Text.Wrap;Layout.fillWidth:true }
                        Repeater {
                            model:[{k:"x",l:"Posición horizontal"},{k:"y",l:"Posición vertical"},{k:"w",l:"Anchura"},{k:"h",l:"Altura"}]
                            ConfigField { required property var modelData;target:settings.panel;field:modelData.k;label:modelData.l;kind:"number";minimum:modelData.k==="x"||modelData.k==="y"?0:.06;maximum:1;step:.01 }
                        }
                        RowLayout {
                            ActionButton { text:"Actualizar vista";onClicked:settings.refresh() }
                            ActionButton { text:"Dividir panel";enabled:!!settings.panel && settings.draft.panels.length<24;onClicked:{let p=settings.panel;let n=settings.clone(p);n.id="cam-"+Date.now();if(p.w>=p.h){p.w/=2;n.w=p.w;n.x=p.x+p.w;}else{p.h/=2;n.h=p.h;n.y=p.y+p.h;}settings.draft.panels.push(n);settings.refresh();} }
                            ActionButton { text:"Eliminar";enabled:!!settings.draft.panels && settings.draft.panels.length>1;onClicked:{settings.draft.panels.splice(settings.panelIndex,1);settings.panelIndex=0;settings.refresh();} }
                        }
                        RowLayout {
                            TextField { id:profileName;placeholderText:"Nombre del perfil";Layout.fillWidth:true;maximumLength:80 }
                            ActionButton { text:"Guardar perfil";enabled:profileName.text.trim().length>0;onClicked:{settings.draft.profiles[profileName.text.trim()]=settings.clone(settings.draft.panels);settings.refresh();} }
                        }
                        RowLayout {
                            ComboBox { id:profiles;model:Object.keys(settings.draft.profiles||{});Layout.fillWidth:true }
                            ActionButton { text:"Cargar";enabled:profiles.count>0;onClicked:{settings.draft.panels=settings.clone(settings.draft.profiles[profiles.currentText]);settings.panelIndex=0;settings.refresh();} }
                            ActionButton { text:"Predeterminado";onClicked:{settings.draft.panels=settings.clone(app.defaults.panels);settings.panelIndex=0;settings.refresh();} }
                        }
                    }
                }
                // Library
                ScrollView {
                    contentWidth:availableWidth;clip:true
                    ColumnLayout {
                        width:parent.width;spacing:12
                        Label { text:"BIBLIOTECA DE ANIMACIONES";font.pixelSize:18;color:"#c5d4db" }
                        ComboBox { Layout.fillWidth:true;model:settings.draft.panels?settings.draft.panels.map(p=>(p.name||p.id)+" · "+p.scene):[];currentIndex:settings.panelIndex;onActivated:settings.selectPanel(currentIndex) }
                        VideoPanel { Layout.fillWidth:true;Layout.preferredHeight:250;app:settings.app;panel:settings.panel||app.defaults.panels[0];preview:true;playingAllowed:settings.visible&&tabs.currentIndex===2;visible:!!settings.panel }
                        Label { text:settings.selectedScene ? ("Procedencia: "+(settings.selectedScene.source ? (settings.selectedScene.source.url || settings.selectedScene.source.filename || "Importación personal") : "Importación personal")) : ""; Layout.fillWidth:true;wrapMode:Text.Wrap;color:"#829ba8";font.pixelSize:10 }
                        ComboBox { model:["Todas","Ciudad","Interiores","Personajes","Industrial","Naturaleza distópica","Transporte","Tecnología","Escenas nocturnas"];onActivated:settings.category=currentText }
                        Flow {
                            Layout.fillWidth:true;spacing:8
                            Repeater {
                                model:app.scenes.filter(s=>settings.category==="Todas"||s.category===settings.category)
                                Rectangle {
                                    required property var modelData;width:164;height:122;color:"#1b2a33";border.color:settings.panel&&settings.panel.scene===modelData.id?"#d2ab83":"#405c6a"
                                    Image { x:4;y:4;width:156;height:88;source:parent.modelData.thumbnailUrl;fillMode:Image.PreserveAspectFit;smooth:false }
                                    Text { x:7;y:98;width:150;text:parent.modelData.name;color:"#b3c6d0";elide:Text.ElideRight;font.pixelSize:11 }
                                    MouseArea { anchors.fill:parent;onClicked:{settings.storeScene();settings.panel.scene=parent.modelData.id;settings.refresh();} }
                                }
                            }
                        }
                        RowLayout {
                            TextField { id:importName;placeholderText:"Nombre de la animación";Layout.fillWidth:true }
                            ActionButton { text:app.busyImport?"Importando…":"Importar vídeo / GIF";enabled:!app.busyImport;onClicked:importDialog.open() }
                            ActionButton { text:"Paquete";enabled:!app.busyImport;onClicked:packDialog.open() }
                        }
                        ActionButton { text:"Descargar selección sugerida (internet)";enabled:!app.busyImport;onClicked:{app.busyImport=true;app.send("fetchCurated");} }
                        Label { text:"La importación crea una copia H.264 local (máximo 5 minutos); el original se conserva. Los paquetes son carpetas con scene.json y medios.";wrapMode:Text.Wrap;Layout.fillWidth:true;color:"#819aa6" }
                        Repeater {
                            model:[{k:"scale",l:"Escala",min:1,max:4,step:.05},{k:"offsetX",l:"Desplazamiento X",min:-1,max:1,step:.05},{k:"offsetY",l:"Desplazamiento Y",min:-1,max:1,step:.05},
                                {k:"speed",l:"Velocidad",min:.25,max:3,step:.05},{k:"loop",l:"Repetición",t:"bool"},{k:"muted",l:"Silenciar",t:"bool"}]
                            ConfigField { required property var modelData;target:settings.panel;field:modelData.k;label:modelData.l;kind:modelData.t||"number";minimum:modelData.min===undefined?0:modelData.min;maximum:modelData.max||100;step:modelData.step||1 }
                        }
                        RowLayout {
                            Label { text:"Encuadre";color:"#acbfc9" }
                            ComboBox { model:["contain","cover"];currentIndex:settings.panel&&settings.panel.fit==="cover"?1:0;onActivated:settings.panel.fit=currentText }
                            ActionButton { text:"Previsualizar cambios";onClicked:settings.refresh() }
                            ActionButton { text:"Restaurar original";onClicked:{let p=app.defaults.panels.find(p=>p.id===settings.panel.id);settings.panel.scene=p?p.scene:app.defaults.panels[0].scene;settings.panel.scale=1;settings.panel.offsetX=0;settings.panel.offsetY=0;settings.panel.speed=1;settings.panel.loop=true;settings.panel.muted=true;settings.panel.fit="contain";settings.refresh();} }
                        }
                    }
                }
                // Characters
                ScrollView {
                    contentWidth:availableWidth;clip:true
                    ColumnLayout {
                        width:parent.width;spacing:12
                        Label { text:"PERSONAJES / DIÁLOGOS / EVENTOS";font.pixelSize:18;color:"#c5d4db" }
                        ComboBox { Layout.fillWidth:true;model:settings.draft.panels?settings.draft.panels.map(p=>(p.name||p.id)+" · "+p.scene):[];currentIndex:settings.panelIndex;onActivated:settings.selectPanel(currentIndex) }
                        ConfigField { target:settings.draft.dialogue;field:"enabled";label:"Mostrar globos";kind:"bool" }
                        ConfigField { target:settings.draft.dialogue;field:"duration";label:"Segundos por intervención";kind:"number";minimum:2;maximum:60 }
                        ConfigField { target:settings.draft.dialogue;field:"frequency";label:"Frecuencia (0 = sin eventos)";kind:"number";minimum:0;maximum:5;step:.1 }
                        ConfigField { target:settings.sceneDraft;field:"name";label:"Nombre de escena" }
                        Label { text:"Personalidad persistente";color:"#b9cbd4" }
                        TextArea { Layout.fillWidth:true;Layout.preferredHeight:90;text:settings.sceneDraft.personality||"";wrapMode:TextEdit.Wrap;onTextChanged:if(activeFocus)settings.sceneDraft.personality=text }
                        Label { text:"Conversaciones locales (JSON: greeting y talk, listas de intervenciones)";color:"#b9cbd4";wrapMode:Text.Wrap;Layout.fillWidth:true }
                        TextArea { id:dialogueJson;Layout.fillWidth:true;Layout.preferredHeight:170;font.family:"DejaVu Sans Mono";wrapMode:TextEdit.Wrap;selectByMouse:true }
                        Label { text:"Eventos JSON · trigger: open, timer, random, hour, memory, app\nprobability: 0–1 · cooldown: segundos · lines: intervenciones";color:"#b9cbd4";wrapMode:Text.Wrap;Layout.fillWidth:true }
                        TextArea { id:eventJson;Layout.fillWidth:true;Layout.preferredHeight:280;font.family:"DejaVu Sans Mono";wrapMode:TextEdit.Wrap;selectByMouse:true }
                        ActionButton { text:"Guardar edición en borrador";onClicked:{try{settings.storeScene();settings.localError="";}catch(e){settings.localError=e.message;}} }
                    }
                }
                // AI
                ScrollView {
                    contentWidth:availableWidth;clip:true
                    ColumnLayout {
                        width:parent.width;spacing:12
                        Label { text:"IA OPCIONAL / CONSENTIMIENTO";font.pixelSize:18;color:"#c5d4db" }
                        Label { text:"Al activar y guardar, los mensajes que envíes, la personalidad y el historial limitado se transmitirán a la URL indicada. Ningún diálogo local provoca peticiones automáticas. Puede haber costes del proveedor.";color:"#bdad96";wrapMode:Text.Wrap;Layout.fillWidth:true }
                        ConfigField { target:settings.draft.ai;field:"enabled";label:"Permitir consultas a IA";kind:"bool" }
                        ConfigField { target:settings.draft.ai;field:"url";label:"URL completa de chat" }
                        ConfigField { target:settings.draft.ai;field:"model";label:"Modelo" }
                        ConfigField { target:settings.draft.ai;field:"maxTokens";label:"Máximo de tokens";kind:"number";minimum:16;maximum:2048 }
                        ConfigField { target:settings.draft.ai;field:"historyLimit";label:"Mensajes locales por personaje";kind:"number";minimum:0;maximum:100 }
                        ConfigField { target:settings.draft.ai;field:"context";label:"Contexto adicional" }
                        TextField { id:apiKey;Layout.fillWidth:true;placeholderText:"API key · se guarda solo en el llavero del sistema";echoMode:TextInput.Password;maximumLength:4096 }
                        RowLayout {
                            ActionButton { text:"Guardar clave";onClicked:{settings.apply({op:"key",key:apiKey.text});apiKey.clear();} }
                            ActionButton { text:"Borrar clave";onClicked:{settings.apply({op:"key",key:""});} }
                            ActionButton { text:"Comprobar conexión";onClicked:{settings.apply({op:"testAI"});} }
                        }
                        ActionButton { text:"Borrar historial local de IA";onClicked:app.send("clearHistory") }
                        Label { text:"Adaptador de API JSON (formato de mensajes compatible con Chat Completions)";wrapMode:Text.Wrap;Layout.fillWidth:true;color:"#b9cbd4" }
                        Repeater {
                            model:[{k:"modelField",l:"Campo de modelo"},{k:"messagesField",l:"Campo de mensajes"},{k:"limitField",l:"Campo del límite"},{k:"responsePath",l:"Ruta a texto de respuesta"}]
                            ConfigField { required property var modelData;target:settings.draft.ai?settings.draft.ai.adapter:null;field:modelData.k;label:modelData.l }
                        }
                        Label { text:"Necesita un servicio Secret Service desbloqueado (GNOME Keyring o compatible). No hay alternativa de almacenamiento en texto plano.";color:"#809aa7";Layout.fillWidth:true;wrapMode:Text.Wrap }
                    }
                }
                // Connection
                ScrollView {
                    contentWidth:availableWidth;clip:true
                    ColumnLayout {
                        width:parent.width;spacing:12
                        Label { text:"CONNECTION LOST";font.pixelSize:18;color:"#c5d4db" }
                        ConfigField { target:settings.draft.connection;field:"enabled";label:"Pérdida ficticia de señal";kind:"bool" }
                        RowLayout {
                            Label { text:"Preajustes";color:"#b9cbd4" }
                            ComboBox { model:["30 segundos","1 minuto","2 minutos","5 minutos","10 minutos"];onActivated:{settings.draft.connection.seconds=[30,60,120,300,600][currentIndex];settings.refresh();} }
                        }
                        ConfigField { target:settings.draft.connection;field:"seconds";label:"Espera personalizada (s)";kind:"number";minimum:5;maximum:86400 }
                        ConfigField { target:settings.draft.connection;field:"interferenceSeconds";label:"Duración de interferencia (s)";kind:"number";minimum:1;maximum:60 }
                        ConfigField { target:settings.draft.connection;field:"intensity";label:"Intensidad de estática";kind:"number";minimum:0;maximum:1;step:.05 }
                        ActionButton { text:"Reconectar escena activa";enabled:!!app.activePanel;onClicked:app.reconnectSerial++ }
                        Label { text:"Este efecto solo afecta al vídeo de la cámara. No cambia la conexión de red ni cierra aplicaciones.";wrapMode:Text.Wrap;Layout.fillWidth:true;color:"#819aa6" }
                    }
                }
                // Applications
                ScrollView {
                    contentWidth:availableWidth;clip:true
                    ColumnLayout {
                        width:parent.width;spacing:12
                        Label { text:"ACCESOS DIRECTOS";font.pixelSize:18;color:"#c5d4db" }
                        Repeater {
                            model:settings.draft.apps||[]
                            Rectangle {
                                required property var modelData;required property int index
                                Layout.fillWidth:true;implicitHeight:160;color:"#1b2932";border.color:"#354e5d"
                                ColumnLayout {
                                    anchors.fill:parent;anchors.margins:10;spacing:6
                                    RowLayout {
                                        TextField { text:modelData.name;onTextEdited:modelData.name=text;Layout.fillWidth:true }
                                        TextField { text:modelData.icon;onTextEdited:modelData.icon=text;Layout.preferredWidth:56 }
                                        ActionButton { text:"↑";implicitWidth:32;enabled:index>0;onClicked:{let a=settings.draft.apps;[a[index-1],a[index]]=[a[index],a[index-1]];settings.refresh();} }
                                        ActionButton { text:"↓";implicitWidth:32;enabled:index<settings.draft.apps.length-1;onClicked:{let a=settings.draft.apps;[a[index+1],a[index]]=[a[index],a[index+1]];settings.refresh();} }
                                        ActionButton { text:"Eliminar";onClicked:{let id=modelData.id;settings.storeScene();for(let s of app.scenes){let o=settings.draft.sceneOverrides[s.id]||{};o.apps=(o.apps||s.apps).filter(x=>x!==id);settings.draft.sceneOverrides[s.id]=o;}settings.draft.apps.splice(index,1);settings.refresh();settings.loadScene();} }
                                    }
                                    TextField { Layout.fillWidth:true;text:JSON.stringify(modelData.argv);enabled:modelData.internal!=="settings";onEditingFinished:{try{let v=JSON.parse(text);if(!Array.isArray(v))throw Error("Usa una lista JSON");modelData.argv=v;settings.localError="";}catch(e){settings.localError=e.message;}} }
                                    CheckBox { text:"Asociar a "+(settings.selectedScene?settings.selectedScene.name:"");checked:settings.sceneDraft.apps?settings.sceneDraft.apps.indexOf(modelData.id)>=0:false;onToggled:{let a=settings.sceneDraft.apps||[];if(checked && a.indexOf(modelData.id)<0)a.push(modelData.id);if(!checked)a=a.filter(x=>x!==modelData.id);settings.sceneDraft.apps=a;} }
                                }
                            }
                        }
                        ActionButton { text:"Añadir acceso";onClicked:{settings.draft.apps.push({id:"app-"+Date.now(),name:"Nueva aplicación",icon:">_",argv:["foot"]});settings.refresh();} }
                        Label { text:'Comandos como lista JSON: ["foot", "-e", "htop"]. Para scripts usa una ruta absoluta al ejecutable. No se interpretan operadores de shell. El orden de los accesos asociados se conserva en la escena.';color:"#819aa6";wrapMode:Text.Wrap;Layout.fillWidth:true }
                        ActionButton { text:"Usar orden de esta lista en la escena";onClicked:{let ids=settings.sceneDraft.apps;settings.sceneDraft.apps=settings.draft.apps.filter(a=>ids.indexOf(a.id)>=0).map(a=>a.id);} }
                    }
                }
                // Performance
                ScrollView {
                    contentWidth:availableWidth;clip:true
                    ColumnLayout {
                        width:parent.width;spacing:12
                        Label { text:"RENDIMIENTO";font.pixelSize:18;color:"#c5d4db" }
                        Repeater {
                            model:[{k:"fps",l:"FPS máximos de vídeo",min:10,max:60},{k:"pauseHidden",l:"Pausar escenas ocultas",t:"bool"},
                                {k:"hardwareDecode",l:"Decodificación hardware",t:"bool"},{k:"quality",l:"Altura máxima al importar",min:216,max:2160},
                                {k:"powerSave",l:"Modo ahorro",t:"bool"},{k:"autoPowerSave",l:"Ahorro automático",t:"bool"},{k:"cpuThreshold",l:"Umbral de CPU (%)",min:10,max:100}]
                            ConfigField { required property var modelData;target:settings.draft.performance;field:modelData.k;label:modelData.l;kind:modelData.t||"number";minimum:modelData.min||0;maximum:modelData.max||100 }
                        }
                        Label { text:"CPU: "+(app.stats.cpu===null?"muestreando":app.stats.cpu+"%")+"\nRAM del sistema: "+app.stats.ramUsedMiB+" / "+app.stats.ramTotalMiB+" MiB\nServicio Python: "+app.stats.rssMiB+" MiB\nGPU: "+(app.stats.gpu===null?"N/D (el controlador no expone gpu_busy_percent)":app.stats.gpu+"%");color:"#b1c7d1";lineHeight:1.6 }
                        Label { text:"En ahorro se pausan las cámaras secundarias y se reduce el ruido. El modo automático responde a CPU alta, batería baja y ventanas a pantalla completa. La pausa por ventanas ocultas detecta pantalla completa y escenas cubiertas por el menú; no calcula oclusión parcial.\n\nLa selección del decodificador requiere reiniciar el escritorio. El límite FPS se aplica también a vídeos existentes mediante copias locales en caché; los originales se conservan. Prepararlas puede tardar. La calidad se aplica a nuevas importaciones. La interfaz se sincroniza con el compositor. La aceleración depende del códec, Qt y los controladores instalados.";wrapMode:Text.Wrap;Layout.fillWidth:true;color:"#819aa6" }
                    }
                }
            }
        }
    }
}
