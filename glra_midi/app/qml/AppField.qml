// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

// One labelled number field. It shows the text the controller holds for it and sends what is
// typed; an invalid entry stays in the field with the profile's own message beneath it.
ColumnLayout {
    id: f
    property var pal
    property string label
    property string fieldName
    property var entry              // {text, error, range} from the controller
    property string note: ""        // shown beside the field (a note's name)
    signal edited(string text)
    spacing: 2
    Layout.fillWidth: true

    RowLayout {
        Layout.fillWidth: true
        spacing: 8
        Text {
            Layout.preferredWidth: 84
            text: f.label
            font.pixelSize: 12
            color: f.pal.muted
        }
        TextField {
            id: input
            objectName: "field-" + f.fieldName
            Layout.fillWidth: true
            implicitHeight: 30
            selectByMouse: true
            font.pixelSize: 13
            color: f.pal.ink
            placeholderText: f.entry ? f.entry.range : ""
            text: f.entry ? f.entry.text : ""
            onTextEdited: f.edited(text)
            background: Rectangle {
                radius: 7
                color: f.pal.surface
                border.width: input.activeFocus ? 2 : 1
                border.color: f.entry && f.entry.error !== "" ? f.pal.errLine
                    : input.activeFocus ? f.pal.accent : f.pal.line
            }
        }
        Text {
            visible: f.note !== ""
            text: f.note
            font.pixelSize: 12
            font.weight: Font.DemiBold
            color: f.pal.muted
        }
    }
    Text {
        objectName: "error-" + f.fieldName
        visible: f.entry !== undefined && f.entry.error !== ""
        Layout.fillWidth: true
        Layout.leftMargin: 92
        wrapMode: Text.WordWrap
        text: f.entry ? f.entry.error : ""
        font.pixelSize: 11
        color: f.pal.errLine
    }
}
