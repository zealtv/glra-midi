// SPDX-License-Identifier: GPL-3.0-only

import QtQuick

// One dial: a round push tile and a turn tile. Each selects on its own.
Item {
    id: d
    property var dial
    property var pal
    property bool sideways: false   // dials down a side: push and turn sit next to each other
    signal picked(string control)

    implicitWidth: sideways ? 180 : 130
    implicitHeight: sideways ? 74 : 128

    Grid {
        anchors.centerIn: parent
        columns: d.sideways ? 2 : 1
        spacing: 4
        horizontalItemAlignment: Grid.AlignHCenter
        verticalItemAlignment: Grid.AlignVCenter
        KeyTile {
            width: 74; height: 74
            round: true
            tile: d.dial.push
            pal: d.pal
            onPicked: function(control) { d.picked(control) }
        }
        KeyTile {
            width: d.sideways ? 96 : 120; height: d.sideways ? 58 : 50
            tile: d.dial.turn
            pal: d.pal
            onPicked: function(control) { d.picked(control) }
        }
    }
}
