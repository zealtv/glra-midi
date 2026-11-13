// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Layouts

// A labelled row of buttons, one of them chosen (an Action or Applies row).
RowLayout {
    id: s
    property var pal
    property string label
    property string fieldName
    property var choices: []        // [{value, label}]
    property string value
    signal picked(string value)
    spacing: 4
    Layout.fillWidth: true

    Text {
        Layout.preferredWidth: 84
        text: s.label
        font.pixelSize: 12
        color: s.pal.muted
    }
    Repeater {
        model: s.choices
        AppButton {
            required property var modelData
            objectName: "seg-" + s.fieldName + "-" + modelData.value
            Layout.fillWidth: true
            Layout.preferredWidth: 1
            implicitWidth: 40
            implicitHeight: 28
            textSize: 12
            pal: s.pal
            text: modelData.label
            primary: modelData.value === s.value
            Accessible.checked: primary
            onClicked: s.picked(modelData.value)
        }
    }
}
