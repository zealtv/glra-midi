// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

// A labelled drop-down over `choices` ([{value, label}]); `value` is the current one.
RowLayout {
    id: c
    property var pal
    property string label
    property string fieldName
    property var choices: []
    property string value
    signal picked(string value)
    spacing: 8
    Layout.fillWidth: true

    Text {
        Layout.preferredWidth: 84
        text: c.label
        font.pixelSize: 12
        color: c.pal.muted
    }
    ComboBox {
        id: box
        objectName: "choice-" + c.fieldName
        Layout.fillWidth: true
        implicitHeight: 30
        font.pixelSize: 13
        model: c.choices
        textRole: "label"
        valueRole: "value"
        // `count` is read so the index is found again once the model has loaded or changed.
        currentIndex: count >= 0 ? indexOfValue(c.value) : -1
        onActivated: c.picked(currentValue)
        contentItem: Text {
            leftPadding: 10
            text: box.displayText
            font: box.font
            color: c.pal.ink
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
        background: Rectangle {
            radius: 7
            color: c.pal.surface
            border.width: box.activeFocus ? 2 : 1
            border.color: box.activeFocus ? c.pal.accent : c.pal.line
        }
    }
}
