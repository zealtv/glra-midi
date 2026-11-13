// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

// The right-hand panel: edits the selected control on the shown tab (docs/config-app.md 4.5).
// It holds no profile logic: every field calls a controller slot and shows what the controller
// returns, including the profile's own message for an invalid entry.
Rectangle {
    id: panel
    property var ctl
    property var pal
    readonly property var info: ctl.inspector
    readonly property var edit: info.edit
    readonly property var fields: edit.fields !== undefined ? edit.fields : ({})
    readonly property bool turn: edit.turn === true
    readonly property bool eventMode: edit.mode === "event"
    readonly property bool onGlobalTab: ctl.tab === 0
    color: pal.panel
    radius: 14
    border.color: pal.line

    function entry(key) { return fields[key] }
    function has(key) { return fields[key] !== undefined }
    function choices(values) {
        return values.map(function(v) { return { value: v[0], label: v[1] } })
    }
    readonly property var channelChoices: edit.channelChoices || []
    readonly property var layerChoices: edit.layerChoices || []
    readonly property var curveChoices: choices([
        ["linear", "Linear"], ["ease-in", "Ease in"], ["ease-out", "Ease out"], ["ease-in-out", "Ease in-out"]])

    Flickable {
        id: scroller
        anchors.fill: parent
        anchors.margins: 18
        clip: true
        contentWidth: width
        contentHeight: column.implicitHeight
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

        ColumnLayout {
            id: column
            width: scroller.width - 10
            spacing: 6

            Text {
                text: "INSPECTOR"
                font.pixelSize: 10
                font.weight: Font.DemiBold
                font.letterSpacing: 0.8
                color: panel.pal.muted
            }

            // Nothing selected.
            Text {
                visible: !panel.info.selected
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                text: panel.info.hint
                font.pixelSize: 14
                color: panel.pal.ink
            }
            Text {
                visible: !panel.info.selected
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                text: panel.info.count
                font.pixelSize: 12
                color: panel.pal.muted
            }

            // The selected control.
            Text {
                visible: panel.info.selected
                objectName: "inspectorTitle"
                text: panel.info.title
                font.pixelSize: 18
                font.weight: Font.Bold
                color: panel.pal.ink
            }
            Text {
                visible: panel.info.selected
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                text: panel.info.subtitle
                font.pixelSize: 12
                color: panel.pal.muted
            }

            // A per-layer control seen from the Global tab: nothing to edit here.
            ColumnLayout {
                objectName: "eachBox"
                visible: panel.info.selected && panel.edit.mode === "each"
                Layout.fillWidth: true
                spacing: 8
                Text {
                    text: "Different on each layer"
                    font.pixelSize: 14
                    font.weight: Font.DemiBold
                    color: panel.pal.ink
                }
                Text {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    text: panel.edit.layersUsedText || ""
                    font.pixelSize: 12
                    color: panel.pal.muted
                }
                AppButton {
                    objectName: "makeGlobal"
                    text: "Make global…"
                    pal: panel.pal
                    onClicked: panel.ctl.setApplies("global")
                }
            }

            ColumnLayout {
                id: editor
                visible: panel.info.selected && panel.edit.mode !== "each"
                Layout.fillWidth: true
                spacing: 8

                Segmented {
                    pal: panel.pal
                    label: "Action"
                    fieldName: "action"
                    choices: (panel.edit.actions || [])
                    value: panel.edit.action || "none"
                    onPicked: function(v) {
                        if (panel.turn && v !== "none") panel.ctl.setKind(v)
                        else panel.ctl.setAction(v)
                    }
                }
                Segmented {
                    objectName: "appliesRow"
                    visible: panel.eventMode && !panel.onGlobalTab
                    pal: panel.pal
                    label: "Applies"
                    fieldName: "applies"
                    choices: panel.choices([["layer", "This layer"], ["global", "All layers"]])
                    value: panel.edit.applies || "layer"
                    onPicked: function(v) { panel.ctl.setApplies(v) }
                }
                Text {
                    visible: panel.eventMode && panel.onGlobalTab
                    text: "Applies to all layers (global)."
                    font.pixelSize: 12
                    color: panel.pal.muted
                }

                // An event's fields.
                ColumnLayout {
                    objectName: "eventFields"
                    visible: panel.eventMode
                    Layout.fillWidth: true
                    spacing: 6

                    AppChoice {
                        visible: !panel.turn
                        pal: panel.pal
                        label: "Kind"
                        fieldName: "kind"
                        choices: panel.edit.kinds || []
                        value: panel.edit.kind || ""
                        onPicked: function(v) { panel.ctl.setKind(v) }
                    }
                    AppField {
                        visible: panel.has("note")
                        pal: panel.pal
                        label: "Note"
                        fieldName: "note"
                        entry: panel.entry("note")
                        note: panel.edit.noteName || ""
                        onEdited: function(t) { panel.ctl.setField("note", t) }
                    }
                    AppField {
                        visible: panel.has("cc")
                        pal: panel.pal
                        label: "CC"
                        fieldName: "cc"
                        entry: panel.entry("cc")
                        onEdited: function(t) { panel.ctl.setField("cc", t) }
                    }
                    AppField {
                        visible: panel.has("velocity")
                        pal: panel.pal
                        label: "Velocity"
                        fieldName: "velocity"
                        entry: panel.entry("velocity")
                        onEdited: function(t) { panel.ctl.setField("velocity", t) }
                    }
                    AppField {
                        visible: panel.has("low")
                        pal: panel.pal
                        label: "Low"
                        fieldName: "low"
                        entry: panel.entry("low")
                        onEdited: function(t) { panel.ctl.setField("low", t) }
                    }
                    AppField {
                        visible: panel.has("high")
                        pal: panel.pal
                        label: "High"
                        fieldName: "high"
                        entry: panel.entry("high")
                        onEdited: function(t) { panel.ctl.setField("high", t) }
                    }
                    AppField {
                        visible: panel.has("value")
                        pal: panel.pal
                        label: "Value"
                        fieldName: "value"
                        entry: panel.entry("value")
                        onEdited: function(t) { panel.ctl.setField("value", t) }
                    }
                    Segmented {
                        visible: panel.has("direction")
                        pal: panel.pal
                        label: "Direction"
                        fieldName: "direction"
                        choices: panel.choices([["inc", "Inc"], ["dec", "Dec"]])
                        value: panel.has("direction") ? panel.entry("direction").text : "inc"
                        onPicked: function(v) { panel.ctl.setField("direction", v) }
                    }
                    AppField {
                        visible: panel.has("size")
                        pal: panel.pal
                        label: "Step size"
                        fieldName: "size"
                        entry: panel.entry("size")
                        onEdited: function(t) { panel.ctl.setField("size", t) }
                    }
                    AppField {
                        visible: panel.has("step")
                        pal: panel.pal
                        label: "Step"
                        fieldName: "step"
                        entry: panel.entry("step")
                        onEdited: function(t) { panel.ctl.setField("step", t) }
                    }
                    AppField {
                        visible: panel.has("initial")
                        pal: panel.pal
                        label: "Initial"
                        fieldName: "initial"
                        entry: panel.entry("initial")
                        onEdited: function(t) { panel.ctl.setField("initial", t) }
                    }
                    AppField {
                        visible: panel.has("rise-ms")
                        pal: panel.pal
                        label: "Rise ms"
                        fieldName: "rise-ms"
                        entry: panel.entry("rise-ms")
                        onEdited: function(t) { panel.ctl.setField("rise-ms", t) }
                    }
                    AppField {
                        visible: panel.has("fall-ms")
                        pal: panel.pal
                        label: "Fall ms"
                        fieldName: "fall-ms"
                        entry: panel.entry("fall-ms")
                        onEdited: function(t) { panel.ctl.setField("fall-ms", t) }
                    }
                    AppField {
                        visible: panel.has("ease-ms")
                        pal: panel.pal
                        label: "Ease ms"
                        fieldName: "ease-ms"
                        entry: panel.entry("ease-ms")
                        onEdited: function(t) { panel.ctl.setField("ease-ms", t) }
                    }
                    AppChoice {
                        visible: panel.has("curve")
                        pal: panel.pal
                        label: "Curve"
                        fieldName: "curve"
                        choices: panel.curveChoices
                        value: panel.has("curve") ? panel.entry("curve").text : "linear"
                        onPicked: function(v) { panel.ctl.setField("curve", v) }
                    }
                    AppChoice {
                        visible: panel.has("encoding")
                        pal: panel.pal
                        label: "Encoding"
                        fieldName: "encoding"
                        choices: panel.choices([["twos-complement", "Two's complement"],
                            ["binary-offset", "Binary offset"], ["signed-bit", "Signed bit"]])
                        value: panel.has("encoding") ? panel.entry("encoding").text : "twos-complement"
                        onPicked: function(v) { panel.ctl.setField("encoding", v) }
                    }
                    RowLayout {
                        visible: panel.has("mode")
                        Layout.fillWidth: true
                        spacing: 8
                        Text {
                            Layout.preferredWidth: 84
                            text: "Latch"
                            font.pixelSize: 12
                            color: panel.pal.muted
                        }
                        Switch {
                            objectName: "field-mode"
                            checked: panel.has("mode") && panel.entry("mode").text === "latch"
                            onToggled: panel.ctl.setField("mode", checked ? "latch" : "momentary")
                        }
                    }
                    AppChoice {
                        visible: panel.has("channel")
                        pal: panel.pal
                        label: "Channel"
                        fieldName: "channel"
                        choices: panel.channelChoices
                        value: panel.has("channel") ? panel.entry("channel").text : "default"
                        onPicked: function(v) { panel.ctl.setField("channel", v) }
                    }
                }

                // A layer key.
                ColumnLayout {
                    objectName: "layerKeyFields"
                    visible: panel.edit.mode === "layer-key"
                    Layout.fillWidth: true
                    spacing: 6
                    Segmented {
                        pal: panel.pal
                        label: "Layer"
                        fieldName: "layerkey"
                        choices: panel.choices([["layer-set", "Set"], ["layer-inc", "Next"], ["layer-dec", "Previous"]])
                        value: panel.edit.layerKey ? panel.edit.layerKey.kind : "layer-inc"
                        onPicked: function(v) {
                            panel.ctl.setLayerKey(v, panel.edit.layerKey ? panel.edit.layerKey.layer : 1)
                        }
                    }
                    AppChoice {
                        visible: panel.edit.layerKey !== undefined && panel.edit.layerKey.kind === "layer-set"
                        pal: panel.pal
                        label: "Go to"
                        fieldName: "layer"
                        choices: panel.layerChoices
                        value: panel.edit.layerKey ? String(panel.edit.layerKey.layer) : "1"
                        onPicked: function(v) { panel.ctl.setLayerKey("layer-set", parseInt(v)) }
                    }
                    Text {
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        text: "Layer keys work the same on every layer, so they can't hold events."
                        font.pixelSize: 12
                        color: panel.pal.muted
                    }
                }

                // The other layers of a per-layer control.
                ColumnLayout {
                    objectName: "alsoOn"
                    visible: panel.edit.alsoOn !== undefined && panel.edit.alsoOn.length > 0
                    Layout.fillWidth: true
                    Layout.topMargin: 6
                    spacing: 2
                    Text {
                        text: "Also on"
                        font.pixelSize: 11
                        font.weight: Font.DemiBold
                        color: panel.pal.muted
                    }
                    Repeater {
                        model: panel.edit.alsoOn || []
                        Text {
                            required property var modelData
                            objectName: "alsoOn" + modelData.layer
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                            text: modelData.text
                            font.pixelSize: 12
                            color: panel.pal.accent
                            TapHandler { onTapped: panel.ctl.selectTab(modelData.layer) }
                        }
                    }
                }
            }
        }
    }
}
