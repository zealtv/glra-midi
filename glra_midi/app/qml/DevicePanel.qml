// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

// The device panel (docs/config-app.md 4.10): orientation, MIDI port and channel, and the pad's
// factory RGB mode. Every field edits the profile. Only [Apply to pad] touches the pad, and each
// Apply is saved in the pad's memory; it holds no logic of its own, the controller says what is
// enabled and what to show.
Rectangle {
    id: panel
    property var ctl
    property var pal
    readonly property var dev: ctl.device
    readonly property var light: dev.lighting
    readonly property var applyState: dev.apply
    implicitHeight: content.implicitHeight + 20
    color: pal.panel
    radius: 14
    border.color: pal.line

    function levelChoices() {
        return light.levels.map(function(n) { return { value: String(n), label: String(n) } })
    }
    function modeChoices() {
        return light.modes.map(function(m) { return { value: String(m.value), label: m.label } })
    }
    function channels() {
        var list = []
        for (var n = 1; n <= 16; n++) list.push({ value: String(n), label: String(n) })
        return list
    }
    function lastColor() {
        return applyState.lastKind === "err" ? pal.errLine : applyState.lastKind === "warn" ? pal.warnLine : applyState.lastKind === "ok" ? pal.accent : pal.muted
    }

    RowLayout {
        id: content
        anchors.fill: parent
        anchors.margins: 10
        spacing: 24

        // Orientation, MIDI.
        ColumnLayout {
            Layout.minimumWidth: 330
            Layout.preferredWidth: 330
            Layout.maximumWidth: 330
            Layout.alignment: Qt.AlignTop
            spacing: 6
            Text {
                text: "PAD AND MIDI"
                font.pixelSize: 10
                font.weight: Font.DemiBold
                font.letterSpacing: 0.8
                color: panel.pal.muted
            }
            Segmented {
                objectName: "orientationRow"
                pal: panel.pal
                label: "Dials on"
                fieldName: "orientation"
                choices: panel.dev.orientations
                value: panel.dev.orientation
                onPicked: function(v) { panel.ctl.setOrientation(v) }
            }
            AppField {
                pal: panel.pal
                label: "MIDI port"
                fieldName: "port"
                entry: ({ text: panel.dev.port.text, error: panel.dev.port.error, range: "" })
                onEdited: function(text) { panel.ctl.setPort(text) }
            }
            AppChoice {
                pal: panel.pal
                label: "Channel"
                fieldName: "midi-channel"
                choices: panel.channels()
                value: String(panel.dev.channel)
                onPicked: function(v) { panel.ctl.setChannel(parseInt(v)) }
            }
        }

        Rectangle {
            Layout.fillHeight: true
            implicitWidth: 1
            color: panel.pal.line
        }

        // The pad's factory RGB mode.
        ColumnLayout {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop
            spacing: 6
            // The heading and what the pad holds now share a line (the panel's height decides
            // how much room the pad view keeps).
            RowLayout {
                Layout.fillWidth: true
                spacing: 12
                Text {
                    text: "PAD LIGHTING (FACTORY MODES)"
                    font.pixelSize: 10
                    font.weight: Font.DemiBold
                    font.letterSpacing: 0.8
                    color: panel.pal.muted
                }
                Text {
                    objectName: "padNow"
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignRight
                    elide: Text.ElideRight
                    text: panel.dev.pad.text
                    font.pixelSize: 12
                    color: panel.pal.ink
                }
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                AppChoice {
                    pal: panel.pal
                    label: "Mode"
                    fieldName: "light-mode"
                    labelWidth: 40
                    choices: panel.modeChoices()
                    value: String(panel.light.mode)
                    onPicked: function(v) { panel.ctl.setLightingMode(parseInt(v)) }
                }
                AppChoice {
                    objectName: "brightnessRow"
                    visible: panel.light.brightness.shown
                    Layout.fillWidth: false
                    Layout.preferredWidth: 150
                    pal: panel.pal
                    label: "Brightness"
                    labelWidth: 66
                    fieldName: "light-brightness"
                    choices: panel.levelChoices()
                    value: String(panel.light.brightness.value)
                    onPicked: function(v) { panel.ctl.setLightingLevel("brightness", parseInt(v)) }
                }
                AppChoice {
                    objectName: "speedRow"
                    visible: panel.light.speed.shown
                    Layout.fillWidth: false
                    Layout.preferredWidth: 120
                    pal: panel.pal
                    label: "Speed"
                    labelWidth: 40
                    fieldName: "light-speed"
                    choices: panel.levelChoices()
                    value: String(panel.light.speed.value)
                    onPicked: function(v) { panel.ctl.setLightingLevel("speed", parseInt(v)) }
                }
            }
            ColumnLayout {
                objectName: "colorRow"
                visible: panel.light.color.shown
                Layout.fillWidth: true
                spacing: 6
                RowLayout {
                    spacing: 10
                    Text {
                        text: "One colour"
                        font.pixelSize: 12
                        color: panel.pal.muted
                    }
                    Switch {
                        objectName: "light-color-on"
                        checked: panel.light.color.on
                        onToggled: panel.ctl.setLightingColor(checked)
                    }
                    Rectangle {
                        objectName: "colorSwatch"
                        visible: panel.light.color.on
                        implicitWidth: 22
                        implicitHeight: 22
                        radius: 6
                        color: panel.light.color.swatch
                        border.color: panel.pal.line
                    }
                    Text {
                        visible: !panel.light.color.on
                        text: "off: the mode's own colours"
                        font.pixelSize: 12
                        color: panel.pal.muted
                    }
                }
                RowLayout {
                    visible: panel.light.color.on
                    Layout.fillWidth: true
                    spacing: 12
                    AppSlider {
                        pal: panel.pal
                        label: "H"
                        fieldName: "hue"
                        rainbow: true
                        value: panel.light.color.h
                        onPicked: function(v) { panel.ctl.setLightingHsv(0, v) }
                    }
                    AppSlider {
                        pal: panel.pal
                        label: "S"
                        fieldName: "sat"
                        value: panel.light.color.s
                        onPicked: function(v) { panel.ctl.setLightingHsv(1, v) }
                    }
                    AppSlider {
                        pal: panel.pal
                        label: "V"
                        fieldName: "val"
                        value: panel.light.color.v
                        onPicked: function(v) { panel.ctl.setLightingHsv(2, v) }
                    }
                }
            }
            Text {
                objectName: "lightNote"
                visible: !panel.light.set
                text: panel.light.hint
                font.pixelSize: 12
                color: panel.pal.muted
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                AppButton {
                    objectName: "applyButton"
                    text: panel.applyState.busy ? "Applying…" : "Apply to pad"
                    pal: panel.pal
                    primary: enabled
                    enabled: panel.applyState.enabled
                    onClicked: panel.ctl.applyLighting()
                }
                AppButton {
                    objectName: "refreshPadButton"
                    text: "Read pad"
                    pal: panel.pal
                    enabled: !panel.applyState.busy
                    onClicked: panel.ctl.refreshPad()
                }
                Text {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    text: panel.applyState.note
                    font.pixelSize: 12
                    color: panel.pal.muted
                }
            }
            Text {
                objectName: "applyLast"
                visible: panel.applyState.last !== "" || panel.applyState.problem !== ""
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                text: panel.applyState.problem !== "" ? panel.applyState.problem : panel.applyState.last
                font.pixelSize: 12
                font.weight: Font.DemiBold
                color: panel.applyState.problem !== "" ? panel.pal.errLine : panel.lastColor()
            }
        }
    }
}
