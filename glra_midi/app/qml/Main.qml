// SPDX-License-Identifier: GPL-3.0-only
// Copyright (c) 2026 GLRA Studio contributors
// The palette-from-one-place and light/dark approach follow glra-studio's Main.qml (taken at
// commit 33aa281); the scheme comes from the system rather than a button.

import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

ApplicationWindow {
    id: root
    width: 1000
    height: 740
    minimumWidth: 860
    minimumHeight: 560
    visible: true
    title: controller.title

    // `controller.scheme` is "system" unless --dark or --light forced it (captures, testing).
    readonly property bool dark: controller.scheme === "dark"
        || (controller.scheme === "system" && Application.styleHints.colorScheme === Qt.Dark)
    // The palette, defined once; every component takes it as `pal`.
    readonly property var pal: dark ? {
        ink: "#edf3fc", muted: "#9eacc1", surface: "#1a2535", panel: "#151e2c",
        line: "#3a485c", hover: "#2b3a50", dim: "#1d2838", disabled: "#6c7a90",
        accent: "#4a7aff", accentDeep: "#6b92ff",
        globalBg: "#1d2b45", lockBg: "#213b68",
        warnBg: "#48301c", warnLine: "#ffad4d", errBg: "#4a2430", errLine: "#ff7d8f"
    } : {
        ink: "#1c2c44", muted: "#6e7e94", surface: "#ffffff", panel: "#f2f5fa",
        line: "#dce3ee", hover: "#f3f6fc", dim: "#eef1f6", disabled: "#95a1b3",
        accent: "#356cf6", accentDeep: "#285add",
        globalBg: "#f1f5ff", lockBg: "#e2ebff",
        warnBg: "#fff3e4", warnLine: "#e78216", errBg: "#fdecef", errLine: "#d4455c"
    }
    color: dark ? "#111a28" : "#f5f7fb"
    font.family: "Helvetica Neue"
    palette.windowText: pal.ink
    palette.text: pal.ink
    palette.buttonText: pal.ink
    palette.window: pal.surface
    palette.base: pal.surface

    property bool quitOk: false
    property bool deviceOpen: false  // the device panel strip, collapsed at start
    onClosing: function(close) {
        if ((controller.dirty || controller.applying) && !quitOk) {
            close.accepted = false
            controller.requestQuit()
        }
    }

    Connections {
        target: controller
        function onQuitApproved() { root.quitOk = true; root.close() }
        function onUnsavedPrompt(message) { unsavedDialog.message = message; unsavedDialog.open() }
        function onConfirmPrompt(title, message) {
            confirmDialog.heading = title
            confirmDialog.message = message
            confirmDialog.open()
        }
    }

    Shortcut { sequences: [StandardKey.Save]; onActivated: if (controller.canSave) controller.saveProfile() }
    Shortcut { sequences: [StandardKey.Open]; onActivated: openDialog.openList() }
    Shortcut { sequences: [StandardKey.SaveAs]; onActivated: saveAsDialog.openFor() }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 10

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            AppButton { objectName: "openButton"; text: "Open…"; pal: root.pal; onClicked: openDialog.openList() }
            AppButton {
                objectName: "saveButton"
                text: "Save"
                pal: root.pal
                primary: controller.dirty
                enabled: controller.canSave && controller.dirty
                onClicked: controller.saveProfile()
            }
            AppButton {
                objectName: "saveAsButton"
                text: "Save As…"
                pal: root.pal
                enabled: controller.canSaveAs
                onClicked: saveAsDialog.openFor()
            }
            AppButton { objectName: "revertButton"; text: "Revert"; pal: root.pal; onClicked: controller.revertProfile() }
            Item { Layout.fillWidth: true }
            Text {
                objectName: "padHeadline"
                text: controller.padHeadline
                font.pixelSize: 12
                color: controller.device.pad.connected ? root.pal.accent : root.pal.muted
            }
            Text {
                text: controller.profileName + (controller.dirty ? " •" : "")
                font.pixelSize: 13
                font.weight: Font.DemiBold
                color: root.pal.muted
            }
        }

        // Messages: a read error or save problem, a comments notice, a change on disk.
        Repeater {
            model: [
                { name: "error", text: controller.error, tone: "err" },
                { name: "notice", text: controller.notice, tone: "warn" },
                { name: "disk", text: controller.diskMessage, tone: "warn" }
            ]
            Rectangle {
                required property var modelData
                objectName: modelData.name + "Banner"
                visible: modelData.text !== ""
                Layout.fillWidth: true
                implicitHeight: visible ? bannerRow.implicitHeight + 16 : 0
                radius: 10
                color: modelData.tone === "err" ? root.pal.errBg : root.pal.warnBg
                border.color: modelData.tone === "err" ? root.pal.errLine : root.pal.warnLine
                RowLayout {
                    id: bannerRow
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 8
                    Text {
                        Layout.fillWidth: true
                        text: modelData.text
                        wrapMode: Text.WordWrap
                        font.pixelSize: 12
                        color: root.pal.ink
                    }
                    AppButton {
                        visible: modelData.name === "disk"
                        text: "Reload"
                        pal: root.pal
                        implicitHeight: 26
                        onClicked: controller.reloadFromDisk()
                    }
                    AppButton {
                        visible: modelData.name === "disk"
                        text: "Keep mine"
                        pal: root.pal
                        implicitHeight: 26
                        onClicked: controller.keepMine()
                    }
                    AppButton {
                        visible: modelData.name !== "disk"
                        text: "Dismiss"
                        pal: root.pal
                        implicitHeight: 26
                        onClicked: controller.dismissNotice()
                    }
                }
            }
        }

        // Problems that span controls block Save; each names the control.
        Rectangle {
            objectName: "problemsBox"
            visible: controller.problems.length > 0
            Layout.fillWidth: true
            implicitHeight: visible ? problemColumn.implicitHeight + 16 : 0
            radius: 10
            color: root.pal.errBg
            border.color: root.pal.errLine
            Column {
                id: problemColumn
                anchors.fill: parent
                anchors.margins: 8
                spacing: 4
                Repeater {
                    model: controller.problems
                    RowLayout {
                        required property var modelData
                        required property int index
                        width: problemColumn.width
                        Text {
                            Layout.fillWidth: true
                            text: modelData.message
                            wrapMode: Text.WordWrap
                            font.pixelSize: 12
                            color: root.pal.ink
                        }
                        AppButton {
                            visible: modelData.control !== ""
                            text: "Select"
                            pal: root.pal
                            implicitHeight: 26
                            onClicked: controller.selectProblem(index)
                        }
                    }
                }
            }
        }

        LayerTabs {
            objectName: "layerTabs"
            Layout.fillWidth: true
            ctl: controller
            pal: root.pal
            onRenameRequested: function(layer) { renameDialog.openFor(layer) }
            onRemoveRequested: function(layer) { controller.removeLayer(layer) }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 14
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: 14
                color: root.pal.panel
                border.color: root.pal.line
                PadView {
                    objectName: "padView"
                    anchors.fill: parent
                    ctl: controller
                    pal: root.pal
                }
                TapHandler { onTapped: controller.clearSelection() }
            }
            Inspector {
                objectName: "inspector"
                Layout.preferredWidth: 330
                Layout.fillHeight: true
                ctl: controller
                pal: root.pal
            }
        }

        DevicePanel {
            objectName: "devicePanel"
            visible: root.deviceOpen
            Layout.fillWidth: true
            ctl: controller
            pal: root.pal
        }

        // The device strip: one line when collapsed; a click opens the panel above it.
        Rectangle {
            objectName: "deviceStrip"
            Layout.fillWidth: true
            implicitHeight: 26
            radius: 8
            color: stripArea.containsMouse ? root.pal.hover : "transparent"
            Text {
                objectName: "deviceLine"
                anchors.fill: parent
                anchors.leftMargin: 6
                verticalAlignment: Text.AlignVCenter
                text: (root.deviceOpen ? "▾ " : "▸ ") + controller.deviceLine
                elide: Text.ElideRight
                font.pixelSize: 12
                color: root.pal.muted
            }
            MouseArea {
                id: stripArea
                objectName: "deviceStripArea"
                anchors.fill: parent
                hoverEnabled: true
                onClicked: root.deviceOpen = !root.deviceOpen
            }
        }
    }

    // --- dialogs -------------------------------------------------------------------------

    AppDialog {
        id: unsavedDialog
        objectName: "unsavedDialog"
        pal: root.pal
        property string message: ""
        heading: message
        Text {
            text: "Your changes will be lost if you don't save them."
            font.pixelSize: 12
            color: root.pal.muted
        }
        actions: [
            AppButton { text: "Cancel"; pal: root.pal; onClicked: { unsavedDialog.close(); controller.resolveUnsaved("cancel") } },
            AppButton { text: "Don't save"; pal: root.pal; onClicked: { unsavedDialog.close(); controller.resolveUnsaved("discard") } },
            AppButton { text: "Save"; pal: root.pal; primary: true; onClicked: { unsavedDialog.close(); controller.resolveUnsaved("save") } }
        ]
        onRejected: controller.resolveUnsaved("cancel")
    }

    AppDialog {
        id: confirmDialog
        objectName: "confirmDialog"
        pal: root.pal
        property string message: ""
        Text {
            Layout.fillWidth: true
            text: confirmDialog.message
            wrapMode: Text.WordWrap
            font.pixelSize: 13
            color: root.pal.ink
        }
        actions: [
            AppButton { text: "Cancel"; pal: root.pal; onClicked: { confirmDialog.close(); controller.resolveConfirm(false) } },
            AppButton { text: "OK"; pal: root.pal; primary: true; onClicked: { confirmDialog.close(); controller.resolveConfirm(true) } }
        ]
        onRejected: controller.resolveConfirm(false)
    }

    AppDialog {
        id: openDialog
        objectName: "openDialog"
        pal: root.pal
        heading: "Open a profile"
        property var names: []
        function openList() { names = controller.listProfiles(); open() }
        Text {
            visible: openDialog.names.length === 0
            text: "No profiles yet."
            color: root.pal.muted
        }
        Repeater {
            model: openDialog.names
            AppButton {
                required property string modelData
                Layout.fillWidth: true
                text: modelData + (modelData === controller.profileName ? "  (open)" : "")
                pal: root.pal
                onClicked: { openDialog.close(); controller.openProfile(modelData) }
            }
        }
        actions: [ AppButton { text: "Cancel"; pal: root.pal; onClicked: openDialog.close() } ]
    }

    AppDialog {
        id: saveAsDialog
        objectName: "saveAsDialog"
        pal: root.pal
        heading: "Save as"
        function openFor() { nameField.text = controller.profileName; open(); nameField.selectAll(); nameField.forceActiveFocus() }
        readonly property string problem: controller.checkName(nameField.text)
        TextField {
            id: nameField
            objectName: "saveAsField"
            Layout.fillWidth: true
            selectByMouse: true
            placeholderText: "Profile name"
            onAccepted: if (saveAsDialog.problem === "") saveAsDialog.accept()
        }
        Text {
            Layout.fillWidth: true
            visible: nameField.text !== "" && saveAsDialog.problem !== ""
            text: saveAsDialog.problem
            wrapMode: Text.WordWrap
            font.pixelSize: 12
            color: root.pal.errLine
        }
        actions: [
            AppButton { text: "Cancel"; pal: root.pal; onClicked: saveAsDialog.close() },
            AppButton {
                text: "Save"
                pal: root.pal
                primary: true
                enabled: saveAsDialog.problem === ""
                onClicked: saveAsDialog.accept()
            }
        ]
        onAccepted: controller.saveProfileAs(nameField.text)
    }

    AppDialog {
        id: renameDialog
        objectName: "renameDialog"
        pal: root.pal
        property int layer: 0
        heading: "Rename layer " + layer
        function openFor(n) {
            layer = n
            layerField.text = controller.tabs[n].label.replace(/^\d+ ?/, "")
            open()
            layerField.selectAll()
            layerField.forceActiveFocus()
        }
        TextField {
            id: layerField
            objectName: "renameField"
            Layout.fillWidth: true
            selectByMouse: true
            maximumLength: 24
            placeholderText: "Name (empty for none)"
            onAccepted: renameDialog.accept()
        }
        actions: [
            AppButton { text: "Cancel"; pal: root.pal; onClicked: renameDialog.close() },
            AppButton { text: "Rename"; pal: root.pal; primary: true; onClicked: renameDialog.accept() }
        ]
        onAccepted: controller.renameLayer(layer, layerField.text)
    }
}
