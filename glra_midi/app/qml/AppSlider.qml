// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

// A labelled 0..255 slider. It edits the profile as it moves (never the pad); `rainbow` draws
// the hue scale behind the track.
RowLayout {
    id: s
    property var pal
    property string label
    property string fieldName
    property int value: 0
    property bool rainbow: false
    signal picked(int value)
    spacing: 4
    Layout.fillWidth: true

    Text {
        Layout.preferredWidth: 14
        text: s.label
        font.pixelSize: 12
        color: s.pal.muted
    }
    Slider {
        id: slider
        objectName: "slider-" + s.fieldName
        Layout.fillWidth: true
        Layout.minimumWidth: 50
        Layout.preferredWidth: 80
        implicitHeight: 24
        from: 0
        to: 255
        stepSize: 1
        onMoved: s.picked(Math.round(value))
        // Keep following the profile, also after the user has dragged.
        Binding { target: slider; property: "value"; value: s.value; when: !slider.pressed }
        background: Rectangle {
            x: slider.leftPadding
            y: slider.topPadding + slider.availableHeight / 2 - height / 2
            width: slider.availableWidth
            height: 8
            radius: 4
            color: s.pal.dim
            border.color: s.pal.line
            Rectangle {
                anchors.fill: parent
                radius: 4
                visible: s.rainbow
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0.0; color: "#ff3b3b" }
                    GradientStop { position: 0.17; color: "#ffd23b" }
                    GradientStop { position: 0.33; color: "#4bd64b" }
                    GradientStop { position: 0.5; color: "#3bd6d6" }
                    GradientStop { position: 0.67; color: "#3b5bff" }
                    GradientStop { position: 0.83; color: "#d63bd6" }
                    GradientStop { position: 1.0; color: "#ff3b3b" }
                }
            }
        }
        handle: Rectangle {
            x: slider.leftPadding + slider.visualPosition * (slider.availableWidth - width)
            y: slider.topPadding + slider.availableHeight / 2 - height / 2
            width: 16
            height: 16
            radius: 8
            color: s.pal.surface
            border.width: slider.activeFocus || slider.pressed ? 2 : 1
            border.color: slider.activeFocus || slider.pressed ? s.pal.accent : s.pal.muted
        }
    }
    Text {
        Layout.preferredWidth: 26
        horizontalAlignment: Text.AlignRight
        text: s.value
        font.pixelSize: 12
        color: s.pal.muted
    }
}
