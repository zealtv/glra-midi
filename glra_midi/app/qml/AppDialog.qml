// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

// A modal box in the app's palette: a title, a body, and a row of buttons.
Dialog {
    id: dlg
    property var pal
    property alias heading: headingText.text
    default property alias body: bodyColumn.data
    property alias actions: actionRow.data

    modal: true
    anchors.centerIn: Overlay.overlay
    padding: 20
    background: Rectangle {
        radius: 14
        color: dlg.pal.surface
        border.color: dlg.pal.line
    }
    Overlay.modal: Rectangle { color: Qt.rgba(0, 0, 0, 0.35) }
    contentItem: ColumnLayout {
        spacing: 14
        implicitWidth: 360
        Text {
            id: headingText
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            font.pixelSize: 16
            font.weight: Font.Bold
            color: dlg.pal.ink
        }
        ColumnLayout { id: bodyColumn; Layout.fillWidth: true; spacing: 8 }
        RowLayout {
            id: actionRow
            Layout.alignment: Qt.AlignRight
            spacing: 8
        }
    }
}
