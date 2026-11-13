# SPDX-License-Identifier: GPL-3.0-only

import time
import unittest
from dataclasses import replace

from . import qt_support  # noqa: F401 - skips this module without PySide6, sets up Qt
from .qt_support import make_home, write_profile

from glra_midi import profile as prof
from glra_midi.app.controller import Controller, has_comments

NOTHING = "version = 1\n"


class Recorder:
    """Collects a controller's prompts."""

    def __init__(self, controller):
        self.unsaved, self.confirm, self.quit = [], [], []
        controller.unsavedPrompt.connect(self.unsaved.append)
        controller.confirmPrompt.connect(lambda title, text: self.confirm.append((title, text)))
        controller.quitApproved.connect(lambda: self.quit.append(True))


class ControllerCase(unittest.TestCase):
    def setUp(self):
        self.home = make_home(self)
        self.c = self.make()
        self.rec = Recorder(self.c)

    def make(self):
        c = Controller(home=self.home)
        self.addCleanup(c.deleteLater)
        return c

    def disk(self, name="default"):
        return prof.load_profile(prof.profile_path(name, self.home))

    def touch_disk(self, name, text):
        """Rewrite a profile as another program would: a new file renamed into place."""
        path = prof.profile_path(name, self.home)
        prof._write_atomic(path, text)
        return path


