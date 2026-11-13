// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Layouts

// The pad as the chosen orientation draws it: 16 keys on a 4 x 4 grid, three dials along
// one edge. Placement comes from the controller (`keys` in displayed order, `dialSide`).
Item {
    id: pad
    property var ctl
    property var pal

    readonly property string side: ctl.dialSide
    readonly property bool sideways: side === "left" || side === "right"
    readonly property int tileW: 100
    readonly property int tileH: 66
    readonly property int gap: 10
    readonly property int gridW: 4 * tileW + 3 * gap
    readonly property int gridH: 4 * tileH + 3 * gap
    implicitWidth: layout.implicitWidth
    implicitHeight: layout.implicitHeight

    GridLayout {
        id: layout
        objectName: "padLayout"
        anchors.centerIn: parent
        // Shrink, never grow, when the window is small.
        scale: Math.min(1, (pad.height - 16) / implicitHeight, (pad.width - 16) / implicitWidth)
        columns: pad.sideways ? 2 : 1
        columnSpacing: 18
        rowSpacing: 10

        Grid {
            id: dialBlock
            objectName: "dialBlock"
            Layout.row: pad.sideways ? 0 : (pad.side === "top" ? 0 : 1)
            Layout.column: pad.sideways ? (pad.side === "left" ? 0 : 1) : 0
            Layout.alignment: Qt.AlignCenter
            columns: pad.sideways ? 1 : 3
            spacing: pad.sideways ? (pad.gridH - 3 * 74) / 2 : (pad.gridW - 3 * 130) / 2
            Repeater {
                model: pad.ctl.dials
                DialTile {
                    required property var modelData
                    dial: modelData
                    pal: pad.pal
                    sideways: pad.sideways
                    onPicked: function(control) { pad.ctl.selectControl(control) }
                }
            }
        }

        Grid {
            id: keyGrid
            objectName: "keyGrid"
            Layout.row: pad.sideways ? 0 : (pad.side === "top" ? 1 : 0)
            Layout.column: pad.sideways ? (pad.side === "left" ? 1 : 0) : 0
            Layout.alignment: Qt.AlignCenter
            columns: 4
            spacing: pad.gap
            Repeater {
                model: pad.ctl.keys
                KeyTile {
                    required property var modelData
                    width: pad.tileW; height: pad.tileH
                    tile: modelData
                    pal: pad.pal
                    onPicked: function(control) { pad.ctl.selectControl(control) }
                }
            }
        }
    }
}
