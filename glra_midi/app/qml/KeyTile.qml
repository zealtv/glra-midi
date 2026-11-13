// SPDX-License-Identifier: GPL-3.0-only
// Copyright (c) 2026 GLRA Studio contributors
// Adapted from glra-studio's KeyTile.qml (taken at commit 33aa281): the tile takes a
// controller-built `tile` map (state, badge, two text lines, selected) instead of a slot entry.

import QtQuick
import QtQuick.Controls.Basic

Button {
    id: b
    property var tile
    property var pal
    property bool round: false
    signal picked(string control)

    readonly property string st: tile.state
    objectName: "tile-" + tile.control
    focusPolicy: Qt.NoFocus
    hoverEnabled: true
    padding: 0
    onClicked: picked(tile.control)
    Accessible.name: tile.label + ": " + tile.line1 + (tile.line2 ? ", " + tile.line2 : "")
        + (tile.state === "global" ? ", same on every layer" : "")
        + (tile.state === "layer-key" ? ", layer key, same on every layer" : "")
    ToolTip.visible: hovered
    ToolTip.delay: 450
    ToolTip.text: tile.label + ": " + tile.line1 + (tile.line2 ? " · " + tile.line2 : "")

    background: Rectangle {
        radius: b.round ? Math.min(width, height) / 2 : 12
        color: b.st === "layer-key" ? b.pal.lockBg
            : b.st === "global" ? b.pal.globalBg
            : b.st === "per-layer" ? b.pal.dim
            : b.hovered ? b.pal.hover : b.pal.surface
        border.width: b.tile.selected ? 3 : 1
        border.color: b.tile.selected ? b.pal.accent : b.pal.line
        opacity: b.st === "per-layer" ? 0.75 : 1
    }
    contentItem: Item {
        Text {
            id: caption
            text: b.tile.caption
            anchors.top: parent.top
            anchors.topMargin: b.round ? 9 : 5
            anchors.left: b.round ? undefined : parent.left
            anchors.leftMargin: 7
            anchors.horizontalCenter: b.round ? parent.horizontalCenter : undefined
            // On a round tile the badge sits beside the caption; shift both to stay centred.
            anchors.horizontalCenterOffset: b.round && badge.visible ? -(badge.width + 3) / 2 : 0
            font.pixelSize: 10
            color: b.pal.muted
        }
        Rectangle {
            id: badge
            visible: b.tile.badge !== ""
            anchors.verticalCenter: caption.verticalCenter
            anchors.right: b.round ? undefined : parent.right
            anchors.rightMargin: 5
            anchors.left: b.round ? caption.right : undefined
            anchors.leftMargin: 3
            width: Math.max(18, badgeText.implicitWidth + 8)
            height: 16
            radius: 8
            color: b.st === "global" ? b.pal.accent : "transparent"
            Text {
                id: badgeText
                anchors.centerIn: parent
                text: b.tile.badge
                font.pixelSize: 10
                font.weight: Font.Bold
                color: b.st === "global" ? "white" : b.pal.ink
            }
        }
        Column {
            anchors.centerIn: parent
            anchors.verticalCenterOffset: b.round ? 6 : 6
            width: parent.width - (b.round ? 4 : 10)
            spacing: 1
            Text {
                width: parent.width
                text: b.tile.line1
                font.pixelSize: b.round ? 11 : (b.tile.line1.length > 11 ? 12 : 13)
                font.weight: Font.DemiBold
                horizontalAlignment: Text.AlignHCenter
                elide: Text.ElideRight
                color: b.st === "empty" ? b.pal.muted : b.pal.ink
            }
            Text {
                visible: b.tile.line2 !== ""
                width: parent.width
                text: b.tile.line2
                font.pixelSize: 10
                horizontalAlignment: Text.AlignHCenter
                elide: Text.ElideRight
                color: b.pal.muted
            }
        }
    }
}
