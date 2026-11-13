// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

// Global, then 1..n, then [+]. Right-click a layer tab (or use the buttons) to rename or remove.
RowLayout {
    id: tabs
    property var ctl
    property var pal
    signal renameRequested(int layer)
    signal removeRequested(int layer)
    spacing: 6

    Repeater {
        model: tabs.ctl.tabs
        Button {
            id: tab
            required property var modelData
            readonly property bool current: modelData.index === tabs.ctl.tab
            objectName: "tab" + modelData.index
            focusPolicy: Qt.NoFocus
            hoverEnabled: true
            implicitHeight: 30
            implicitWidth: Math.max(48, text.implicitWidth + 24)
            Accessible.name: (modelData.index === 0 ? "Global tab" : "Layer " + modelData.label)
                + (current ? ", selected" : "")
            onClicked: tabs.ctl.selectTab(modelData.index)
            contentItem: Text {
                id: text
                text: tab.modelData.label
                font.pixelSize: 13
                font.weight: tab.current ? Font.Bold : Font.Medium
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                color: tab.current ? "white" : tab.pal.ink
            }
            readonly property var pal: tabs.pal
            background: Rectangle {
                radius: 15
                color: tab.current ? tab.pal.accent : tab.hovered ? tab.pal.hover : tab.pal.surface
                border.width: tab.current ? 0 : 1
                border.color: tab.pal.line
            }
            TapHandler {
                acceptedButtons: Qt.RightButton
                enabled: tab.modelData.index > 0
                onTapped: {
                    tabs.ctl.selectTab(tab.modelData.index)
                    menu.popup()
                }
            }
            Menu {
                id: menu
                MenuItem { text: "Rename…"; onTriggered: tabs.renameRequested(tab.modelData.index) }
                MenuItem { text: "Remove…"; onTriggered: tabs.removeRequested(tab.modelData.index) }
            }
        }
    }
    AppButton {
        objectName: "addLayer"
        text: "+"
        pal: tabs.pal
        implicitWidth: 34
        enabled: tabs.ctl.layerCount < 8
        Accessible.name: "Add a layer"
        onClicked: tabs.ctl.addLayer()
    }
    Item { Layout.fillWidth: true }
    AppButton {
        objectName: "renameLayer"
        text: "Rename…"
        pal: tabs.pal
        enabled: tabs.ctl.tab > 0
        onClicked: tabs.renameRequested(tabs.ctl.tab)
    }
    AppButton {
        objectName: "removeLayer"
        text: "Remove…"
        pal: tabs.pal
        enabled: tabs.ctl.tab > 0 && tabs.ctl.layerCount > 1
        onClicked: tabs.removeRequested(tabs.ctl.tab)
    }
}
