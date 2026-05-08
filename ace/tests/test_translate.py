import unittest
from unittest.mock import MagicMock, PropertyMock, mock_open, patch

from mido import Message, MetaMessage

from ace.charter import Charter


class TestChartTranslator(unittest.TestCase):
    """Tests for Charter class."""

    def setUp(self):
        """Set up test fixtures."""
        self.translator = Charter()

    def test_init(self):
        """Test that Charter can be instantiated."""
        self.assertIsInstance(self.translator, Charter)

    @patch("ace.charter.MidiFile")
    @patch("ace.charter.MidiTrack")
    @patch("os.path.join")
    @patch("os.path.exists")
    @patch("os.path.splitext")
    @patch("os.path.basename")
    def test_split_midi(
        self,
        mock_basename,
        mock_splitext,
        mock_exists,
        mock_join,
        mock_midi_track,
        mock_midi_file,
    ):
        """Test split_midi method."""
        in_file_dir = "/path/to/input.mid"
        out_dir = "/path/to/output"

        # Setup mocks
        mock_basename.return_value = "input.mid"
        mock_splitext.return_value = ("input", ".mid")
        mock_join.return_value = "/path/to/output/input_DRUMS.mid"
        mock_exists.return_value = True

        # Create mock MidiFile objects
        mock_in_mid = MagicMock()
        mock_out_mid = MagicMock()
        mock_midi_file.side_effect = [mock_in_mid, mock_out_mid]

        # Create track mocks
        mock_track1 = MagicMock()
        mock_track2 = MagicMock()

        type(mock_in_mid).tracks = PropertyMock(return_value=[mock_track1, mock_track2])
        type(mock_in_mid).ticks_per_beat = PropertyMock(return_value=480)

        mock_drum_track = MagicMock()
        mock_midi_track.return_value = mock_drum_track
        type(mock_out_mid).tracks = PropertyMock(return_value=[mock_drum_track])

        # Create sample MIDI messages
        tempo_msg = MetaMessage("set_tempo", tempo=500000, time=0)
        time_sig_msg = MetaMessage("time_signature", numerator=4, denominator=4, time=0)
        note_on_drum = Message("note_on", note=36, velocity=64, time=100, channel=9)
        note_off_drum = Message("note_off", note=36, velocity=0, time=100, channel=9)
        note_on_other = Message("note_on", note=60, velocity=64, time=100, channel=0)

        mock_track1.__iter__.return_value = [tempo_msg, time_sig_msg]
        mock_track2.__iter__.return_value = [note_on_drum, note_off_drum, note_on_other]

        result = self.translator.split_midi(in_file_dir, out_dir)

        # Verify MidiFile was opened with the input path
        mock_midi_file.assert_any_call(in_file_dir)

        # Check the returned file key
        self.assertEqual(result, "input_DRUMS.mid")

    @patch("builtins.open", new_callable=mock_open)
    @patch("ace.charter.MidiFile")
    @patch("ace.charter.mido.merge_tracks")
    @patch("os.path.join")
    @patch("os.path.exists")
    @patch("os.path.splitext")
    @patch("os.path.basename")
    def test_convert_to_chart(
        self,
        mock_basename,
        mock_splitext,
        mock_exists,
        mock_join,
        mock_merge_tracks,
        mock_midi_file,
        mock_file_open,
    ):
        """Test generate_chart_file method."""
        in_file_key = "input_DRUMS.mid"
        out_dir = "/path/to/output"
        ch_out_dir = "artist - input (ACE)"

        # Setup mocks
        mock_splitext.return_value = ("input_DRUMS", ".mid")
        mock_join.return_value = "/path/to/output/input_DRUMS.chart"
        mock_exists.return_value = True
        mock_basename.return_value = "input_DRUMS.chart"

        # Create mock MidiFile
        mock_mid = MagicMock()
        mock_midi_file.return_value = mock_mid

        mock_track = MagicMock()
        type(mock_mid).tracks = PropertyMock(return_value=[mock_track])
        type(mock_mid).ticks_per_beat = PropertyMock(return_value=480)

        # Setup merged track with sample MIDI events
        tempo_msg = MetaMessage("set_tempo", tempo=500000, time=0)
        kick_msg = Message("note_on", note=36, velocity=64, time=100, channel=9)
        snare_msg = Message("note_on", note=38, velocity=64, time=100, channel=9)
        hihat_msg = Message("note_on", note=42, velocity=64, time=100, channel=9)
        crash_msg = Message("note_on", note=49, velocity=64, time=100, channel=9)

        mock_merge_tracks.return_value = [
            tempo_msg,
            kick_msg,
            snare_msg,
            hihat_msg,
            crash_msg,
        ]

        self.translator.generate_chart_file(in_file_key, out_dir, ch_out_dir)

        # Verify MidiFile was opened from local path
        mock_midi_file.assert_called_once()

        # Verify chart file was written to local directory
        mock_file_open.assert_any_call("/path/to/output/input_DRUMS.chart", "w")

        # Verify chart content includes expected sections
        write_calls = mock_file_open().write.call_args_list
        if write_calls:
            written_content = "".join(call.args[0] for call in write_calls)
            self.assertIn("[Song]", written_content)
            self.assertIn("[SyncTrack]", written_content)
            self.assertIn("[Events]", written_content)
            self.assertIn("[ExpertDrums]", written_content)


if __name__ == "__main__":
    unittest.main()
