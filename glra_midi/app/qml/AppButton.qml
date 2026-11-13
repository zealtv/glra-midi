// SPDX-License-Identifier: GPL-3.0-only
// Copyright (c) 2026 GLRA Studio contributors
// Adapted from glra-studio's StudioButton.qml (taken at commit 33aa281): palette comes from
// the window's `pal` instead of per-button colour pairs.

import QtQuick
import QtQuick.Controls.Basic

Button {
    id: b
    property var pal
    property bool primary: false
    property int textSize: 13
    implicitHeight: 32
    implicitWidth: Math.max(64, label.implicitWidth + 24)
    focusPolicy: Qt.NoFocus
    hoverEnabled: true
    contentItem: Text {
        id: label
        text: b.text
        font.pixelSize: b.textSize
        font.weight: Font.DemiBold
        color: !b.enabled ? b.pal.disabled : b.primary ? "white" : b.pal.ink
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }
    background: Rectangle {
        radius: 8
        color: !b.enabled ? b.pal.dim
            : b.primary ? (b.hovered ? b.pal.accentDeep : b.pal.accent)
            : b.hovered ? b.pal.hover : b.pal.surface
        border.width: b.primary ? 0 : 1
        border.color: b.pal.line
    }
}