class StartTests(ControllerCase):
    def test_opens_the_current_profile_clean(self):
        self.assertEqual(self.c.profileName, "default")
        self.assertFalse(self.c.dirty)
        self.assertEqual(self.c.title, "glra-midi config — default")
        self.assertEqual(self.c.profile.layer_count, 4)

    def test_starts_on_the_shipped_default_when_there_is_no_profile(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            c = Controller(home=Path(tmp))
            self.addCleanup(c.deleteLater)
            self.assertEqual(c.profileName, "default")
            self.assertFalse(c.dirty)
            self.assertTrue(prof.profile_path("default", Path(tmp)).is_file())
            self.assertEqual(c.profile.layer_count, 3)  # Bob's Q3 default

    def test_starts_on_layer_1(self):
        self.assertEqual(self.c.tab, 1)

    def test_a_file_with_comments_gets_one_notice_per_file(self):
        self.assertIn("has comments", self.c.notice)
        self.c.dismissNotice()
        self.assertEqual(self.c.notice, "")
        self.c.revertProfile()  # re-reads the same file
        self.assertEqual(self.c.notice, "")

    def test_has_comments_ignores_the_header_the_app_writes(self):
        self.assertFalse(has_comments(prof.HEADER + "\nversion = 1\n"))
        self.assertTrue(has_comments("# my notes\nversion = 1\n"))

    def test_a_broken_current_profile_shows_the_error_and_blocks_save(self):
        home = make_home(self, "version = 1\n[key.1]\nkind = \"nonsense\"\n")
        c = Controller(home=home)
        self.addCleanup(c.deleteLater)
        self.assertIn("kind", c.error)
        self.assertFalse(c.canSave)
        self.assertTrue(c.canSaveAs)
        before = prof.profile_path("default", home).read_text()
        c.saveProfile()
        self.assertEqual(prof.profile_path("default", home).read_text(), before)
        c.saveProfileAs("fresh")
        self.assertEqual(prof.load_profile(prof.profile_path("fresh", home)), prof.Profile())
        self.assertEqual(prof.current_profile_path(home).stem, "fresh")
        self.assertEqual(c.error, "")
        self.assertTrue(c.canSave)


class TabAndSelectionTests(ControllerCase):
    def test_tabs_list_global_then_layers_with_names(self):
        labels = [t["label"] for t in self.c.tabs]
        self.assertEqual(labels, ["Global", "1 Drums", "2 Synth", "3", "4 Mixer"])

    def test_select_tab_shows_that_layer_and_ignores_out_of_range(self):
        def key2():
            return next(k for k in self.c.keys if k["control"] == "key.2")["line1"]

        self.assertEqual(key2(), "Note C#1")
        self.c.selectTab(2)
        self.assertEqual(key2(), "CC20 10↔120")
        self.c.selectTab(0)
        self.assertEqual(key2(), "per layer")
        self.c.selectTab(9)
        self.c.selectTab(-1)
        self.assertEqual(self.c.tab, 0)
        self.assertFalse(self.c.dirty)

    def test_global_and_layer_key_tiles_look_the_same_on_every_tab(self):
        def tiles(tab):
            self.c.selectTab(tab)
            return {
                k["control"]: (k["state"], k["badge"], k["line1"])
                for k in self.c.keys
                if k["control"] in ("key.1", "key.13")
            }

        self.assertEqual(tiles(1), tiles(3))
        self.assertEqual(tiles(1), tiles(0))
        self.assertEqual(tiles(1)["key.1"][1], "G")
        self.assertEqual(tiles(1)["key.13"][1], "🔒")

    def test_selecting_a_control_highlights_it_and_names_it_in_the_inspector(self):
        self.c.selectControl("key.2")
        self.assertEqual(self.c.selected, "key.2")
        tile = next(k for k in self.c.keys if k["control"] == "key.2")
        self.assertTrue(tile["selected"])
        self.assertEqual(self.c.inspector["title"], "KEY 2")
        self.assertEqual(self.c.inspector["subtitle"], 'layer 1 "Drums"')
        self.assertFalse(self.c.dirty)

    def test_selection_survives_a_tab_change_and_clears(self):
        self.c.selectControl("enc.2.turn")
        self.c.selectTab(2)
        self.assertEqual(self.c.selected, "enc.2.turn")
        self.assertEqual(self.c.inspector["title"], "DIAL 2 TURN")
        self.c.clearSelection()
        self.assertEqual(self.c.selected, "")
        self.assertFalse(self.c.inspector["selected"])

    def test_unknown_controls_are_ignored(self):
        self.c.selectControl("key.99")
        self.c.selectControl("enc.1")
        self.assertEqual(self.c.selected, "")

    def test_layer_key_inspector_says_it_is_on_every_layer(self):
        self.c.selectControl("enc.3.push")
        self.assertIn("every layer", self.c.inspector["subtitle"])

    def test_nothing_selected_counts_what_the_shown_layer_does(self):
        self.assertIn('Layer 1 "Drums"', self.c.inspector["count"])
        self.assertIn("of 22", self.c.inspector["count"])
        self.c.selectTab(0)
        self.assertIn("Global tab", self.c.inspector["count"])


class OrientationTests(ControllerCase):
    def test_displayed_numbers_follow_the_orientation_but_the_file_does_not(self):
        self.c.setOrientation("dials-right")
        first = self.c.keys[0]
        self.assertEqual((first["number"], first["control"]), (1, "key.13"))
        self.assertEqual(self.c.dialSide, "right")
        self.assertEqual(self.c.inspector["title"], "")
        self.c.selectControl("key.13")
        self.assertEqual(self.c.inspector["title"], "KEY 1")
        self.assertEqual([d["push"]["control"] for d in self.c.dials], [
            "enc.1.push", "enc.2.push", "enc.3.push"
        ])
        self.assertTrue(self.c.dirty)
        self.assertEqual(self.c.profile.controls, self.disk().controls)  # same assignments

    def test_dials_bottom_reverses_the_dials(self):
        self.c.setOrientation("dials-bottom")
        self.assertEqual(
            [d["turn"]["control"] for d in self.c.dials], ["enc.3.turn", "enc.2.turn", "enc.1.turn"]
        )

    def test_keys_come_in_displayed_order_with_cells(self):
        self.c.setOrientation("dials-left")
        self.assertEqual([k["number"] for k in self.c.keys], list(range(1, 17)))
        self.assertEqual((self.c.keys[5]["row"], self.c.keys[5]["col"]), (1, 1))

    def test_bad_orientation_is_refused(self):
        self.c.setOrientation("upside-down")
        self.assertIn("orientation", self.c.error)
        self.assertEqual(self.c.orientation, "dials-top")


class LayerEditTests(ControllerCase):
    def test_rename_marks_dirty_and_renaming_back_clears_it(self):
        self.c.renameLayer(1, "Kit")
        self.assertTrue(self.c.dirty)
        self.assertTrue(self.c.title.endswith(" •"))
        self.assertEqual(self.c.tabs[1]["label"], "1 Kit")
        self.c.renameLayer(1, "Drums")
        self.assertFalse(self.c.dirty)

    def test_add_layer_selects_it_and_stops_at_eight(self):
        for _ in range(4):
            self.c.addLayer()
        self.assertEqual((self.c.layerCount, self.c.tab), (8, 8))
        self.c.addLayer()
        self.assertEqual(self.c.layerCount, 8)
        self.assertIn("at most", self.c.error)

    def test_removing_an_empty_layer_needs_no_question(self):
        self.c.selectTab(3)
        self.c.removeLayer(3)  # layer 3 has no events in the demo
        self.assertEqual(self.rec.confirm, [])
        self.assertEqual(self.c.layerCount, 3)
        self.assertEqual(self.c.tab, 3)  # clamps to the last layer that remains

    def test_removing_a_layer_with_events_asks_and_waits(self):
        before = self.c.profile
        self.c.removeLayer(1)
        self.assertEqual(len(self.rec.confirm), 1)
        self.assertIn("Layer 1 has", self.rec.confirm[0][1])
        self.assertEqual(self.c.profile, before)
        self.c.resolveConfirm(True)
        self.assertEqual(self.c.layerCount, 3)
        self.assertEqual(self.c.tabs[1]["label"], "1 Synth")
        self.assertTrue(self.c.dirty)

    def test_saying_no_keeps_the_layer(self):
        self.c.removeLayer(1)
        self.c.resolveConfirm(False)
        self.assertEqual(self.c.layerCount, 4)
        self.assertFalse(self.c.dirty)

    def test_tab_follows_the_layer_it_was_on(self):
        self.c.selectTab(4)
        self.c.removeLayer(3)  # empty, below the shown tab
        self.assertEqual(self.c.tab, 3)

    def test_the_last_layer_stays(self):
        home = make_home(self, "version = 1\n[layers]\ncount = 1\n")
        c = Controller(home=home)
        self.addCleanup(c.deleteLater)
        c.removeLayer(1)
        self.assertEqual(c.layerCount, 1)
        self.assertIn("at least one", c.error)

    def test_layer_keys_follow_their_layer_when_one_below_is_removed(self):
        controls = dict(self.c.profile.controls)
        controls["enc.3.push"] = prof.LayerSet(layer=4)
        self.c._edit(replace(self.c.profile, controls=controls))
        self.c.removeLayer(3)  # empty
        self.assertEqual(self.c.profile.controls["enc.3.push"], prof.LayerSet(layer=3))
        self.assertEqual(self.c.problems, [])

    def test_layer_key_pointing_at_the_removed_layer_is_flagged_and_blocks_save(self):
        controls = dict(self.c.profile.controls)
        controls["enc.3.push"] = prof.LayerSet(layer=3)
        self.c._edit(replace(self.c.profile, controls=controls))
        self.c.removeLayer(3)  # empty: goes straight through
        self.assertEqual(len(self.c.problems), 1)
        self.assertIn("Dial 3 push", self.c.problems[0]["message"])
        self.assertIn("the layer it pointed at was removed", self.c.problems[0]["message"])
        self.assertEqual(self.c.problems[0]["control"], "enc.3.push")
        self.assertFalse(self.c.canSave)
        # choosing another layer clears it
        self.c.selectControl("enc.3.push")
        self.c.setLayerKey("layer-set", 2)
        self.assertEqual(self.c.problems, [])
        self.assertTrue(self.c.canSave)

    def test_removing_the_last_layer_flags_a_key_that_pointed_at_it(self):
        self.c.selectTab(4)
        controls = dict(self.c.profile.controls)
        controls["enc.3.push"] = prof.LayerSet(layer=4)
        self.c._edit(replace(self.c.profile, controls=controls))
        self.assertEqual(self.c.problems, [])
        self.c.removeLayer(4)  # empty: goes straight through
        self.assertEqual(len(self.c.problems), 1)
        self.assertIn("the layer it pointed at was removed", self.c.problems[0]["message"])
        self.assertFalse(self.c.canSave)
        self.c.saveProfile()
        self.assertTrue(self.c.dirty)
        self.assertIn("Fix 1 problem", self.c.error)
        self.assertEqual(self.disk().layer_count, 4)

    def test_problem_messages_use_displayed_numbers(self):
        self.c.setOrientation("dials-right")
        controls = dict(self.c.profile.controls)
        controls["key.13"] = prof.LayerSet(layer=7)  # displayed key 1 in dials-right
        self.c._edit(replace(self.c.profile, controls=controls))
        self.assertTrue(self.c.problems[0]["message"].startswith("Key 1 (layer): "))


class SaveTests(ControllerCase):
    def test_save_writes_the_file_and_clears_dirty(self):
        self.c.renameLayer(2, "Pads")
        self.c.saveProfile()
        self.assertFalse(self.c.dirty)
        self.assertEqual(self.disk().layer_names[1], "Pads")
        self.assertEqual(self.disk(), self.c.profile)

    def test_own_save_does_not_trigger_a_reload_notice(self):
        self.c.renameLayer(2, "Pads")
        self.c.saveProfile()
        self.c.poll()
        self.assertEqual(self.c.diskMessage, "")
        self.assertFalse(self.c.dirty)

    def test_save_as_writes_a_new_profile_and_points_current_at_it(self):
        self.c.renameLayer(1, "Kit")
        self.c.saveProfileAs("drums")
        self.assertEqual(self.c.profileName, "drums")
        self.assertFalse(self.c.dirty)
        self.assertEqual(self.disk("drums").layer_names[0], "Kit")
        self.assertEqual(self.disk("default").layer_names[0], "Drums")  # the old file is untouched
        self.assertEqual(prof.current_profile_path(self.home).stem, "drums")

    def test_save_as_over_another_profile_asks_first(self):
        write_profile(self.home, "other", NOTHING)
        self.c.saveProfileAs("other")
        self.assertEqual(len(self.rec.confirm), 1)
        self.assertEqual(self.disk("other").layer_count, prof.DEFAULT_LAYERS)
        self.assertEqual(self.c.profileName, "default")
        self.c.resolveConfirm(True)
        self.assertEqual(self.c.profileName, "other")
        self.assertEqual(self.disk("other").layer_names[0], "Drums")

    def test_save_as_with_a_bad_name_is_refused(self):
        self.c.saveProfileAs("../evil")
        self.assertIn("profile name", self.c.error)
        self.assertEqual(self.c.profileName, "default")
        self.assertNotEqual(self.c.checkName(".hidden"), "")
        self.assertNotEqual(self.c.checkName(""), "")
        self.assertEqual(self.c.checkName("drums 2"), "")

    def test_save_as_the_open_name_is_a_plain_save(self):
        self.c.renameLayer(1, "Kit")
        self.c.saveProfileAs("default")
        self.assertEqual(self.rec.confirm, [])
        self.assertEqual(self.disk().layer_names[0], "Kit")


class OpenAndRevertTests(ControllerCase):
    def setUp(self):
        super().setUp()
        write_profile(self.home, "empty", NOTHING)

    def test_list_profiles(self):
        self.assertEqual(self.c.listProfiles(), ["default", "empty"])

    def test_open_loads_it_and_points_current_at_it(self):
        self.c.openProfile("empty")
        self.assertEqual(self.c.profileName, "empty")
        self.assertEqual(self.c.profile.controls, {})
        self.assertEqual(prof.current_profile_path(self.home).stem, "empty")
        self.assertFalse(self.c.dirty)
        self.assertEqual(self.rec.unsaved, [])

    def test_open_with_unsaved_changes_prompts_and_cancel_stays(self):
        self.c.renameLayer(1, "Kit")
        self.c.openProfile("empty")
        self.assertEqual(self.rec.unsaved, ["Save changes to default?"])
        self.assertEqual(self.c.profileName, "default")
        self.c.resolveUnsaved("cancel")
        self.assertEqual(self.c.profileName, "default")
        self.assertTrue(self.c.dirty)

    def test_open_then_discard_drops_the_edits(self):
        self.c.renameLayer(1, "Kit")
        self.c.openProfile("empty")
        self.c.resolveUnsaved("discard")
        self.assertEqual(self.c.profileName, "empty")
        self.assertEqual(self.disk().layer_names[0], "Drums")

    def test_open_then_save_writes_first(self):
        self.c.renameLayer(1, "Kit")
        self.c.openProfile("empty")
        self.c.resolveUnsaved("save")
        self.assertEqual(self.c.profileName, "empty")
        self.assertEqual(self.disk().layer_names[0], "Kit")

    def test_open_then_save_with_problems_stays_put(self):
        self.c.selectTab(4)
        controls = dict(self.c.profile.controls)
        controls["enc.3.push"] = prof.LayerSet(layer=4)
        self.c._edit(replace(self.c.profile, controls=controls))
        self.c.removeLayer(4)
        self.c.openProfile("empty")
        self.c.resolveUnsaved("save")
        self.assertEqual(self.c.profileName, "default")
        self.assertIn("Fix 1 problem", self.c.error)

    def test_open_refuses_a_file_that_will_not_read(self):
        write_profile(self.home, "bad", "not a profile\n")
        self.c.openProfile("bad")
        self.assertEqual(self.c.profileName, "default")
        self.assertIn("Can't open bad", self.c.error)
        self.assertEqual(prof.current_profile_path(self.home).stem, "default")

    def test_revert_asks_when_dirty_and_restores_the_file(self):
        self.c.renameLayer(1, "Kit")
        self.c.revertProfile()
        self.assertEqual(len(self.rec.confirm), 1)
        self.assertTrue(self.c.dirty)
        self.c.resolveConfirm(True)
        self.assertFalse(self.c.dirty)
        self.assertEqual(self.c.profile.layer_names[0], "Drums")

    def test_revert_when_clean_just_rereads(self):
        self.c.revertProfile()
        self.assertEqual(self.rec.confirm, [])

    def test_quit_clean_goes_ahead_and_dirty_asks(self):
        self.c.requestQuit()
        self.assertEqual(self.rec.quit, [True])
        self.c.renameLayer(1, "Kit")
        self.c.requestQuit()
        self.assertEqual(len(self.rec.unsaved), 1)
        self.assertEqual(self.rec.quit, [True])
        self.c.resolveUnsaved("save")
        self.assertEqual(self.rec.quit, [True, True])
        self.assertEqual(self.disk().layer_names[0], "Kit")

    def test_quit_cancel_stays_open(self):
        self.c.renameLayer(1, "Kit")
        self.c.requestQuit()
        self.c.resolveUnsaved("cancel")
        self.assertEqual(self.rec.quit, [])


class DiskChangeTests(ControllerCase):
    def edited_text(self):
        return prof.dumps_profile(replace(self.c.profile, layer_names=("Edited", "", "", "")))

    def test_nothing_changed_nothing_happens(self):
        self.c.poll()
        self.assertEqual(self.c.diskMessage, "")

    def test_clean_app_reloads_a_changed_file(self):
        self.touch_disk("default", self.edited_text())
        self.c.poll()
        self.assertEqual(self.c.profile.layer_names[0], "Edited")
        self.assertFalse(self.c.dirty)
        self.assertEqual(self.c.diskMessage, "")

    def test_a_poll_waits_while_a_confirm_is_open(self):
        # Review 9: with no unsaved edits, a reload under an open dialog let "OK" apply an edit
        # built on the old profile and drop the reload.
        self.c.removeLayer(1)  # layer 1 holds events: asks first
        self.assertEqual(len(self.rec.confirm), 1)
        self.touch_disk("default", self.edited_text())
        self.c.poll()
        self.assertEqual(self.c.profile.layer_names[0], "Drums")  # not reloaded under the dialog
        self.c.resolveConfirm(True)
        self.assertEqual(self.c.layerCount, 3)
        self.c.poll()  # the change is still noticed; the edit is unsaved, so it asks
        self.assertIn("changed on disk", self.c.diskMessage)

    def test_a_poll_waits_while_the_unsaved_prompt_is_open(self):
        self.c.setChannel(5)
        self.c.requestQuit()
        self.assertEqual(len(self.rec.unsaved), 1)
        self.touch_disk("default", self.edited_text())
        self.c.poll()
        self.assertEqual(self.c.diskMessage, "")
        self.c.resolveUnsaved("cancel")
        self.c.poll()
        self.assertIn("changed on disk", self.c.diskMessage)

    def test_clean_app_follows_current_to_another_profile(self):
        write_profile(self.home, "other", NOTHING)
        prof.set_current("other", self.home)
        self.c.poll()
        self.assertEqual(self.c.profileName, "other")
        self.assertEqual(self.c.selected, "")

    def test_unsaved_edits_raise_a_notice_instead_of_reloading(self):
        self.c.renameLayer(1, "Mine")
        self.touch_disk("default", self.edited_text())
        self.c.poll()
        self.assertEqual(self.c.diskMessage, "default changed on disk.")
        self.assertEqual(self.c.profile.layer_names[0], "Mine")
        self.c.poll()  # one notice, not one per tick
        self.assertEqual(self.c.diskMessage, "default changed on disk.")

    def test_reload_takes_the_disk_version(self):
        self.c.renameLayer(1, "Mine")
        self.touch_disk("default", self.edited_text())
        self.c.poll()
        self.c.reloadFromDisk()
        self.assertEqual(self.c.profile.layer_names[0], "Edited")
        self.assertFalse(self.c.dirty)
        self.assertEqual(self.c.diskMessage, "")

    def test_keep_mine_stops_the_questions_and_the_next_save_wins(self):
        self.c.renameLayer(1, "Mine")
        self.touch_disk("default", self.edited_text())
        self.c.poll()
        self.c.keepMine()
        self.assertEqual(self.c.diskMessage, "")
        self.c.poll()
        self.assertEqual(self.c.diskMessage, "")
        self.c.saveProfile()
        self.assertEqual(self.disk().layer_names[0], "Mine")

    def test_unsaved_edits_and_current_pointing_elsewhere_raise_a_notice(self):
        write_profile(self.home, "other", NOTHING)
        self.c.renameLayer(1, "Mine")
        prof.set_current("other", self.home)
        self.c.poll()
        self.assertEqual(self.c.diskMessage, "The current profile changed on disk.")
        self.c.reloadFromDisk()
        self.assertEqual(self.c.profileName, "other")

    def test_a_file_that_stops_parsing_keeps_what_is_open(self):
        time.sleep(0.01)
        self.touch_disk("default", "version = 1\n[key.1]\nkind = \"nonsense\"\n")
        self.c.poll()
        self.assertEqual(self.c.profile.layer_names[0], "Drums")
        self.assertIn("Can't open default", self.c.error)
        self.c.poll()  # no repeat; the open profile is still the app's
        self.assertFalse(self.c.dirty)


if __name__ == "__main__":
    unittest.main()
