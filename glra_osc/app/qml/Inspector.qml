// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Layouts

// The right-hand panel. In this stitch it only names the selected control and what it does
// on the shown tab; the editing fields arrive with `app-inspector`.
Rectangle {
    id: panel
    property var ctl
    property var pal
    readonly property var info: ctl.inspector
    color: pal.panel
    radius: 14
    border.color: pal.line

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 8
        Text {
            text: "INSPECTOR"
            font.pixelSize: 10
            font.weight: Font.DemiBold
            font.letterSpacing: 0.8
            color: panel.pal.muted
        }
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
            text: panel.info.subtitle
            font.pixelSize: 12
            color: panel.pal.muted
        }
        Repeater {
            model: panel.info.lines
            Text {
                required property string modelData
                text: modelData
                font.pixelSize: 14
                color: panel.pal.ink
            }
        }
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
        Text {
            visible: panel.info.selected
            Layout.fillWidth: true
            Layout.topMargin: 10
            wrapMode: Text.WordWrap
            text: panel.info.hint
            font.pixelSize: 12
            font.italic: true
            color: panel.pal.muted
        }
        Item { Layout.fillHeight: true }
    }
}
